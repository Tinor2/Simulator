from Grid import Grid
import time
import copy
import os

class HeatGrid(Grid):
    def __init__(self, width:int, height:int, time_step:float, thermal_diffusivity:float):
        super().__init__(width+2, height+2, None)
        self.lost_heat = []
        self.obstacle_mask = [[0 for _ in range(self.width)] for _ in range(self.height)]
        if time_step <= 1/(4*thermal_diffusivity):
            self.time_step = time_step
            self.thermal_diffusivity = thermal_diffusivity
        else:
            raise ValueError("Time step is too large, or thermal diffusivity is too small")
        # Create a second grid for double buffering
        self.next_grid = copy.deepcopy(self.grid)
    def set_obstacle(self, x1, y1, x2, y2):
        for i in range(y1+1, y2+2):
            for j in range(x1+1, x2+2):
                self.obstacle_mask[i][j] = 1
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


    def total_heat(self):
        total = 0
        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):
                total += self.grid[i][j]
        return total
    def set_heat(self, x:int, y:int, amount:int):
        self.update(x+1, y+1, amount)
        
    def set_heat_block(self, x1:int, y1:int, x2:int, y2:int, amount:int):
        # Convert to 1-based coordinates and ensure within grid bounds
        x1 = max(1, min(x1 + 1, self.width - 2))
        y1 = max(1, min(y1 + 1, self.height - 2))
        x2 = max(1, min(x2 + 1, self.width - 2))
        y2 = max(1, min(y2 + 1, self.height - 2))
        
        # Ensure x1,y1 is top-left and x2,y2 is bottom-right
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
            
        # Set all cells in the block to the specified amount
        for i in range(y1, y2 + 1):
            for j in range(x1, x2 + 1):
                self.grid[i][j] = amount
    def update_grid(self, use_diagonals: bool = False, wrap: bool = False, delay: float = 0):
        """Update the grid one timestep forward, applying optional diagonal diffusion,
        periodic (wrap-around) boundaries, and insulated obstacles.
        """
        buffer_grid = [row[:] for row in self.grid]  # double-buffer for stability

        for i in range(1, self.height - 1):
            for j in range(1, self.width - 1):

                # Skip obstacle cells (perfect insulators)
                if self.obstacle_mask[i][j] == 1:
                    buffer_grid[i][j] = self.grid[i][j]
                    continue

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

                # Update temperature
                buffer_grid[i][j] = self._heat_equation(self.grid[i][j], ortho_neighbors, diag_neighbors)

        # Swap buffer → current
        self.grid = buffer_grid

        # Optional: slow down for visualization
        if delay > 0:
            time.sleep(delay)

    def run(self, steps:int, is_color:bool):
        self.lost_heat = [self.total_heat()]
        self.render_colored_grid()
        for step in range(steps):
            self.update_grid(use_diagonals=True, delay=True, wrap = False)
            if is_color:
                self.render_colored_grid()
            else:
                self.display(is_round=True)
            self.lost_heat.append(self.total_heat())
            print(f"Total heat: {self.total_heat():.2f}")
            # time.sleep(0.1)  # Pause briefly to see the changes
            self.lost_heat.append(self.total_heat())
        return self.lost_heat
            



if __name__ == "__main__":
    # Create a larger grid for better visualization 
    grid = HeatGrid(100, 300 , 0.25, 1)
    
    # Add some initial heat sources
    grid.set_heat(2,2, 20)
    # grid.set_obstacle(10, 10, 26, 11)
    
    print("Initial state:")
    # lost_heat = grid.run(50, True)
    for n in range(1000):
        
        grid.set_heat(0,0, 30)
        grid.set_heat(30,24, 20)
        grid.update_grid(use_diagonals=True, wrap=True, delay=0.000000001)
        os.system('cls' if os.name == 'nt' else 'clear')
        grid.render_colored_grid()
        print("\n\n\n")
        # time.sleep(0.1)
        
        


    



    
