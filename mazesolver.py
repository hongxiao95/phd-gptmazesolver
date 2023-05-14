from maze_generator import gen_maze
import openai
import os
import copy


DIR_UP = "up"
DIR_DOWN = "down"
DIR_LEFT = "left"
DIR_RIGHT = "right"

def main():
    exit_mark = "Q"
    ent, exit, maze = gen_maze(10, 10, surrand=True, exit_mark="Q")
    api_key = None
    if os.path.exists("proj_config/api_key.conf") == False:
        print("No API-key File!")
        return

    with open("proj_config/api_key.conf") as api_key_file:
        api_key = api_key_file.readline().strip()
        if api_key == "":
            print("API-KEY is Empty!")
            return
    
    openai.api_key = api_key
    print([x["id"] if "gpt" in x["id"] else 0 for x in openai.Model.list()["data"]])

    for line in maze:
        print(''.join(line))

    solve_by_gpt_4(ent, maze, "Q")
    
    print(ent)
    print(exit)

def get_maze_str(maze, current_pos, history_indexes):
    his_mark = "●"
    current_mark = "◎"
    cache_str = ""
    item = ""
    for y in range(len(maze)):
        for x in range(len(maze[y])):
            item = maze[y][x]
            if (y, x) in history_indexes:
                item = his_mark
            if y == current_pos[0] and x == current_pos[1]:
                item = current_mark
            cache_str += item
        cache_str += "\n"
    return cache_str
def get_four_closet(maze, pos, exit_mark, natural=False):

    # 上 左 下 右
    ori = [maze[pos[0] - 1][pos[1]], maze[pos[0]][pos[1] - 1], maze[pos[0] + 1][pos[1]], maze[pos[0]][pos[1] + 1]]
    li = ["0" if x == " " else ("1" if x != exit_mark else exit_mark) for x in ori]
    li_nat = ["pathway" if x == "0" else ("wall" if x != exit_mark else exit_mark) for x in li]

    res = "-".join(li)

    if natural:
        res = f"at this position, the up side is {li_nat[0]}, the left side is {li_nat[1]}, the down side is {li_nat[2]} and the right side is {li_nat[3]}"
    return res

def one_step_move(pos, dir):
    if dir == DIR_UP:
        return (pos[0] - 1, pos[1])
    if dir == DIR_DOWN:
        return (pos[0] + 1, pos[1])
    if dir == DIR_LEFT:
        return (pos[0], pos[1] - 1)
    if dir == DIR_RIGHT:
        return (pos[0], pos[1] + 1)

def solve_by_gpt_4(ent, maze, exit_mark):
    SYSTEM_NAME = "system"
    USER_NAME = "user"
    ASSISTANT_NAME = "assistant"
    PARAM_ROLE = "role"
    PARAM_CONTENT = "content"

    use_natural_feedback = True

    natural_closest_des = "I will tell you the closest 4 items at four directions."

    formated_closest_des = "The wall is \"1\" and the legal pathway is \"0\", and I will tell you the closest 4 items in the order of \"up,left,down,right\" at the format of example \"1-0-0-1\", means the up side is wall, the left side is pathway, the right side is path way, and the right side is wall. you make the next step after get my information. for example, you say \"up\", I will take one step up and tell you the new closest 4 directions' items of \"0-1-0-1\". "

    start_prompt = f'''
    Now I need you to be a explorer of a maze, try to find the pathway from the entrance  to the correct exit. The maze is a 2-D matrix, you're now on the entrance. you can only see one-step-far once. 
    The exit is "{exit_mark}", for each step, you can go "up", "down", "left" or "right". after you told me your decision for this step, {natural_closest_des if use_natural_feedback else formated_closest_des}
    At the next message, I will give you the begin situation of 4 closest items. And then ,you need to output the next step direction of "up, down, left, right" without any explanation, only one of the words of "up, down, left, right". when you see the "{exit_mark}" represents for the correct exit, step into it."  
    Before you start the task, try to think and use a strategy, to find a effiency plan of doing it. If you found you get into a dead loop, try jump out it, don't loop the repeated path again and again.
    '''

    messages = [
        {PARAM_ROLE:SYSTEM_NAME, PARAM_CONTENT:start_prompt},
        {PARAM_ROLE:USER_NAME, PARAM_CONTENT:get_four_closet(maze, ent, exit_mark, use_natural_feedback)}
        ]

    finish = False

    valid_cmd = {DIR_UP,DIR_DOWN,DIR_LEFT,DIR_RIGHT}

    retry_times = 0
    bad_pos_retry = 0
    current_pos = [ent[0], ent[1]]
    history_path = []
    history_path.append(current_pos)
    history_dirs = []

    while finish == False:
        resp_msg = talk_gpt_4(messages=messages)
        instruction = resp_msg[PARAM_CONTENT].lower()

        if instruction not in valid_cmd:
            if retry_times > 5:
                print("Too many retry")
                break
            retry_times += 1
            continue
        else:
            retry_times = 0

        new_pos = one_step_move(current_pos, instruction)
        if maze[new_pos[0]][new_pos[1]] != " ":
            if bad_pos_retry > 5:
                print("Too many retry")
                break
            print(f"BAD POS {instruction} Retry")
            bad_pos_retry += 1
            continue
        else:
            bad_pos_retry = 0

        current_pos = new_pos
        history_path.append(current_pos)
        history_dirs.append(instruction)

        maze_str = get_maze_str(maze, current_pos, history_indexes=history_path)
        os.system("clear")
        print(instruction)
        print(maze_str)

        if maze[new_pos[0]][new_pos[1]] == exit_mark:
            finish = True
            continue  
        else:
            four_closest = get_four_closet(maze, current_pos, exit_mark=exit_mark, natural=use_natural_feedback)
            
            messages = [messages[0]] + [{PARAM_ROLE:USER_NAME, PARAM_CONTENT:f"From the entrance, you've already walked the following step:[{','.join(history_dirs)}] and now " + four_closest + "which direction will you go next?"}]
            print(messages[1])
            # input("press to next")

def talk_gpt_4(messages):
    completion = openai.ChatCompletion.create(
        model="gpt-4-0314",
        messages=messages,
        n = 1,
        temperature = 1,
        stream = False
    )
    return completion.choices[0]["message"]

if __name__ == "__main__":
    main()