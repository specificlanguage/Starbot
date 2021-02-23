from discord.ext import commands
from database import Database
import helpers
import discord

desc = """
    A somewhat weird bot used all kinds of things.
"""

intents = discord.Intents.default()
intents.members = True
db = Database()
discord_token = helpers.get_token()

class Bot(commands.Bot):
    def __init__(self, db, command_prefix, *args, **kwargs):
        super().__init__(command_prefix, *args, **kwargs)
        self.db = db.database


bot = Bot(db=db, description=desc, command_prefix="!", intents=intents)
# help command None is temporary right now
# we'll change prefix once everything becomes all set

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.event
async def on_disconnect():
    print('Bot was disconnected!')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send("Incorrect arguments! Use !help [command] for more information.")
    elif isinstance(error, commands.CommandNotFound):
        return
    # elif isinstance(error, commands.CommandInvokeError):
    #    await ctx.send("Incorrect arguments, use !help [command] for more info.")
    else:
        await ctx.send("Something wrong happened. Check the console.")
        raise error

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(':ping_pong: Pong!')

extensions = [
    "cogs.starboard"
]

for ext in extensions:
    bot.load_extension(ext)

bot.run(discord_token)
