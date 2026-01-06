// Grid Renderer
let canvas, ctx;
let cellSize = 20; // Default cell size
let gridWidth, gridHeight;
// Initialize the canvas
function initCanvas() {
    canvas = document.getElementById('grid-canvas');
    if (!canvas) return;
    
    ctx = canvas.getContext('2d');
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
}

// Resize canvas to fit container
function resizeCanvas() {
    if (!canvas) return;
    
    const container = canvas.parentElement;
    const size = Math.min(container.clientWidth, container.clientHeight) * 0.9;
    canvas.width = size;
    canvas.height = size;
    
    // Re-render if we have grid data
    if (window.currentGrid) {
        updateGrid(window.currentGrid, window.currentColorScheme);
    }
}

// Update the grid visualization
window.updateGrid = function(grid, colorScheme = 'heat') {
    if (!canvas || !ctx) initCanvas();
    if (!canvas) return;
    
    // Store for resize events
    window.currentGrid = grid;
    window.currentColorScheme = colorScheme;
    
    gridHeight = grid.length;
    if (gridHeight === 0) return;
    gridWidth = grid[0].length;

    // Many simulators include a +2 border. Skip the border cells when rendering.
    const skipBorder = gridHeight >= 3 && gridWidth >= 3;
    const startX = skipBorder ? 1 : 0;
    const startY = skipBorder ? 1 : 0;
    const endX = skipBorder ? gridWidth - 1 : gridWidth;
    const endY = skipBorder ? gridHeight - 1 : gridHeight;
    const renderWidth = endX - startX;
    const renderHeight = endY - startY;

    // Compute min/max over interior for normalization (heat values can be 0..30 etc.)
    let minVal = Infinity;
    let maxVal = -Infinity;
    for (let y = startY; y < endY; y++) {
        for (let x = startX; x < endX; x++) {
            const v = grid[y][x];
            if (typeof v === 'number' && Number.isFinite(v)) {
                if (v < minVal) minVal = v;
                if (v > maxVal) maxVal = v;
            }
        }
    }
    if (!Number.isFinite(minVal) || !Number.isFinite(maxVal) || minVal === maxVal) {
        minVal = 0;
        maxVal = 1;
    }
    
    // Calculate cell size to fit the grid
    const maxCellSize = Math.min(canvas.width / renderWidth, canvas.height / renderHeight);
    cellSize = Math.max(5, Math.min(20, maxCellSize)); // Keep cell size reasonable
    
    // Center the grid
    const offsetX = (canvas.width - (renderWidth * cellSize)) / 2;
    const offsetY = (canvas.height - (renderHeight * cellSize)) / 2;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid cells
    
    for (let y = startY; y < endY; y++) {
        for (let x = startX; x < endX; x++) {
            const value = grid[y][x];
            let normalized;
            // Get the current state of the dynamic color checkbox
            const dynamicColorCheckbox = document.getElementById('is_dynamic_color');
            const isDynamicColor = dynamicColorCheckbox ? dynamicColorCheckbox.checked : true; // Default to true if not found
            
            if (isDynamicColor) { 
                // Dynamic scaling: normalize between current min and max
                normalized = (value - minVal) / (maxVal - minVal);
            } else {
                // Fixed scaling: use raw value (assuming it's already in 0-1 range)
                // If values can be outside 0-1, you might want to add: normalized = Math.max(0, Math.min(1, value));
                normalized = value;
            }
            const color = getColor(normalized, colorScheme);
            
            ctx.fillStyle = color;
            ctx.fillRect(
                Math.round(offsetX + (x - startX) * cellSize),
                Math.round(offsetY + (y - startY) * cellSize),
                Math.ceil(cellSize - 1),  // Slight gap between cells
                Math.ceil(cellSize - 1)
            );
        }
    }
    
    // Draw grid lines (optional)
    if (cellSize > 10) {
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.1)';
        ctx.lineWidth = 0.5;
        
        // Vertical lines
        for (let x = 0; x <= renderWidth; x++) {
            const xPos = Math.round(offsetX + x * cellSize);
            ctx.beginPath();
            ctx.moveTo(xPos, offsetY);
            ctx.lineTo(xPos, offsetY + renderHeight * cellSize);
            ctx.stroke();
        }
        
        // Horizontal lines
        for (let y = 0; y <= renderHeight; y++) {
            const yPos = Math.round(offsetY + y * cellSize);
            ctx.beginPath();
            ctx.moveTo(offsetX, yPos);
            ctx.lineTo(offsetX + renderWidth * cellSize, yPos);
            ctx.stroke();
        }
    }
};

// Get color based on value and color scheme
function getColor(value, scheme) {
    // Normalize value to 0-1 range
    const normalized = Math.max(0, Math.min(1, value));
    
    switch(scheme) {
        case 'heat':
            // Heat map: blue -> cyan -> green -> yellow -> red
            if (normalized < 0.25) {
                // Blue to cyan
                const t = normalized * 4;
                return `rgb(0, ${Math.round(255 * t)}, 255)`;
            } else if (normalized < 0.5) {
                // Cyan to green
                const t = (normalized - 0.25) * 4;
                return `rgb(0, 255, ${Math.round(255 * (1 - t))})`;
            } else if (normalized < 0.75) {
                // Green to yellow
                const t = (normalized - 0.5) * 4;
                return `rgb(${Math.round(255 * t)}, 255, 0)`;
            } else {
                // Yellow to red
                const t = (normalized - 0.75) * 4;
                return `rgb(255, ${Math.round(255 * (1 - t))}, 0)`;
            }
            
        case 'ripple':
            // Ripple effect: dark blue -> light blue -> white
            const intensity = Math.min(1, normalized * 1.5);
            const blue = 255 - Math.round(155 * (1 - intensity));
            return `rgb(${Math.round(255 * intensity)}, ${Math.round(255 * intensity)}, ${blue})`;
            
        default:
            // Grayscale fallback
            const gray = Math.round(255 * normalized);
            return `rgb(${gray}, ${gray}, ${gray})`;
    }
}

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCanvas);
} else {
    initCanvas();
}
