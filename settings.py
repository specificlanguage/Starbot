import yaml
import logging

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
