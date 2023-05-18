from maze_generator import gen_maze, write_maze_to_file, get_maze_from_file
import maze_generator
import openai
import os
import json, mazeutil


DIR_UP = "up"
DIR_DOWN = "down"
DIR_LEFT = "left"
DIR_RIGHT = "right"

PARAM_PROMPT = "prompt"
PARAM_COMP = "completion"

MODEL_35_T = "gpt-3.5-turbo-0301"
MODEL_4_8K = "gpt-4-0314"

PRICING = {
    MODEL_35_T:{
        PARAM_PROMPT:0.002,
        PARAM_COMP:0.002
    },
    MODEL_4_8K:{
        PARAM_PROMPT:0.03,
        PARAM_COMP:0.06
    }
}



def main():
    using_wall_mark = maze_generator.DEFAULT_WALL
    using_way_mark = maze_generator.DEFALUT_WAY
    using_ent_mark = maze_generator.DEFAULT_ENT
    using_exit_mark = maze_generator.DEFAULT_EXIT

    map_file_name = input("input map file name in [maps], leave blank and gen new map: ")
    ent, exit, maze = (0,0,0)
    using_prev_tip = True if input("Using Pre-Step-Tips to improve efficent?(y/n)").strip().lower() == "y" else False
    using_self_fix_check = True if input("Using Self-Fix-Check to improve efficent?(y/n)").strip().lower() == "y" else False
    using_main_model = MODEL_4_8K if input("Using GPT-4 instead of GPT3.5-turbo as main model?(y/n)").strip().lower() == "y" else MODEL_35_T


    # Get map from generator or file
    if map_file_name.strip() == "" or os.path.exists("maps" + os.path.sep + map_file_name) == False:
        ent, exit, maze = gen_maze(15, 15, surrand=True, wall_mark=using_wall_mark, path_way_mark=using_way_mark, entrance_mark=using_ent_mark, exit_mark=using_exit_mark)
        new_map_file_name = get_new_map_file_name()
        if new_map_file_name == False:
            print("Too many map files, not saved")
        else:
            writting_res = write_maze_to_file(maze, file_name=new_map_file_name)
            if writting_res == True:
                print("New Map Saved as " + new_map_file_name)
            else:
                print("Writting new map failed")
    else:
        map_file_name = "maps" + os.path.sep + map_file_name
        print("reading from " + map_file_name)
        success, msg, legend, ent, maze = get_maze_from_file(map_file_name)
        using_wall_mark, using_way_mark, using_ent_mark, using_exit_mark = legend
        if success == True:
            input("Reading Finished")
            # print(maze)
        else:
            print(f"Reading Maze File Failed: {msg}")
            return
        
    # read api_key from config file
    api_key = None
    success, msg = mazeutil.get_api_key()
    if success == False:
        print(f"Fail to get API Key! reason:{msg}")
    api_key = msg
    
    openai.api_key = api_key
    # deprecated: print all the avaliable models about gpt
    # print([x["id"] if "gpt" in x["id"] else 0 for x in openai.Model.list()["data"]])

    for line in maze:
        print(''.join(line))

    solve_by_gpt(ent, maze, using_exit_mark, using_prev_tip=using_prev_tip, model=using_main_model, use_self_fix_check=using_self_fix_check)
    
    print(f"Finished from {ent} to {exit}")

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
def get_four_closet(maze, pos, exit_mark, natural=False, last_step_dir = "", need_straight = False):

    # 上 左 下 右
    ori = [maze[pos[0] - 1][pos[1]], maze[pos[0]][pos[1] - 1], maze[pos[0] + 1][pos[1]], maze[pos[0]][pos[1] + 1]]
    li = ["0" if x == " " else ("1" if x != exit_mark else exit_mark) for x in ori]
    li_nat = ["road" if x == "0" else ("wall" if x != exit_mark else exit_mark) for x in li]
    if need_straight:
        li_nat = [x + f"{', do not step in ' if x=='wall' else ', you can step in'}" for x in li_nat]

    res = "-".join(li)

    if natural:
        res = f"at this position, the up side is {li_nat[0]} {'(you came from there)' if last_step_dir == DIR_DOWN else ''}, the left side is {li_nat[1]}{'(you came from there)' if last_step_dir == DIR_RIGHT else ''}, the down side is {li_nat[2]}{'(you came from there)' if last_step_dir == DIR_UP else ''} and the right side is {li_nat[3]}{'(you came from there)' if last_step_dir == DIR_LEFT else ''}"
        res = f"Now, your up side:{li_nat[0]} {'(you came from there)' if last_step_dir == DIR_DOWN else ''}; left side:{li_nat[1]}{'(you came from there)' if last_step_dir == DIR_RIGHT else ''}; down side:{li_nat[2]}{'(you came from there)' if last_step_dir == DIR_UP else ''}; right side: {li_nat[3]}{'(you came from there)' if last_step_dir == DIR_LEFT else ''}"
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

def solve_by_gpt(ent, maze, exit_mark, using_prev_tip, model=MODEL_4_8K, use_self_fix_check=False, cross_check_model=MODEL_35_T):
    SYSTEM_NAME = "system"
    USER_NAME = "user"
    ASSISTANT_NAME = "assistant"
    PARAM_ROLE = "role"
    PARAM_CONTENT = "content"

    use_natural_feedback = True

    natural_closest_des = "I will tell you the closest 4 items at 4 directions."

    formated_closest_des = "The wall is \"1\" and the legal pathway is \"0\", and I will tell you the closest 4 items in the order of \"up,left,down,right\" at the format of example \"1-0-0-1\", means the up side is wall, the left side is pathway, the right side is path way, and the right side is wall. you make the next step after get my information. for example, you say \"up\", I will take one step up and tell you the new closest 4 directions' items of \"0-1-0-1\". "

    start_prompt = f'''
    Now I need you to be a explorer of an maze, try to find the pathway from the entrance  to the correct exit. The maze is a 2-D matrix, you're now on the entrance. you can only see one-step-far once. 
    The exit is "{exit_mark}", for each step, you can go "up", "down", "left" or "right". after you told me your decision for this step, {natural_closest_des if use_natural_feedback else formated_closest_des}
    At the next message, I will give you the begin situation of 4 closest items. And then ,you need to output the next step direction of "up, down, left, right" without any explanation, only one of the words of "up, down, left, right". when you see the "{exit_mark}" represents for the correct exit, step into it.
    Before you start the task, try to think and use a strategy, to find a effiency plan of doing it, such as "right hand principle". If you found you get into a dead loop, try jump out it, don't loop the repeated path again and again. Never try work into a wall.
    '''

    messages = [
        {PARAM_ROLE:SYSTEM_NAME, PARAM_CONTENT:start_prompt},
        {PARAM_ROLE:USER_NAME, PARAM_CONTENT:get_four_closet(maze, ent, exit_mark, use_natural_feedback, need_straight=model==MODEL_35_T)}
        ]
    
    gen_self_fixing_message = lambda sentence: [{PARAM_ROLE:USER_NAME, PARAM_CONTENT:f"Summarize this sentence to one-word-command of one of (up, down, left, right)  without explanation and punctuation: {sentence}"}]

    finish = False

    valid_cmd = {DIR_UP,DIR_DOWN,DIR_LEFT,DIR_RIGHT}

    asking_retry_time = 0
    MAX_ASKING_RETRY_TIME = 5
    bad_pos_retry = 0
    current_pos = [ent[0], ent[1]]
    history_path = []
    history_path.append(current_pos)
    history_dirs = []
    cost_dollar = 0

    while finish == False:
        resp_msg = ""
        try:
            resp_msg = talk_gpt(messages=messages, model_name=model)
        except Exception as e:
            print(f"err of {e}")
            continue
        instruction = resp_msg[0][PARAM_CONTENT].lower()
        cost_dollar += resp_msg[1][1] + resp_msg[2][1]
        this_time_token = resp_msg[1][0] + resp_msg[2][0]

        if use_self_fix_check == True:
            SELF_FIXING_RETRY_TIME = 5
            fixing_time = 0

            # if the command doesn't fit the format, using self_fix_model to fix it. max try 5 times. 
            while instruction not in valid_cmd and fixing_time < SELF_FIXING_RETRY_TIME:
                fixing_time += 1
                print(f"Cmd illegal, try self-check and fixing....")
                fixing_msg = gen_self_fixing_message(instruction)
                # TODO to use GPT3.5 to correct command
                fix_resp = ""
                try:
                    fix_resp = talk_gpt(messages=fixing_msg, model_name=cross_check_model)
                except Exception as e:
                    print(f"error while try self_fixing. Exception of {e}")
                    continue
                instruction = fix_resp[0][PARAM_CONTENT].lower()
                instruction = "".join([x if x.isalpha() else "" for x in instruction])
                cost_dollar += fix_resp[1][1] + fix_resp[2][1]
                this_time_token += fix_resp[1][0] + fix_resp[2][0]
                print(f"Fixed command at {fixing_time} time: {instruction}")

        # after possible self_fixing, if still invalid, reasking for at most <MAX_ASKING_RETRY_TIME> times.
        if instruction not in valid_cmd:
            print("instrucaion invalid: " + instruction)
            if asking_retry_time > MAX_ASKING_RETRY_TIME:
                print(f"Too many asking retry, allowed max {MAX_ASKING_RETRY_TIME} times")
                break
            asking_retry_time += 1
            continue
        else:
            asking_retry_time = 0
                    
        new_pos = one_step_move(current_pos, instruction)
        if maze[new_pos[0]][new_pos[1]] != " " and maze[new_pos[0]][new_pos[1]] != exit_mark:
            if bad_pos_retry > 5:
                print("Too many retry")
                break
            print(f"Bad instruction: {instruction} Retry")
            bad_pos_retry += 1
            continue
        else:
            bad_pos_retry = 0

        current_pos = new_pos
        history_path.append(current_pos)
        history_dirs.append(instruction)

        maze_str = get_maze_str(maze, current_pos, history_indexes=history_path)
        os.system("clear")
        print(f"Move: {instruction}.\n" + (" Now Cost: $%.2f, this round_token: %d" %(cost_dollar, this_time_token)))
        print(maze_str)

        if maze[new_pos[0]][new_pos[1]] == exit_mark:
            finish = True
            continue  
        else:
            four_closest = get_four_closet(maze, current_pos, exit_mark=exit_mark, natural=use_natural_feedback, last_step_dir= instruction if using_prev_tip else "", need_straight=model==MODEL_35_T)
            
            messages.append(resp_msg[0])
            messages.append({PARAM_ROLE:USER_NAME, PARAM_CONTENT:four_closest})
            print(messages[-1])
            with open("logs/testlog.log", "w+") as logfile:
                logfile.write(maze_str)
                logfile.write(json.dumps(messages))
            # input("press to next")

# returns (message, (prompt_token, prompt_cost), (completion_token, completion_cost))
def talk_gpt(messages, model_name):
    completion = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        n = 1,
        temperature = 1,
        stream = False
    )
    prompt_tokens = int(completion["usage"]["prompt_tokens"])
    completion_tokens = int(completion["usage"]["completion_tokens"])
    print("safe")
    return (completion.choices[0]["message"], (prompt_tokens, prompt_tokens / 1000 * PRICING[model_name][PARAM_PROMPT]) ,(completion_tokens, completion_tokens / 1000 * PRICING[model_name][PARAM_COMP]))

def get_new_map_file_name():
    for i in range(100):
        file_name = "maps" + os.path.sep + "map" + str(i) + ".txt"
        if os.path.exists(file_name) == False:
            return file_name
    return False

def read_map(filename, ent_mark, exit_mark):
    with open(filename) as map_file:
        lines = map_file.readlines()
        map = []
        for line in lines:
            map.append(list(line.strip()))
        ent = []
        exit = []
        for y in range(len(map)):
            for x in range(len(map[y])):
                if map[y][x] == ent_mark:
                    ent = (y,x)
                if map[y][x] == exit_mark:
                    exit = (y,x)

        return (ent, exit, map)


if __name__ == "__main__":
    main()