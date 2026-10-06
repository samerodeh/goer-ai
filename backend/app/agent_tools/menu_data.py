import json

file_path = "app/data/menu.json"

with open(file_path, "r", encoding="utf-8") as file:
    menu_data = json.load(file)

print("json file loaded!")
