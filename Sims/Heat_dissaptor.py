from Grid import SimulatorGrid
import time
import copy
import os

class HeatGrid(SimulatorGrid):
    def __init__(self, width: int, height: int, time_step: float, thermal_diffusivity: float):
        # Pass time_step to parent, add border padding
        super().__init__(width + 2, height + 2, time_step, None)
        self.thermal_diffusivity = thermal_diffusivity
        
        # Validate stability condition for heat equation
        if time_step > 1 / (4 * thermal_diffusivity):
            raise ValueError("Time step is too large, or thermal diffusivity is too small")
        
        # Rename history to lost_heat for backward compatibility
        self.lost_heat = self.history
    
    def set_obstacle(self, x1, y1, x2, y2):
        """Override to handle border offset."""
        super().set_obstacle(x1 + 1, y1 + 1, x2 + 1, y2 + 1)
    
    def _heat_equation(self, current_value: float, ortho_neighbors: list, diag_neighbors: list = None):
        """Apply the discrete heat diffusion equation."""
        if diag_neighbors is None:
            # 5-point Laplacian (standard finite difference stencil)
            laplacian = sum(ortho_neighbors) - 4 * current_value
        else:
            # 9-point Laplacian for smoother isotropy
            laplacian = (4 * sum(ortho_neighbors) + sum(diag_neighbors) - 20 * current_value) / 6
        
        # Apply forward-Euler integration
        return current_value + self.thermal_diffusivity * self.time_step * laplacian
    
    def _compute_cell_update(self, i: int, j: int, use_diagonals: bool = False, 
                            wrap: bool = False, **kwargs) -> float:
        """
        Compute the new temperature for a cell using the heat equation.
        This overrides the SimulatorGrid method.
        """
        # --- Neighbor lookup helper ---
        def neighbor(ii, jj):
            # Handle periodic wrapping if enabled
            if wrap:
                ii = (ii - 1) % (self.height - 2) + 1
                jj = (jj - 1) % (self.width - 2) + 1
            else:
                # Insulated borders (Neumann BC): reflect out-of-bounds indices
                ii = max(1, min(ii, self.height - 2))
                jj = max(1, min(jj, self.width - 2))

            # If neighbor is obstacle → insulated (no heat flow)
            if self.obstacle_mask[ii][jj] == 1:
                return self.grid[i][j]

            return self.grid[ii][jj]

        # Orthogonal (N, S, E, W) neighbors
        ortho_neighbors = [
            neighbor(i - 1, j),  # up
            neighbor(i + 1, j),  # down
            neighbor(i, j - 1),  # left
            neighbor(i, j + 1)   # right
        ]

        # Diagonal (optional)
        diag_neighbors = None
        if use_diagonals:
            diag_neighbors = [
                neighbor(i - 1, j - 1),
                neighbor(i - 1, j + 1),
                neighbor(i + 1, j - 1),
                neighbor(i + 1, j + 1)
            ]

        # Update temperature using heat equation
        return self._heat_equation(self.grid[i][j], ortho_neighbors, diag_neighbors)
    
    def _get_metric(self) -> float:
        """Calculate total heat in the grid."""
        return self.total_heat()
    
    def total_heat(self):
        """Calculate the total heat in the grid (excluding borders)."""
        total = 0
        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):
                total += self.grid[i][j]
        return total
    
    def set_value(self, x: int, y: int, value: float):
        """
        Set a value at a specific position in the simulation grid.
        
        Args:
            x: x-coordinate
            y: y-coordinate
            value: value to set
        """
        super().set_value(x + 1, y + 1, value)
    
    def set_value_block(self, x1: int, y1: int, x2: int, y2: int, value: float):
        """
        Set a rectangular block of cells to a specific value.
        
        Args:
            x1, y1: top-left corner coordinates
            x2, y2: bottom-right corner coordinates
            value: value to set for all cells in the block
        """
        super().set_value_block(x1 + 1, y1 + 1, x2 + 1, y2 + 1, value)
    
    def run(self, steps: int, is_color: bool, use_diagonals: bool = True, 
            wrap: bool = False, delay: float = 0):
        """
        Run the heat simulation with custom display.
        Overrides parent's run method to maintain backward compatibility.
        """
        self.lost_heat = [self.total_heat()]
        self.render_colored_grid()
        
        for step in range(steps):
            self.update_grid(use_diagonals=use_diagonals, delay=delay, wrap=wrap)
            
            if is_color:
                self.render_colored_grid()
            else:
                self.display(is_round=True)
                
            heat = self.total_heat()
            self.lost_heat.append(heat)
            print(f"Total heat: {heat:.2f}")
        
        return self.lost_heat


if __name__ == "__main__":
    # Create a larger grid for better visualization 
    grid = HeatGrid(100, 300, 0.25, 1)
    
    # Add some initial heat sources
    grid.set_value(2, 2, 20)
    # grid.set_obstacle(10, 10, 26, 11)
    
    print("Initial state:")
    # lost_heat = grid.run(50, True)
    for n in range(1000):
        grid.set_value(0, 0, 30)
        grid.set_value(30, 24, 20)
        grid.update_grid(use_diagonals=True, wrap=True, delay=0.000000001)
        os.system('cls' if os.name == 'nt' else 'clear')
        grid.render_colored_grid()
        print("\n\n\n")