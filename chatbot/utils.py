import json
import os


def load_roles_from_file(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    return data["roles"]


def load_user_roles(user_roles_file: str):
    if os.path.isfile(user_roles_file):
        with open(user_roles_file, "r") as f:
            return json.load(f)
    else:
        return {}


def save_user_roles(user_roles_file: str, user_roles: dict):
    with open(user_roles_file, "w") as f:
        json.dump(user_roles, f)



