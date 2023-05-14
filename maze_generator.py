import random

def gen_maze(width: int, length: int, entrance: tuple = None, wall_mark: str = "M", path_way_mark: str = " ", entrance_mark: str = "O", exit_mark: str = "Q", surrand: bool = False) -> tuple:

    def create_grid():
        grid = [[wall_mark for j in range(width)] for i in range(length)]
        return grid

    def create_entrance(grid):
        if not entrance:
            entrance_y = random.choice([0, length - 1])
            entrance_x = random.randint(1, width - 2)
        else:
            entrance_y, entrance_x = entrance
        
        grid[entrance_y][entrance_x] = entrance_mark
        return (entrance_y, entrance_x)
    
    def valid_move(y, x):
        return 0 < y < length - 1 and 0 < x < width - 1

    def dfs(grid, y, x):
        grid[y][x] = path_way_mark
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        random.shuffle(directions)
        
        for dy, dx in directions:
            ny, nx = y + dy * 2, x + dx * 2
            if valid_move(ny, nx) and grid[ny][nx] == wall_mark:
                grid[y + dy][x + dx] = path_way_mark
                dfs(grid, ny, nx)

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