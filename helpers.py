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
    avatar_url = "https://cdn.discordapp.com/avatars/" + str(message.author.id) + "/" + message.author.avatar + ".jpg"

    embed = discord.Embed(
        description=message.content)
    embed.add_field(name="Original message:", value="[Click to jump!](" + message.jump_url + ")", inline=False)
    embed.set_author(name=message.author.name, icon_url=avatar_url)
    embed.set_footer(text=message.created_at.strftime("%d %B %Y, %H %M %S"))
    try:
        embed.set_image(url=message.attachments[0].url)
    except AttributeError:
        pass
    except IndexError:
        pass
    return embed
