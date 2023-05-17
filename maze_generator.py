import random

DEFAULT_WALL = "█"
DEFALUT_WAY = " "
DEFAULT_ENT = "O"
DEFAULT_EXIT = "X"

# Function to generate maze
def gen_maze(width: int, length: int, entrance: tuple = None, wall_mark: str = DEFAULT_WALL, path_way_mark: str = DEFALUT_WAY, entrance_mark: str = DEFAULT_ENT, exit_mark: str = DEFAULT_EXIT, surrand: bool = False) -> tuple:

    # To create the background of the map, full of walls
    def create_grid():
        grid = [[wall_mark for j in range(width)] for i in range(length)]
        return grid

    # To create entrance of the map
    def create_entrance(grid):
        # if the entrance was given
        if not entrance:
            # decide on bottom-top or left-right side
            b_t, l_r = 0, 1
            if random.choice([b_t, l_r]) == b_t:
                entrance_y = random.choice([0, length - 1])
                entrance_x = random.randint(1, width - 2)
            else:
                entrance_y = random.randint(1, length - 2)
                entrance_x = random.choice([0, width - 1])
        else:
            entrance_y, entrance_x = entrance
        
        grid[entrance_y][entrance_x] = entrance_mark
        return (entrance_y, entrance_x)
    
    # judge whether the position is legal, walking on the side way is not allowed
    def valid_move(y, x):
        return 0 < y < length - 1 and 0 < x < width - 1

    # create ways
    # TODO: figure out how does nynx work
    def dfs(grid, y, x):
        grid[y][x] = path_way_mark
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(directions)
        
        for dy, dx in directions:
            ny, nx = y + dy * 2, x + dx * 2
            if valid_move(ny, nx) and grid[ny][nx] == wall_mark:
                grid[y + dy][x + dx] = path_way_mark
                dfs(grid, ny, nx)

    # generate part
    def generate_maze(grid, entrance):
        start_y, start_x = entrance
        if start_y == 0:
            start_y += 1
        elif start_y == length - 1:
            start_y -= 1
        elif start_x == 0:
            start_x += 1
        elif start_x == width - 1:
            start_x -= 1
        dfs(grid, start_y, start_x)
        return grid
    
    # create exit at last
    def create_exit(grid, entrance):
        edge_cells = [((i, 0), (i, 1)) for i in range(1, length-1)] + [((i, width-1), (i, width-2)) for i in range(1, length-1)] + [((0, j), (1, j)) for j in range(1, width-1)] + [((length-1, j), (length-2, j)) for j in range(1, width-1)]
        valid_exit_cells = [c for c in edge_cells if c != entrance and grid[c[1][0]][c[1][1]] == path_way_mark]
        exit_cell, adj_cell = random.choice(valid_exit_cells)
        grid[exit_cell[0]][exit_cell[1]] = exit_mark
        return exit_cell
    
    grid = create_grid()
    entrance = create_entrance(grid)
    grid = generate_maze(grid, entrance)
    exit_pos = create_exit(grid, entrance)

    if surrand:
        grid = [[wall_mark] * (width + 2)] + [[wall_mark] + row + [wall_mark] for row in grid] + [[wall_mark] * (width + 2)]
        entrance = (entrance[0] + 1, entrance[1] + 1)
        exit_pos = (exit_pos[0] + 1, exit_pos[1] + 1)

    return entrance, exit_pos, grid