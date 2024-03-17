import json
import os

class read_write_json():
    def __init__ (self):

        self.command_self_data = None

        current_directory = os.getcwd()
        json_directory = os.path.join(current_directory, "json_files")
        self.json_paths = [os.path.join(json_directory, "item.json"), os.path.join(json_directory, "embeds.json"), os.path.join(json_directory, "system.json")]
        self.json_index = {"item": 0, "embeds": 1, "system": 2}

        self.bot = None
        with open(self.json_paths[0], 'r', encoding='utf-8') as file:
            self.item = json.load(file)

        with open(self.json_paths[1], 'r', encoding='utf-8') as file:
            self.embeds = json.load(file)

        with open(self.json_paths[2], 'r', encoding='utf-8') as file:
            self.system = json.load(file)

    def write_json(self, file_path, json_data):
        with open(self.json_paths[self.json_index[file_path]], "w", encoding='utf-8') as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
    
    def set_bot(self, bot):
        self.bot = bot

read_write_json_class = read_write_json()