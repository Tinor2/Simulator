// Global variables
let socket;
let currentRoom = null;
let paramConfigs = new Map(); // Store parameter configurations for validation

// DOM Elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const simForm = document.getElementById('sim-form');
const stepCounter = document.getElementById('step-counter');
const metricValue = document.getElementById('metric-value');

// Validate a parameter value against its constraints
function validateParam(input) {
    // Skip validation for source inputs (they're validated separately)
    if (input.closest('.source-row')) {
        return true;
    }
    
    const value = parseFloat(input.value);
    const min = parseFloat(input.min);
    const max = parseFloat(input.max);
    let isValid = true;
    let message = '';

    // Check required
    if (input.required && (isNaN(value) || input.value === '')) {
        isValid = false;
        message = 'This field is required';
    } 
    // Check min/max if they exist
    else if (!isNaN(min) && value < min) {
        isValid = false;
        message = `Value must be at least ${min}`;
    } else if (!isNaN(max) && value > max) {
        isValid = false;
        message = `Value must be at most ${max}`;
    } 
    // Check if it's a valid number
    else if (isNaN(value)) {
        isValid = false;
        message = 'Please enter a valid number';
    }

    // Update UI - handle both form-group and table cell containers
    const container = input.closest('.form-group') || input.parentElement;
    let errorElement = container.querySelector('.validation-error');
    
    if (!errorElement) {
        errorElement = document.createElement('div');
        errorElement.className = 'validation-error';
        container.appendChild(errorElement);
    }

    if (isValid) {
        input.classList.remove('invalid');
        errorElement.textContent = '';
        errorElement.hidden = true;
    } else {
        input.classList.add('invalid');
        errorElement.textContent = message;
        errorElement.hidden = false;
    }

    return isValid;
}

// Validate all form inputs
function validateForm() {
    let isValid = true;
    
    // Validate regular form inputs
    document.querySelectorAll('.form-group input[type="number"]').forEach(input => {
        if (!validateParam(input)) {
            isValid = false;
        }
    });
    
    // Validate source inputs
    const sourceRows = document.querySelectorAll('.source-row');
    sourceRows.forEach((row, index) => {
        const xInput = row.querySelector('input[name="source_x"]');
        const yInput = row.querySelector('input[name="source_y"]');
        const valueInput = row.querySelector('input[name="source_value"]');
        
        // Check if any field is empty
        if (!xInput.value || !yInput.value || !valueInput.value) {
            isValid = false;
            const errorMsg = document.createElement('div');
            errorMsg.className = 'validation-error';
            errorMsg.textContent = 'Please fill in all source fields';
            errorMsg.style.color = '#ef4444';
            errorMsg.style.fontSize = '0.75rem';
            errorMsg.style.marginTop = '0.25rem';
            
            // Remove any existing error messages
            const existingError = row.querySelector('.validation-error');
            if (existingError) existingError.remove();
            
            // Add new error message
            row.querySelector('td:last-child').appendChild(errorMsg);
        } else {
            // Clear any existing error messages
            const existingError = row.querySelector('.validation-error');
            if (existingError) existingError.remove();
        }
    });
    
    return isValid;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Connect to Socket.IO
    socket = io();

    // Initialize parameter configurations for validation
    document.querySelectorAll('input[type="number"]').forEach(input => {
        const config = {
            min: input.min ? parseFloat(input.min) : undefined,
            max: input.max ? parseFloat(input.max) : undefined,
            step: input.step ? parseFloat(input.step) : undefined
        };
        paramConfigs.set(input.name, config);

        // Add validation on blur
        input.addEventListener('blur', () => validateParam(input));
        
        // Add validation on input for immediate feedback
        input.addEventListener('input', () => {
            if (input.value) {  // Only validate if there's a value
                validateParam(input);
            } else {
                // Clear validation state if field is empty
                input.classList.remove('invalid');
                const errorElement = input.closest('.form-group')?.querySelector('.validation-error');
                if (errorElement) {
                    errorElement.textContent = '';
                    errorElement.hidden = true;
                }
            }
        });
    });

    function closeAllParamTooltips() {
        document.querySelectorAll('.param-tooltip').forEach(t => {
            t.hidden = true;
        });
    }

    document.querySelectorAll('.param-info-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const id = btn.dataset.tooltipFor;
            const tooltip = document.querySelector(`.param-tooltip[data-tooltip-id="${id}"]`);
            if (!tooltip) return;

            const willShow = tooltip.hidden;
            closeAllParamTooltips();
            tooltip.hidden = !willShow;
        });
    });

    document.addEventListener('click', () => {
        closeAllParamTooltips();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAllParamTooltips();
        }
    });
    
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
        console.log("is_dynamic_color:", window.is_dynamic_color);
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

// Add a new source row to the table
function addSourceRow(x = null, y = null, value = null) {
    const tbody = document.getElementById('sources-tbody');
    const row = document.createElement('tr');
    row.className = 'source-row';
    
    const width = document.querySelector('input[name="width"]')?.value || 30;
    const height = document.querySelector('input[name="height"]')?.value || 20;
    
    row.innerHTML = `
        <td><input type="number" name="source_x" data-field-group="initial_conditions" class="source-input" min="0" max="${width}" value="${x !== null ? x : Math.floor(width/2)}"></td>
        <td><input type="number" name="source_y" data-field-group="initial_conditions" class="source-input" min="0" max="${height}" value="${y !== null ? y : Math.floor(height/2)}"></td>
        <td><input type="number" name="source_value" data-field-group="initial_conditions" class="source-input" step="0.1" value="${value !== null ? value : '10'}"></td>
        <td><button type="button" class="btn btn-sm btn-remove-source">×</button></td>
    `;
    
    tbody.appendChild(row);
    
    // Add event listener to the remove button
    row.querySelector('.btn-remove-source').addEventListener('click', () => {
        if (document.querySelectorAll('.source-row').length > 1) {
            row.remove();
        } else {
            alert('At least one source is required');
        }
    });
}

// Handle add source button click
document.getElementById('add-source')?.addEventListener('click', () => {
    addSourceRow();
});

// Handle start simulation
function handleStartSimulation(e) {
    e.preventDefault();
    
    if (!socket.connected) {
        alert('Not connected to server. Please refresh the page.');
        return;
    }
    
    // Validate all inputs before proceeding
    if (!validateForm()) {
        // Scroll to the first error
        const firstError = document.querySelector('.invalid');
        if (firstError) {
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            firstError.focus();
        }
        return;
    }
    
    const formData = {
        parameters: {},
        initial_conditions: {
            sources: []
        }
    };

    // Group form fields by their data-field-group attribute
    document.querySelectorAll('input:not(.source-input), select').forEach(input => {
        const group = input.dataset.fieldGroup;
        if (!group || !formData[group]) return;

        // Handle different input types
        if (input.type === 'checkbox') {
            formData[group][input.name] = input.checked;
        } else if (input.type === 'number') {
            formData[group][input.name] = input.value ? parseFloat(input.value) : 0;
        } else {
            formData[group][input.name] = input.value;
        }
    });
    
    // Process source inputs
    const sourceRows = document.querySelectorAll('.source-row');
    sourceRows.forEach((row, index) => {
        const x = parseInt(row.querySelector('input[name="source_x"]').value);
        const y = parseInt(row.querySelector('input[name="source_y"]').value);
        const value = parseFloat(row.querySelector('input[name="source_value"]').value);
        
        if (!isNaN(x) && !isNaN(y) && !isNaN(value)) {
            formData.initial_conditions.sources.push({ x, y, value });
        }
    });
    
    document.querySelectorAll('input, select').forEach(input => {
        const group = input.dataset.fieldGroup;
        if (!group || !formData[group]) return;

        // Handle different input types
        if (input.type === 'checkbox') {
            formData[group][input.name] = input.checked;
        } else if (input.type === 'number') {
            formData[group][input.name] = input.value ? parseFloat(input.value) : 0;
        } else {
            formData[group][input.name] = input.value;
        }
    });
    
    // Ensure frame_skip is an integer
    if ('frame_skip' in formData.initial_conditions) {
        formData.initial_conditions.frame_skip = Math.max(0, Math.floor(formData.initial_conditions.frame_skip));
    }
    
    // Ensure simulation_speed is a positive number
    if ('simulation_speed' in formData.initial_conditions) {
        formData.initial_conditions.simulation_speed = Math.max(0.1, formData.initial_conditions.simulation_speed);
    }

    // Emit start simulation event with all form data
    socket.emit('start_simulation', {
        sim_id: simId,
        parameters: formData.parameters,
        initial_conditions: formData.initial_conditions,
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
