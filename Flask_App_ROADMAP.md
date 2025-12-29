# Flask Simulator Conversion Roadmap

## DISCLAIMER: How to use this ROADMAP: READ THIS EVERY TIME
ONLY WORK BY PHASE - Do not race ahead and execute multiple phases at once - work through each phase, and stop the moment you finish each one. When you stop a phase, provide the user with a list of manual checks to ensure the phase was completed succesfully. You can also pitch a couple automatic checks you can execute to the user, but ensure these checks do not interfere with the code you have created, and also ensure that the checks are valid, and actually test what you are aiming to test. Also make sure you only run these tests when the user provides direct permission

## Phase 1: Project Structure Setup

### 1.1 Directory Structure

```
Simulator/
├── Grid.py                    # Core grid logic (keep as-is)
├── Sims/
│   ├── Heat_dissaptor.py     # Heat simulation (keep as-is)
│   ├── ripples.py            # Ripple simulation (keep as-is)
│   └── __init__.py           # Package initialization
├── flask_app/
│   ├── app.py                # Main Flask application
│   ├── simulator_manager.py   # Simulator instantiation & execution
│   ├── templates/
│   │   ├── base.html         # Base template with common layout
│   │   ├── index.html        # Simulator selection page
│   │   └── simulator.html    # Generic simulator display template
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css     # Styling
│   │   └── js/
│   │       ├── grid_renderer.js    # Canvas rendering logic
│   │       └── simulator_client.js # WebSocket/SSE client
│   └── config/
│       └── simulators.json   # Simulator metadata & parameters
├── requirements.txt          # Dependencies
└── README.md
```

### 1.2 Dependencies

Add to `requirements.txt`:

```
Flask==3.0.0
flask-socketio==5.3.5
python-socketio==5.10.0
eventlet==0.33.3  # For async support
```

## Phase 2: Backend Architecture

### 2.1 Simulator Registry System

`config/simulators.json` - Describes each simulator's configuration:

```json
{
  "heat": {
    "name": "Heat Dissipation",
    "class_name": "HeatGrid",
    "module_path": "Sims.Heat_dissaptor",
    "description": "Simulates heat diffusion across a 2D grid",
    "parameters": [
      {"name": "width", "type": "int", "default": 100, "min": 10, "max": 200},
      {"name": "height", "type": "int", "default": 100, "min": 10, "max": 200},
      {"name": "time_step", "type": "float", "default": 0.25, "min": 0.01, "max": 1.0, "step": 0.01},
      {"name": "thermal_diffusivity", "type": "float", "default": 1.0, "min": 0.1, "max": 5.0, "step": 0.1}
    ],
    "initial_conditions": [
      {"name": "heat_source_x", "type": "int", "default": 50},
      {"name": "heat_source_y", "type": "int", "default": 50},
      {"name": "heat_amount", "type": "float", "default": 20}
    ],
    "color_scheme": "heat"
  },
  "ripples": {
    "name": "Ripple Effect",
    "class_name": "Ripples",
    "module_path": "Sims.ripples",
    "description": "Simulates ripple propagation",
    "parameters": [
      {"name": "width", "type": "int", "default": 30, "min": 10, "max": 100},
      {"name": "height", "type": "int", "default": 20, "min": 10, "max": 100},
      {"name": "time_step", "type": "float", "default": 0.1, "min": 0.01, "max": 1.0, "step": 0.01}
    ],
    "initial_conditions": [
      {"name": "source_x", "type": "int", "default": 15},
      {"name": "source_y", "type": "int", "default": 10},
      {"name": "intensity", "type": "float", "default": 30}
    ],
    "color_scheme": "ripple"
  }
}
```

### 2.2 Simulator Manager

`simulator_manager.py` - Handles dynamic loading and execution:

```python
import importlib
import json
from threading import Thread
import time

class SimulatorManager:
    def __init__(self):
        with open('flask_app/config/simulators.json', 'r') as f:
            self.simulators = json.load(f)
    
    def get_simulator_list(self):
        """Returns list of available simulators for selection page"""
        return [{
            'id': sim_id,
            'name': sim_data['name'],
            'description': sim_data['description']
        } for sim_id, sim_data in self.simulators.items()]
    
    def get_simulator_config(self, sim_id):
        """Returns parameter configuration for a specific simulator"""
        return self.simulators.get(sim_id)
    
    def instantiate_simulator(self, sim_id, params):
        """Dynamically loads and creates simulator instance"""
        config = self.simulators[sim_id]
        module = importlib.import_module(config['module_path'])
        SimClass = getattr(module, config['class_name'])
        
        # Extract only the constructor parameters
        constructor_params = {p['name']: params[p['name']] 
                            for p in config['parameters']}
        return SimClass(**constructor_params)
    
    def run_simulation(self, sim_instance, initial_conditions, 
                      steps, socketio, room):
        """Runs simulation and emits grid state via WebSocket"""
        # Apply initial conditions
        for condition, value in initial_conditions.items():
            if 'x' in condition and 'y' in condition:
                # Handle setting initial values
                pass
        
        # Run simulation loop
        for step in range(steps):
            sim_instance.update_grid(use_diagonals=True, wrap=True)
            
            # Convert grid to serializable format
            grid_data = self._serialize_grid(sim_instance.grid)
            
            # Emit to client
            socketio.emit('grid_update', {
                'step': step,
                'grid': grid_data,
                'metric': sim_instance._get_metric()
            }, room=room)
            
            time.sleep(sim_instance.time_step)
    
    def _serialize_grid(self, grid):
        """Convert 2D grid to JSON-friendly format"""
        return [[float(cell) for cell in row] for row in grid]
```

### 2.3 Flask Application

`app.py` - Main application setup and routes:

```python
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room
import uuid
from simulator_manager import SimulatorManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

sim_manager = SimulatorManager()
active_simulations = {}

@app.route('/')
def index():
    """Simulator selection page"""
    simulators = sim_manager.get_simulator_list()
    return render_template('index.html', simulators=simulators)

@app.route('/simulator/<sim_id>')
def simulator(sim_id):
    """Simulator page with parameter form"""
    config = sim_manager.get_simulator_config(sim_id)
    if not config:
        return "Simulator not found", 404
    
    return render_template('simulator.html', 
                         sim_id=sim_id,
                         config=config)

@socketio.on('start_simulation')
def handle_start_simulation(data):
    """Client requests to start a simulation"""
    sim_id = data['sim_id']
    params = data['parameters']
    initial_conditions = data['initial_conditions']
    steps = data.get('steps', 1000)
    
    # Create unique room for this simulation
    room = str(uuid.uuid4())
    join_room(room)
    
    # Instantiate simulator
    sim_instance = sim_manager.instantiate_simulator(sim_id, params)
    
    # Store active simulation
    active_simulations[room] = sim_instance
    
    # Run simulation in background thread
    socketio.start_background_task(
        sim_manager.run_simulation,
        sim_instance, initial_conditions, steps, socketio, room
    )
    
    emit('simulation_started', {'room': room})

@socketio.on('stop_simulation')
def handle_stop_simulation(data):
    """Client requests to stop simulation"""
    room = data['room']
    if room in active_simulations:
        del active_simulations[room]
    emit('simulation_stopped')
```

```python
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

## Phase 3: Frontend Architecture

### 3.1 Selection Page

`templates/index.html` - Grid layout showing available simulators:

```html
{% extends "base.html" %}

{% block content %}
<div class="simulator-grid">
    {% for sim in simulators %}
    <div class="simulator-card">
        <h3>{{ sim.name }}</h3>
        <p>{{ sim.description }}</p>
        <a href="/simulator/{{ sim.id }}" class="btn">Launch</a>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

### 3.2 Simulator Template

`templates/simulator.html` - Generic template that adapts to any simulator:

```html
{% extends "base.html" %}

{% block content %}
<div class="simulator-container">
    <div class="controls-panel">
        <h2>{{ config.name }}</h2>
        
        <form id="sim-form">
            <h3>Parameters</h3>
            {% for param in config.parameters %}
            <div class="form-group">
                <label>{{ param.name }}</label>
                <input type="{{ param.type }}" 
                       name="{{ param.name }}"
                       value="{{ param.default }}"
                       min="{{ param.min }}"
                       max="{{ param.max }}"
                       step="{{ param.get('step', 1) }}">
            </div>
            {% endfor %}
            
            <h3>Initial Conditions</h3>
            {% for condition in config.initial_conditions %}
            <div class="form-group">
                <label>{{ condition.name }}</label>
                <input type="{{ condition.type }}"
                       name="{{ condition.name }}"
                       value="{{ condition.default }}">
            </div>
            {% endfor %}
            
            <button type="submit" id="start-btn">Start Simulation</button>
            <button type="button" id="stop-btn" disabled>Stop</button>
        </form>
        
        <div class="metrics">
            <p>Step: <span id="step-counter">0</span></p>
            <p>Metric: <span id="metric-value">0</span></p>
        </div>
    </div>
    
    <div class="visualization-panel">
        <canvas id="grid-canvas"></canvas>
    </div>
</div>

<script src="/static/js/grid_renderer.js"></script>
<script src="/static/js/simulator_client.js"></script>
<script>
    const simId = "{{ sim_id }}";
    const colorScheme = "{{ config.color_scheme }}";
</script>
{% endblock %}
```

### 3.3 Canvas Renderer

`static/js/grid_renderer.js` - Handles rendering the grid visualization:

```javascript
class GridRenderer {
    constructor(canvasId, colorScheme) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.colorScheme = this.getColorScheme(colorScheme);
        this.cellSize = 5; // pixels per cell
    }
    
    getColorScheme(scheme) {
        const schemes = {
            'heat': [
                { threshold: 0.05, color: '#000000' },
                { threshold: 0.10, color: '#2C2C2C' },
                { threshold: 0.20, color: '#4A4A4A' },
                { threshold: 0.30, color: '#AAAAAA' },
                { threshold: 0.40, color: '#0066FF' },
                { threshold: 0.50, color: '#00FFFF' },
                { threshold: 0.60, color: '#00FF00' },
                { threshold: 0.70, color: '#FFFF00' },
                { threshold: 0.85, color: '#FFD700' },
                { threshold: 1.0,  color: '#FF0000' }
            ],
            'ripple': [
                // Similar structure for ripples
            ]
        };
        return schemes[scheme] || schemes['heat'];
    }
    
    render(grid) {
        const height = grid.length;
        const width = grid[0].length;
        
        // Resize canvas if needed
        if (this.canvas.width !== width * this.cellSize) {
            this.canvas.width = width * this.cellSize;
            this.canvas.height = height * this.cellSize;
        }
        
        // Draw grid
        for (let i = 1; i < height - 1; i++) {  // Skip borders
            for (let j = 1; j < width - 1; j++) {
                const value = grid[i][j] / 10.0;  // Normalize
                const normalizedValue = Math.max(0, Math.min(1, value));
                
                const color = this.getColor(normalizedValue);
                this.ctx.fillStyle = color;
                this.ctx.fillRect(
                    (j - 1) * this.cellSize,
                    (i - 1) * this.cellSize,
                    this.cellSize,
                    this.cellSize
                );
            }
        }
    }
    
    getColor(value) {
        for (let i = 0; i < this.colorScheme.length; i++) {
            if (value <= this.colorScheme[i].threshold) {
                return this.colorScheme[i].color;
            }
        }
        return this.colorScheme[this.colorScheme.length - 1].color;
    }
}
```

### 3.4 WebSocket Client

`static/js/simulator_client.js` - Handles WebSocket communication:

```javascript
const socket = io();
let renderer = new GridRenderer('grid-canvas', colorScheme);
let currentRoom = null;

document.getElementById('sim-form').addEventListener('submit', (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const parameters = {};
    const initial_conditions = {};
    
    // Parse form data based on config
    // (split into parameters vs initial_conditions)
    
    socket.emit('start_simulation', {
        sim_id: simId,
        parameters: parameters,
        initial_conditions: initial_conditions,
        steps: 1000
    });
    
    document.getElementById('start-btn').disabled = true;
    document.getElementById('stop-btn').disabled = false;
});

socket.on('simulation_started', (data) => {
    currentRoom = data.room;
    console.log('Simulation started in room:', currentRoom);
});

socket.on('grid_update', (data) => {
    renderer.render(data.grid);
    document.getElementById('step-counter').textContent = data.step;
    document.getElementById('metric-value').textContent = data.metric.toFixed(2);
});

socket.on('simulation_stopped', () => {
    document.getElementById('start-btn').disabled = false;
    document.getElementById('stop-btn').disabled = true;
});

document.getElementById('stop-btn').addEventListener('click', () => {
    socket.emit('stop_simulation', { room: currentRoom });
});
```

## Phase 4: Implementation Steps

### Step 1: Setup (Week 1)

Create Flask directory structure
Install dependencies
Create simulators.json for HeatGrid
Test basic Flask app with static templates

### Step 2: Backend Integration (Week 2)

Implement SimulatorManager class
Add dynamic simulator loading
Implement WebSocket handlers in app.py
Test with HeatGrid simulator

Step 3: Frontend Development (Week 2-3)

Create base template with CSS grid for selection page
Build generic simulator template
Implement Canvas renderer
Implement WebSocket client
Test end-to-end with HeatGrid

Step 4: Add Second Simulator (Week 3)

Add Ripples configuration to simulators.json
Test that template system works for both simulators
Verify no simulator code was modified

Step 5: Polish & Optimization (Week 4)

Add loading indicators
Optimize Canvas rendering (only redraw changed cells)
Add error handling
Improve UI/UX
Documentation


Phase 5: Future Enhancements (Post-MVP)

Mid-simulation interaction: Click to add heat sources/obstacles
Multiple visualizations: Side-by-side comparison of different parameters
Recording: Save simulation as video/GIF
Presets: Pre-configured interesting simulations
Performance: WebGL renderer for larger grids
Mobile: Responsive design


Key Design Principles
✅ Zero modification to simulator logic - All integration happens through:

JSON configuration
Dynamic imports
Standard method interfaces (set_value, update_grid, _get_metric)

✅ Template-based system - One simulator template serves all simulators
✅ Easy to add new simulators - Just add JSON config + ensure simulator inherits from SimulatorGrid
✅ Real-time visualization - WebSocket streaming of grid state
✅ Scalability - Background threads prevent blocking