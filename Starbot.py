import discord
import logging
import yaml

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename = 'discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

token_file = open("token.yml", "r")
settings_file = open("settings.yml", "r")
token = yaml.load(token_file, Loader=yaml.Loader).get("token")
settings = yaml.load(settings_file, Loader=yaml.FullLoader)

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")

client.run(token)
