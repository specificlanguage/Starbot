from discord.ext import commands
from pymongo import MongoClient
import logging
import yaml

settings = yaml.load(open("settings.yml", "r"))
discord_token = settings.get("discord_bot_token")
mongo_user, mongo_pass, mongo_db = \
    settings.get("mongo_username"), settings.get("mongo_password"), settings.get("mongo_db")

print('settings.yml has loaded.')

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

client = MongoClient('mongodb+srv://' + mongo_user + ":" + mongo_pass + "@cluster0.n0rcn.mongodb.net/"
                     + mongo_db + '?retryWrites=true&w=majority')
db = client.test

bot = commands.Bot(command_prefix='%')


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@bot.command(name="ping")
async def ping(ctx):
    await ctx.send('pong')


bot.run(discord_token)

