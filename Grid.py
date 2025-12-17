from typing import List
from colorama import Fore, Back, Style, init

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