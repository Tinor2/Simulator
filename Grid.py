from typing import List, Callable
from colorama import Fore, Back, Style, init
import time
import copy

class Grid:
    def __init__(self, width:int, height:int, valid_types:list|None=None):            
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        if valid_types is not None:
            self.valid_types = valid_types 
        else:
            self.valid_types = [] #indicates everything is valid
    def display(self, is_round:bool|None = None):
        if is_round == None:
            is_round = False
        for row in self.grid:
            if is_round:
                print([round(cell) for cell in row])
            else:
                print(row)

    def update(self, x, y, value):
        if value not in self.valid_types and self.valid_types != []:
            raise ValueError(f"Invalid value: {value}")
        self.grid[y][x] = value
    def get_value(self, x, y):
        return self.grid[x][y]

    def get_neighbors(self, x, y):
        neighbors = []
        for i in range(x-1, x+2):
            for j in range(y-1, y+2):
                if i >= 0 and i < self.height and j >= 0 and j < self.width:
                    neighbors.append(self.grid[i][j])
        return neighbors
    def render_colored_grid(self):
        """
        Renders the heat grid with colored ASCII characters based on temperature values.
        Uses a gradient from blue (cold) to red (hot).
        """
        # Define color thresholds and corresponding characters
        # Using explicit ANSI color codes with better resolution
        # Color gradient from black (cold) to red (hot)
        color_map = [
            (0.05, '\033[0m', ' '),      # Blank for very cold areas
            (0.10, '\033[90m', '░'),     # Dark Grey
            (0.20, '\033[30;107m', '▒'), # Black on white - Cold
            (0.30, '\033[37m', '▓'),     # Light Grey - Cool
            (0.40, '\033[94m', '█'),     # Blue - Mild
            (0.50, '\033[36m', '█'),     # Cyan - Warm
            (0.60, '\033[32m', '█'),     # Green - Hot
            (0.70, '\033[33m', '█'),     # Yellow - Very Hot
            (0.85, '\033[93m', '█'),     # Light Yellow - Extremely Hot
            (float('inf'), '\033[91m', '█')  # Bright Red - Maximum Heat
        ]
        
        # Print the grid with colors
        for row in self.grid[1:-1]:  # Skip the border
            for cell in row[1:-1]:        # Skip the border
                # Normalize the value to 0-1 range
                value = cell / 10.0  # Assuming max value is around 9
                value = max(0, min(1, value))  # Clamp between 0 and 1
                
                # Find the appropriate color and character
                for threshold, color, char in color_map:
                    if value <= threshold:
                        print(f"{color}{char}{Style.RESET_ALL}", end='')
                        break
            print()  # New line after each row


class SimulatorGrid(Grid):
    """
    Base class for simulation grids that evolve over time.
    Provides common methods for running simulations with timesteps.
    """
    def __init__(self, width: int, height: int, time_step: float, valid_types: list|None = None):
        super().__init__(width, height, valid_types)
        self.time_step = time_step
        self.obstacle_mask = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.history = []  # For tracking simulation metrics over time
        
    def set_obstacle(self, x1: int, y1: int, x2: int, y2: int):
        """Set a rectangular region as an obstacle."""
        for i in range(y1, y2 + 1):
            for j in range(x1, x2 + 1):
                if 0 <= i < self.height and 0 <= j < self.width:
                    self.obstacle_mask[i][j] = 1
    
    def _compute_cell_update(self, i: int, j: int, **kwargs) -> float:
        """
        Compute the new value for a cell at position (i, j).
        This method should be overridden by child classes to implement
        specific physics/rules (e.g., heat equation, wave equation, etc.)
        
        Args:
            i: row index
            j: column index
            **kwargs: additional parameters for the update computation
            
        Returns:
            The new value for the cell
        """
        raise NotImplementedError("Child classes must implement _compute_cell_update")
    
    def update_grid(self, use_diagonals: bool = False, wrap: bool = False, delay: float = 0, **kwargs):
        """
        Update the grid one timestep forward.
        
        Args:
            use_diagonals: Whether to consider diagonal neighbors
            wrap: Whether to use periodic boundary conditions
            delay: Time delay for visualization (in seconds)
            **kwargs: Additional parameters passed to _compute_cell_update
        """
        buffer_grid = [row[:] for row in self.grid]  # double-buffer for stability

        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):
                # Skip obstacle cells
                if self.obstacle_mask[i][j] == 1:
                    buffer_grid[i][j] = self.grid[i][j]
                    continue

                # Compute new value using child class implementation
                buffer_grid[i][j] = self._compute_cell_update(
                    i, j, 
                    use_diagonals=use_diagonals, 
                    wrap=wrap,
                    **kwargs
                )

        # Swap buffer → current
        self.grid = buffer_grid

        # Optional: slow down for visualization
        if delay > 0:
            time.sleep(delay)
    
    def _get_metric(self) -> float:
        """
        Calculate a simulation metric (e.g., total energy, total mass, etc.).
        Override in child classes to track specific quantities.
        
        Returns:
            A numeric metric value
        """
        total = 0
        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):
                total += self.grid[i][j]
        return total
    
    def run(self, steps: int, is_color: bool = False, use_diagonals: bool = False, 
            wrap: bool = False, delay: float = 0, display_metric: bool = True, **kwargs):
        """
        Run the simulation for a specified number of steps.
        
        Args:
            steps: Number of timesteps to simulate
            is_color: Whether to use colored rendering
            use_diagonals: Whether to consider diagonal neighbors
            wrap: Whether to use periodic boundary conditions
            delay: Time delay between steps for visualization
            display_metric: Whether to print the metric each step
            **kwargs: Additional parameters for the simulation
            
        Returns:
            List of metric values over time
        """
        self.history = [self._get_metric()]
        
        # Initial display
        if is_color:
            self.render_colored_grid()
        else:
            self.display(is_round=True)
        
        for step in range(steps):
            self.update_grid(use_diagonals=use_diagonals, wrap=wrap, delay=delay, **kwargs)
            
            if is_color:
                self.render_colored_grid()
            else:
                self.display(is_round=True)
            
            metric = self._get_metric()
            self.history.append(metric)
            
            if display_metric:
                print(f"Step {step + 1}/{steps} - Metric: {metric:.2f}")
        
        return self.history


class PairedGrid:
    def __init__(self, grid1, grid2):
        if grid1.width != grid2.width or grid1.height != grid2.height:
            raise ValueError("Grids must have the same dimensions")
        self.grid1 = grid1
        self.grid2 = grid2
        self.width = grid1.width
        self.height = grid1.height

    def display(self):
        print("Grid 1:")
        self.grid1.display()
        print("Grid 2:")
        self.grid2.display()

    def get_value(self, x, y):
        return (self.grid1.get_value(x, y), self.grid2.get_value(x, y))


def test():
    grid = Grid(10, 10, [0, 1])
    grid.display()
    grid.update(5, 5, 1)
    grid.display()
    print(grid.get_value(5, 5))
    print(grid.get_neighbors(5, 5))

def test_paired_grid():
    print("\n--- Testing PairedGrid ---")
    grid1 = Grid(5, 5)
    grid2 = Grid(5, 5)

    grid1.update(2, 2, 10)
    grid2.update(2, 2, 20)

    paired_grid = PairedGrid(grid1, grid2)
    paired_grid.display()

    print(f"Paired value at (2, 2): {paired_grid.get_value(2, 2)}")

    # Test for different dimensions
    try:
        grid3 = Grid(3, 3)
        PairedGrid(grid1, grid3)
    except ValueError as e:
        print(f"Successfully caught expected error: {e}")

if __name__ == "__main__":
    test()
    test_paired_grid()