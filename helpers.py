import yaml
import logging
import discord
import re
from emoji import UNICODE_EMOJI

settings = yaml.load(open("settings.yml", "r"), Loader=yaml.FullLoader)

# logger
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# get_credentials and get_token
# Gets discord bot token and credentials from yml file.

def get_token():
    return settings.get("discord_bot_token")

def get_credentials():
    return [settings.get("mongo_username"), settings.get("mongo_password"), settings.get("mongo_db")]

# create_embed
# Creates embeds for messages for starboards.
def create_embed(message):
    avatar_url = "https://cdn.discordapp.com/avatars/" + str(message.author.id) + "/" + message.author.avatar + ".jpg"

    embed = discord.Embed(
        description=message.content)
    embed.add_field(name="Original message:", value="[Click to jump!](" + message.jump_url + ")", inline=False)
    embed.set_author(name=message.author.name, icon_url=avatar_url)
    embed.set_footer(text=message.created_at.strftime("%d %B %Y, %H:%M:%S"))
    try:
        embed.set_image(url=message.attachments[0].url)
    except AttributeError:
        pass
    except IndexError:
        pass
    return embed

# get_board_name:
# Gets the board name. The database makes it so that the board name has the guild id preceding the board_name.
def get_board_name(guild_id, board_name):
    return board_name + "-" + str(guild_id)


""" 
validate_reaction() does all the work to validate reactions and check for several things:
- Did the author react?
- Is there a valid reaction to count?
- Was the reaction was a star message?
If any of the above, it doesn't count, and will return a none object.
Upon success, it will return a list with two objects:
- Index 0 will return the board name to check and update
- Index 1 will return the dictionary request, which also contains all other required objects.
"""


async def validate_reaction(bot, payload):
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    emoji = str(payload.emoji)  # this is due to mongodb's limitations. Probably have to fix this.
    user = bot.get_user(id=payload.user_id)
    valid_reactions = bot.db.channels.find_one({"guild": channel.guild.id, "$or": [
        {"reaction": emoji}, {"antistar": emoji}]})
    board_name = valid_reactions["name"]
    star_messages = bot.db.star_messages.find_one(
        {"board_name": board_name, "star_message": payload.message_id})
    antistar = False

    if user == message.author or valid_reactions is None or star_messages is not None:
        return None  # reactions made by users do not count.
    try:
        if valid_reactions["antistar"] == emoji:
            antistar = True
    except KeyError:
        pass
    return [board_name, {"reactor": user.name, "message": message.id,
                         "message_author": message.author.name,
                         "reaction": emoji, "antistar": antistar}]

# check_if_emoji
# Given a string, returns if it's an emoji or not. Pretty simple.

def is_emoji(bot, emoji: str):
    if emoji in UNICODE_EMOJI:
        return True
    name, emoji_id = re.split(":>", emoji) # Note: discord emojis are in format <:name:id>
    if bot.get_emoji(emoji_id) is not None:
        return True
    return False

def get_error_message(message_name):
    errors = yaml.load(open("errors.yml", "r"), Loader=yaml.FullLoader)
    return errors.get(message_name)

