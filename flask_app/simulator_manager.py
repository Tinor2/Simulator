import importlib
import json
import logging
import os
from threading import Thread
import time
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimulatorManager:
    def __init__(self, config_path: str = None):
        """Initialize the SimulatorManager with configuration.
        
        Args:
            config_path: Optional path to the simulators configuration file.
                        If not provided, defaults to 'flask_app/config/simulators.json'
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'flask_app', 
                'config', 
                'simulators.json'
            )
        
        try:
            with open(config_path, 'r') as f:
                self.simulators = json.load(f)
            logger.info(f"Loaded {len(self.simulators)} simulators from {config_path}")
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            self.simulators = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file {config_path}: {str(e)}")
            self.simulators = {}
    
    def get_simulator_list(self) -> List[Dict[str, str]]:
        """Get a list of available simulators for the selection page.
        
        Returns:
            List of dictionaries containing simulator metadata (id, name, description)
        """
        try:
            return [{
                'id': sim_id,
                'name': sim_data.get('name', 'Unnamed Simulator'),
                'description': sim_data.get('description', 'No description available')
            } for sim_id, sim_data in self.simulators.items()]
        except Exception as e:
            logger.error(f"Error getting simulator list: {str(e)}")
            return []
    
    def get_simulator_config(self, sim_id: str) -> Optional[Dict[str, Any]]:
        """Get the configuration for a specific simulator.
        
        Args:
            sim_id: The ID of the simulator to get configuration for
            
        Returns:
            The simulator configuration dictionary if found, None otherwise
        """
        if not sim_id or not isinstance(sim_id, str):
            logger.warning(f"Invalid simulator ID: {sim_id}")
            return None
            
        config = self.simulators.get(sim_id)
        if not config:
            logger.warning(f"Simulator not found: {sim_id}")
        return config
    
    def instantiate_simulator(self, sim_id: str, params: Dict[str, Any]) -> Any:
        """Dynamically load and create a simulator instance.
        
        Args:
            sim_id: The ID of the simulator to instantiate
            params: Dictionary of parameters to pass to the simulator constructor
            
        Returns:
            An instance of the requested simulator class
            
        Raises:
            ValueError: If the simulator cannot be instantiated with the given parameters
            ImportError: If the simulator module cannot be imported
            AttributeError: If the simulator class cannot be found in the module
        """
        if not sim_id or sim_id not in self.simulators:
            raise ValueError(f"Invalid simulator ID: {sim_id}")
            
        config = self.simulators[sim_id]
        
        # Validate required parameters
        required_params = {p['name'] for p in config.get('parameters', []) 
                         if 'default' not in p}
        missing_params = required_params - set(params.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
        
        try:
            # Import the module
            module = importlib.import_module(config['module_path'])
            
            # Get the class
            SimClass = getattr(module, config['class_name'])
            
            # Prepare constructor parameters with defaults
            constructor_params = {}
            for param in config.get('parameters', []):
                param_name = param['name']
                if param_name in params:
                    # Type conversion based on parameter type
                    param_type = param.get('type', 'str')
                    try:
                        if param_type == 'int':
                            constructor_params[param_name] = int(params[param_name])
                        elif param_type == 'float':
                            constructor_params[param_name] = float(params[param_name])
                        else:
                            constructor_params[param_name] = params[param_name]
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"Invalid value for parameter '{param_name}': {params[param_name]}. "
                            f"Expected type {param_type}."
                        )
                elif 'default' in param:
                    constructor_params[param_name] = param['default']
            
            logger.info(f"Instantiating {config['class_name']} with params: {constructor_params}")
            return SimClass(**constructor_params)
            
        except ImportError as e:
            logger.error(f"Failed to import module {config['module_path']}: {str(e)}")
            raise ImportError(f"Could not import simulator module: {config['module_path']}")
        except AttributeError as e:
            logger.error(f"Class {config['class_name']} not found in module {config['module_path']}")
            raise AttributeError(f"Simulator class {config['class_name']} not found")
        except Exception as e:
            logger.error(f"Error instantiating simulator {sim_id}: {str(e)}")
            raise
    
    def run_simulation(
        self, 
        sim_instance: Any, 
        initial_conditions: Dict[str, Any], 
        steps: int, 
        socketio: Any, 
        room: str
    ) -> None:
        """Run the simulation and emit updates via WebSocket.
        
        Args:
            sim_instance: The simulator instance to run
            initial_conditions: Dictionary of initial conditions to apply
            steps: Number of simulation steps to run
            socketio: SocketIO instance for emitting updates
            room: Room ID to emit updates to
        """
        if not hasattr(sim_instance, 'update_grid') or not callable(sim_instance.update_grid):
            error_msg = "Simulator instance is missing required 'update_grid' method"
            logger.error(error_msg)
            socketio.emit('simulation_error', {'error': error_msg}, room=room)
            return
            
        if not hasattr(sim_instance, 'grid'):
            error_msg = "Simulator instance is missing required 'grid' attribute"
            logger.error(error_msg)
            socketio.emit('simulation_error', {'error': error_msg}, room=room)
            return
            
        # Set up simulation control
        sim_instance.is_running = True
        
        try:
            # Apply initial conditions
            for condition, value in initial_conditions.items():
                if hasattr(sim_instance, condition):
                    try:
                        # Try to convert the value to the expected type
                        attr_type = type(getattr(sim_instance, condition))
                        setattr(sim_instance, condition, attr_type(value))
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Could not set {condition}={value} on simulator: {str(e)}. "
                            f"Using default value."
                        )
            
            # Run simulation loop
            for step in range(int(steps)):
                if not getattr(sim_instance, 'is_running', True):
                    logger.info("Simulation stopped by user")
                    break
                    
                try:
                    # Update the simulation state
                    sim_instance.update_grid(use_diagonals=True, wrap=True)
                    
                    # Get the current grid state
                    if not hasattr(sim_instance, 'grid'):
                        raise AttributeError("Simulator is missing 'grid' attribute after update")
                    
                    # Convert grid to serializable format
                    grid_data = self._serialize_grid(sim_instance.grid)
                    
                    # Get metric if available
                    metric = 0
                    if hasattr(sim_instance, '_get_metric') and callable(sim_instance._get_metric):
                        try:
                            metric = float(sim_instance._get_metric())
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error getting metric: {str(e)}")
                    
                    # Emit update to client
                    socketio.emit('grid_update', {
                        'step': step,
                        'grid': grid_data,
                        'metric': metric,
                        'total_steps': steps
                    }, room=room)
                    
                    # Throttle the simulation if needed
                    time_step = getattr(sim_instance, 'time_step', 0.1)
                    if time_step > 0:
                        time.sleep(time_step)
                        
                except Exception as e:
                    error_msg = f"Error in simulation step {step}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    socketio.emit('simulation_error', {'error': error_msg}, room=room)
                    break
                    
        except Exception as e:
            error_msg = f"Fatal error in simulation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            socketio.emit('simulation_error', {'error': error_msg}, room=room)
            
        finally:
            # Clean up
            if hasattr(sim_instance, 'is_running'):
                sim_instance.is_running = False
                
            # Notify client that simulation has ended
            socketio.emit('simulation_ended', {'reason': 'completed'}, room=room)
    
    def _serialize_grid(self, grid) -> List[List[float]]:
        """Convert a 2D grid to a JSON-serializable format.
        
        Args:
            grid: 2D grid (list of lists) to serialize
            
        Returns:
            2D list of floats
            
        Raises:
            ValueError: If the grid cannot be serialized
        """
        if not isinstance(grid, (list, tuple)) or not all(isinstance(row, (list, tuple)) for row in grid):
            raise ValueError("Grid must be a 2D list or tuple")
            
        try:
            return [
                [float(cell) for cell in row] 
                for row in grid
            ]
        except (ValueError, TypeError) as e:
            raise ValueError(f"Could not serialize grid: {str(e)}")
