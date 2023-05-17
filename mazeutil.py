# coding: utf-8
import os

# return (success, msg)
def get_api_key():
    if os.path.exists("proj_config/api_key.conf") == False:
        return (False, "No API-key File!")

    with open("proj_config/api_key.conf") as api_key_file:
        api_key = api_key_file.readline().strip()
        if api_key == "":
            return (False, "API-KEY is Empty!")
        return (True, api_key)