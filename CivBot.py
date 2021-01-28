from discord.ext import commands
from disputils import BotMultipleChoice

import settings

desc = """
    A somewhat weird bot used all kinds of things.
"""

db = settings.get_database()
discord_token = settings.get_token()

class Bot(commands.Bot):
    def __init__(self, db, command_prefix, *args, **kwargs):
        super().__init__(command_prefix, *args, **kwargs)
        self.db = db


bot = Bot(db=db, description=desc, command_prefix="!", help_command=None)
# help command None is temporary right now
# we'll change prefix once everything becomes all set

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.event
async def on_disconnect():
    print('Bot was disconnected!')

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send('pong')

@bot.command(name="choice")
async def choice(ctx):
    multiple_choice = BotMultipleChoice(ctx, ["Create a new starboard", "Modify a starboard", "Delete a starboard"], "Testing stuff")
    await multiple_choice.run()

    await multiple_choice.quit(multiple_choice.choice)



bot.run(discord_token)