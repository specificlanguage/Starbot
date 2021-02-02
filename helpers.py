import yaml
import logging
import discord

settings = yaml.load(open("settings.yml", "r"), Loader=yaml.FullLoader)

# logger
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

def get_token():
    return settings.get("discord_bot_token")

def get_credentials():
    return [settings.get("mongo_username"), settings.get("mongo_password"), settings.get("mongo_db")]

def create_embed(message):
    if len(message.attachment) == 0:
        image = None
    else:
        image = message.attachments[0]
    embed = discord.Embed(
        author=message.author.name,
        description=message.content,
        image=image.url,
        footer=message.created_at.strftime("%d %B %Y, %H %M %S"))
    embed.add_field(name="Original message:", value="[Click to jump!]("+ message.jump_url + ")", inline=False)
    return embed