import sys
import subprocess
import os
try:
    from discord import Intents
    from discord.ext import commands
    from discord import Game
    from discord import Status
except:
    subprocess.check_call([sys.executable,'-m', 'pip', 'install', '--upgrade', 'discord'])
    subprocess.check_call([sys.executable,'-m', 'pip', 'install', '--upgrade', 'discord.py'])
    from discord import Intents
    from discord.ext import commands
    from discord import Game
    from discord import Status
    
script_directory = os.path.dirname(os.path.abspath(__file__))
txt_file_path = [os.path.join(script_directory, "applications_id.txt"), os.path.join(script_directory, "Token.txt")]

my_application_id = ',,,'

my_Token = ',,,'


class main(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='',
            intents=Intents.all(),
            sync_all_commands=True,
            application_id=my_application_id
        )
        self.initial_extension = [
            "Cogs.Commands",
            "Cogs.item"
        ]

    async def setup_hook(self):
        for ext in self.initial_extension:
            await self.load_extension(ext)
        await self.tree.sync()

    async def on_ready(self):
        print("login")
        print(self.user.name)
        print(self.user.id)
        print("===============")
        game = Game("경매 관리")
        
        await self.change_presence(status=Status.online, activity=game)

bot = main()
bot.run(f'{my_Token}')
