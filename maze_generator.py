import random, os

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

    # create roads
    # TODO: figure out how does nynx work
    def dfs(grid, y, x):
        # make current position pathway at first
        grid[y][x] = path_way_mark

        # define four directions move, represents going right, left, down and up
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

        # make the choices random
        random.shuffle(directions)
        
        # decide valid moves
        for dy, dx in directions:
            # for each direction, the two-step-further should be still wall( not allowed to step into edge of the map or create a circle)
            ny, nx = y + dy * 2, x + dx * 2
            if valid_move(ny, nx) and grid[ny][nx] == wall_mark:
                grid[y + dy][x + dx] = path_way_mark
                dfs(grid, ny, nx)

    # generate part
    def generate_maze(grid, entrance):

        start_y, start_x = entrance
        # Because the entrance point is the only legal point on the side, so the first step must step into the map
        if start_y == 0:
            start_y += 1
        elif start_y == length - 1:
            start_y -= 1
        elif start_x == 0:
            start_x += 1
        elif start_x == width - 1:
            start_x -= 1

        # dfs from the legal point inside the map
        dfs(grid, start_y, start_x)
        return grid
    
    # create exit at last
    def create_exit(grid, entrance):
        # Generate legal 4 - sides position list and their near-by in-map position.
        edge_cells = [((i, 0), (i, 1)) for i in range(1, length-1)] + [((i, width-1), (i, width-2)) for i in range(1, length-1)] + [((0, j), (1, j)) for j in range(1, width-1)] + [((length-1, j), (length-2, j)) for j in range(1, width-1)]

        # valid_exit_cells meets the consitions of: at the edge of the map; not the entrance; near-by in-map position is pathway
        valid_exit_cells = [c for c in edge_cells if c[0] != entrance and grid[c[1][0]][c[1][1]] == path_way_mark]
        exit_cell, adj_cell = random.choice(valid_exit_cells)
        grid[exit_cell[0]][exit_cell[1]] = exit_mark
        return exit_cell
    
    grid = create_grid()
    entrance = create_entrance(grid)
    grid = generate_maze(grid, entrance)
    exit_pos = create_exit(grid, entrance)

    # if the map need to be surranded by walls
    if surrand:
        grid = [[wall_mark] * (width + 2)] + [[wall_mark] + row + [wall_mark] for row in grid] + [[wall_mark] * (width + 2)]
        entrance = (entrance[0] + 1, entrance[1] + 1)
        exit_pos = (exit_pos[0] + 1, exit_pos[1] + 1)

    return entrance, exit_pos, grid


# maze file format:
'''
█ OX
<maze>
'''

# writing maze to file
def write_maze_to_file(maze_matrix:list, file_name:str, wall:str=DEFAULT_WALL, way:str=DEFALUT_WAY, ent:str=DEFAULT_ENT, exit:str=DEFAULT_EXIT):
    try:
        with open(file_name, "w") as maze_file:
            maze_file.write(f"Legend={wall}{way}{ent}{exit}\n")
            for line in maze_matrix:
                maze_file.write("".join(line) + "\n")
            return True
    except Exception as e:
        print(f"Writting maze file fail. Reason: {e}")
        return False


# get maze from file
# return: (True, msg, (wallmark, waymark, entmark, exitmark), ent_pos, maze)
def get_maze_from_file(file_name:str) -> tuple:
    if os.path.exists(file_name) == False:
        return (False, f"File <{file_name}> Not Exist.")
    
    with open(file_name, "r") as maze_file:
        ent = (0,0)
        first_line = maze_file.readline().strip()
        if first_line.startswith("Legend=") == False:
            return (False, "File to get legend")
        
        legend_list = first_line.split("=")[1].strip()
        if len(set(legend_list)) != 4:
            return (False, f"Legend count illegal. legend:{legend_list}")
        
        maze = []
        next_line = maze_file.readline().strip()
        maze_width = len(next_line)
        while next_line != "":
            new_maze_width = len(next_line)
            if new_maze_width != maze_width:
                return (False, f"Unmached Size of maze, new_width:{new_maze_width}, old_width:{maze_width}")
    
            maze.append(list(next_line))
            next_line = maze_file.readline().strip()

        legend_list = tuple(legend_list)

        found_ent = False
        for y in range(len(maze)):
            for x in range(len(maze[y])):
                if maze[y][x] == legend_list[2]:
                    ent = (y,x)
                    break
            if found_ent == True:
                break


        return (True, "success", tuple(legend_list), ent, maze)
    
if __name__ == "__main__":
    succ, msg, legneds, maze = get_maze_from_file("maps/map0.txt")
    if succ == True:
        print("\n".join(["".join(line) for line in maze]))
