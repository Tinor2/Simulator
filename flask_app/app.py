import logging
import os
import sys
import traceback
import uuid
from functools import wraps
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, disconnect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PORT = 5000
DEFAULT_HOST = '0.0.0.0'
DEBUG_MODE = True

# Type aliases
SimulationID = str
RoomID = str

def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__, template_folder='templates')
    
    # Default configuration
    app.config.update(
        SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production'),
        SESSION_COOKIE_SECURE=not DEBUG_MODE,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        TEMPLATES_AUTO_RELOAD=DEBUG_MODE,
        EXPLAIN_TEMPLATE_LOADING=DEBUG_MODE
    )
    
    # Update with any provided config
    if config:
        app.config.update(config)
    
    return app

def create_socketio(app: Flask) -> SocketIO:
    """Create and configure Socket.IO instance."""
    return SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=DEBUG_MODE,
        engineio_logger=DEBUG_MODE
    )

# Create application and Socket.IO instances
app = create_app()
socketio = create_socketio(app)

# Initialize Simulator Manager
from .simulator_manager import SimulatorManager
sim_manager = SimulatorManager()
active_simulations: Dict[RoomID, Any] = {}

# Note: in Flask-SocketIO, `socketio.server` is a python-socketio Server instance
# and does not expose the Flask `app`. Use `app.app_context()` when needed.

# Helper functions
def validate_simulation_access(room_id: RoomID) -> bool:
    """Validate if the current session has access to the simulation room."""
    return room_id in active_simulations

def handle_error(error: Exception, message: str = "An error occurred", status_code: int = 400):
    """Handle and log errors consistently."""
    error_type = error.__class__.__name__
    error_details = str(error)
    
    logger.error(f"{message}: {error_type} - {error_details}")
    logger.debug(traceback.format_exc())
    
    return jsonify({
        'status': 'error',
        'message': message,
        'error': error_details,
        'type': error_type
    }), status_code

# Routes
@app.route('/')
def index():
    """Render the simulator selection page."""
    try:
        simulators = sim_manager.get_simulator_list()
        if not simulators:
            logger.warning("No simulators found in configuration")
        return render_template('index.html', simulators=simulators)
    except Exception as e:
        return handle_error(e, "Failed to load simulator list")

@app.route('/simulator/<sim_id>')
def simulator(sim_id: str):
    """Render the simulator page with parameter form."""
    try:
        config = sim_manager.get_simulator_config(sim_id)
        if not config:
            return handle_error(ValueError(f"Simulator '{sim_id}' not found"), 
                             "Simulator not found", 404)
        
        # Add CSRF token for forms
        if 'csrf_token' not in session:
            if app.config.get('WTF_CSRF_ENABLED', True):
                session['csrf_token'] = str(uuid.uuid4())
        
        # Pass the sim_id to the template
        return render_template(
            'simulator.html',
            sim_id=sim_id,  # Pass the simulator ID
            config=config,
            csrf_token=session.get('csrf_token', '')
        )
    except Exception as e:
        return handle_error(e, f"Failed to load simulator: {sim_id}")

# Socket.IO Event Handlers
def socket_error_handler(f):
    """Decorator to handle errors in Socket.IO event handlers."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error(f"Socket.IO error [{error_id}]: {str(e)}", exc_info=True)
            emit('error', {
                'id': error_id,
                'message': str(e),
                'type': e.__class__.__name__
            })
    return wrapped

@socketio.on('connect')
@socket_error_handler
def handle_connect(auth=None):
    """Handle new client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_established', {'status': 'connected'})

@socketio.on('disconnect')
@socket_error_handler
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")
    # Clean up any resources for this connection

@socketio.on('start_simulation')
@socket_error_handler
def handle_start_simulation(data: Dict[str, Any]):
    """Handle request to start a new simulation."""
    try:
        # Validate required fields
        required_fields = ['sim_id', 'parameters', 'initial_conditions']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        sim_id = str(data['sim_id'])
        params = data['parameters']
        initial_conditions = data['initial_conditions']
        steps = int(data.get('steps', 1000))
        
        # Validate parameters
        if not isinstance(params, dict):
            raise ValueError("Parameters must be a dictionary")
            
        if not isinstance(initial_conditions, dict):
            raise ValueError("Initial conditions must be a dictionary")
        
        # Create or join a room
        room = data.get('room')
        if room and room in active_simulations:
            # Join existing simulation
            join_room(room)
            emit('simulation_joined', {
                'room': room,
                'status': 'joined',
                'message': 'Joined existing simulation'
            })
            return
        else:
            # Create a new simulation
            room = str(uuid.uuid4())
            join_room(room)
            
            # Instantiate the simulator with provided parameters
            sim_instance = sim_manager.instantiate_simulator(sim_id, params)
            
            # Store the active simulation
            active_simulations[room] = {
                'instance': sim_instance,
                'clients': {request.sid},
                'config': sim_manager.get_simulator_config(sim_id)
            }
            
            # Start the simulation in a background task
            def run_simulation_task():
                with app.app_context():
                    try:
                        sim_manager.run_simulation(
                            sim_instance=sim_instance,
                            initial_conditions=initial_conditions,
                            steps=steps,
                            socketio=socketio,
                            room=room
                        )
                    except Exception as e:
                        logger.error(f"Simulation error in room {room}: {str(e)}", exc_info=True)
                        socketio.emit('simulation_error', {
                            'error': str(e),
                            'type': e.__class__.__name__
                        }, room=room)
                    finally:
                        # Clean up
                        if room in active_simulations:
                            del active_simulations[room]
            
            socketio.start_background_task(run_simulation_task)
            
            # Notify the client that the simulation has started
            emit('simulation_started', {
                'room': room,
                'simulator_id': sim_id,
                'steps': steps
            })
            
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}", exc_info=True)
        emit('simulation_error', {
            'error': str(e),
            'type': e.__class__.__name__
        })

@socketio.on('stop_simulation')
@socket_error_handler
def handle_stop_simulation(data: Dict[str, Any]):
    """Handle request to stop a running simulation."""
    try:
        room = data.get('room')
        if not room:
            raise ValueError("Room ID is required")
            
        if room not in active_simulations:
            raise ValueError(f"No active simulation in room: {room}")
        
        # Get the simulation instance
        sim_data = active_simulations[room]
        sim_instance = sim_data['instance']
        
        # Set flag to stop the simulation loop
        if hasattr(sim_instance, 'is_running'):
            sim_instance.is_running = False
            
        # Notify all clients in the room
        emit('simulation_stopped', {
            'room': room,
            'reason': 'stopped_by_user',
            'message': 'Simulation stopped by user'
        }, room=room)
        
        # Clean up
        if room in active_simulations:
            del active_simulations[room]
            
    except Exception as e:
        logger.error(f"Error stopping simulation: {str(e)}", exc_info=True)
        emit('simulation_error', {
            'error': str(e),
            'type': e.__class__.__name__
        })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    return handle_error(error, "The requested resource was not found", 404)

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return handle_error(error, "An internal server error occurred", 500)

# Main entry point
if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', DEFAULT_PORT))
    
    # Log startup information
    logger.info(f"Starting server on {DEFAULT_HOST}:{port}")
    logger.info(f"Debug mode: {'ON' if DEBUG_MODE else 'OFF'}")
    
    try:
        # Run the Flask-SocketIO application
        socketio.run(
            app,
            host=DEFAULT_HOST,
            port=port,
            debug=DEBUG_MODE,
            use_reloader=DEBUG_MODE,
            log_output=DEBUG_MODE,
            allow_unsafe_werkzeug=DEBUG_MODE
        )
    except Exception as e:
        logger.critical(f"Fatal error starting server: {str(e)}", exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)