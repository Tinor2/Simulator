// Global variables
let socket;
let currentRoom = null;

// DOM Elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const simForm = document.getElementById('sim-form');
const stepCounter = document.getElementById('step-counter');
const metricValue = document.getElementById('metric-value');

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Connect to Socket.IO
    socket = io();
    
    // Handle form submission
    if (simForm) {
        simForm.addEventListener('submit', handleStartSimulation);
    }
    
    // Handle stop button
    if (stopBtn) {
        stopBtn.addEventListener('click', handleStopSimulation);
    }
    
    // Socket.IO event handlers
    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
    });
    
    socket.on('simulation_started', (data) => {
        console.log('Simulation started in room:', data.room);
        currentRoom = data.room;
        startBtn.disabled = true;
        stopBtn.disabled = false;
    });
    
    socket.on('grid_update', (data) => {
        updateGridDisplay(data);
        stepCounter.textContent = data.step;
        metricValue.textContent = data.metric.toFixed(2);
    });
    
    socket.on('simulation_stopped', () => {
        console.log('Simulation stopped');
        currentRoom = null;
        startBtn.disabled = false;
        stopBtn.disabled = true;
    });
    
    socket.on('simulation_error', (error) => {
        console.error('Simulation error:', error);
        alert(`Error: ${error.error}`);
        startBtn.disabled = false;
        stopBtn.disabled = true;
    });
});

// Handle start simulation
function handleStartSimulation(e) {
    e.preventDefault();
    
    if (!socket.connected) {
        alert('Not connected to server. Please refresh the page.');
        return;
    }
    
    const formData = new FormData(simForm);
    const params = {};
    const initialConditions = {};
    
    // Separate parameters and initial conditions
    document.querySelectorAll('input').forEach(input => {
        const value = input.type === 'number' ? parseFloat(input.value) : input.value;
        if (input.name.startsWith('initial_')) {
            initialConditions[input.name] = value;
        } else {
            params[input.name] = value;
        }
    });
    
    // Emit start simulation event
    socket.emit('start_simulation', {
        sim_id: simId,
        parameters: params,
        initial_conditions: initialConditions,
        steps: 1000  // Default number of steps
    });
}

// Handle stop simulation
function handleStopSimulation() {
    if (currentRoom) {
        socket.emit('stop_simulation', { room: currentRoom });
    }
}

// Update grid display (to be implemented in grid_renderer.js)
function updateGridDisplay(data) {
    if (window.updateGrid) {
        window.updateGrid(data.grid, colorScheme);
    }
}
