try:    
    from .Grid import SimulatorGrid, Grid
except ImportError:
    from Grid import SimulatorGrid, Grid
import os
import time

class Sim1(SimulatorGrid):
    def __init__(self, width: int, height: int, time_step: float):
        super().__init__(width, height, time_step, None)
        
    def _compute_cell_update(self, i: int, j: int, use_diagonals: bool = False, wrap: bool = False,**kwargs) -> float:
        # Placeholder implementation - override in subclasses
        current_value = self.get_value(i, j)
        current_value /= 9
        current_value += sum(self.get_neighbors(i, j))/10
        return current_value

if __name__ == "__main__":
    # Create a larger grid for better visualization 
    grid = Sim1(30, 20, 0.1)
    
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