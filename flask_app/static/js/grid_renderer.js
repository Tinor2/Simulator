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
    
    // Calculate cell size to fit the grid
    const maxCellSize = Math.min(canvas.width / gridWidth, canvas.height / gridHeight);
    cellSize = Math.max(5, Math.min(20, maxCellSize)); // Keep cell size reasonable
    
    // Center the grid
    const offsetX = (canvas.width - (gridWidth * cellSize)) / 2;
    const offsetY = (canvas.height - (gridHeight * cellSize)) / 2;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid cells
    for (let y = 0; y < gridHeight; y++) {
        for (let x = 0; x < gridWidth; x++) {
            const value = grid[y][x];
            const color = getColor(value, colorScheme);
            
            ctx.fillStyle = color;
            ctx.fillRect(
                Math.round(offsetX + x * cellSize),
                Math.round(offsetY + y * cellSize),
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
        for (let x = 0; x <= gridWidth; x++) {
            const xPos = Math.round(offsetX + x * cellSize);
            ctx.beginPath();
            ctx.moveTo(xPos, offsetY);
            ctx.lineTo(xPos, offsetY + gridHeight * cellSize);
            ctx.stroke();
        }
        
        // Horizontal lines
        for (let y = 0; y <= gridHeight; y++) {
            const yPos = Math.round(offsetY + y * cellSize);
            ctx.beginPath();
            ctx.moveTo(offsetX, yPos);
            ctx.lineTo(offsetX + gridWidth * cellSize, yPos);
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
