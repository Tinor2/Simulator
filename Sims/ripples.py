from Grid import SimulatorGrid, Grid
import os
import time

class Ripples(SimulatorGrid):
    def __init__(self, width: int, height: int, time_step: float):
        super().__init__(width + 2, height + 2, time_step, None)  
        # grid_flags should match the actual grid dimensions (which already has +2)
        self.grid_flags = Grid(self.width, self.height)  
    
    def _compute_cell_update(self, i: int, j: int, **kwargs) -> float:
        temp_val = 0

        # Get neighbors - note that i is row (y), j is column (x)
        neighbors = self.get_neighbors(j, i)  # Swap to x, y order
        
        if self.grid_flags.grid[i][j] > 0:  # Direct access to avoid coordinate confusion
            self.grid_flags.grid[i][j] = 0
            return 0
        else:
            for neighbor in neighbors:
                if neighbor > 0:
                    temp_val = neighbor
            self.grid_flags.grid[i][j] = temp_val
            return temp_val

    def set_value(self, x: int, y: int, value: float):
        """Set a value at a specific position in the grid and update flags."""
        super().set_value(x, y, value)
        self.grid_flags.grid[y][x] = value

    def set_value_block(self, x1: int, y1: int, x2: int, y2: int, value: float):
        """Set a block of values in the grid and update flags."""
        super().set_value_block(x1, y1, x2, y2, value)
        # Update flags for the block as well
        for i in range(y1, y2 + 1):
            for j in range(x1, x2 + 1):
                if 0 <= i < self.height and 0 <= j < self.width:
                    self.grid_flags.grid[i][j] = value


if __name__ == "__main__":
    # Create a larger grid for better visualization 
    grid = Ripples(30, 20, 0.1)
    
    print("Initial state:")
    for n in range(20):
        grid.set_value(grid.width//2, grid.height//2, 30)
        grid.set_value(0,0,30)
        grid.set_value(15,2,30)
        grid.set_value(27,19,30)
        grid.update_grid(use_diagonals=True, wrap=True, delay=0.000000001)
        # os.system('cls' if os.name == 'nt' else 'clear')
        grid.render_colored_grid()
        time.sleep(grid.time_step)
        print("\n\n\n")
        grid.render_colored_grid()
        time.sleep(grid.time_step)
        print("\n\n\n")