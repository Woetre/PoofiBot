import os
import logging
import discord
from dotenv import load_dotenv

def get_intents():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    return intents

# ─────── Config laden ───────
def load_config():
    # Kies env
    env = os.getenv("ENV") or ("production" if "--env=production" in os.sys.argv else "development")
    dotenv_file = os.path.join("config", f".env.{env}")
    load_dotenv(dotenv_file)

    return {
        "ENV": env,
        "TOKEN": os.getenv("DISCORD_TOKEN"),
        "GUILD_ID": discord.Object(id=int(os.getenv("GUILD_ID"))),
        "DB_CONFIG": {
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "database": os.getenv("DB_NAME")
        },
        "WELCOME_CHANNEL_ID": int(os.getenv("WELCOME_CHANNEL_ID")),
        "AUTO_ROLE_ID": int(os.getenv("AUTO_ROLE_ID")),
        "handler": logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w'),
        "intents": get_intents()
    }

# ─────── Zet alles als losse variabelen ───────
_config = load_config()

ENV = _config["ENV"]
TOKEN = _config["TOKEN"]
GUILD_ID = _config["GUILD_ID"]
DB_CONFIG = _config["DB_CONFIG"]
WELCOME_CHANNEL_ID = _config["WELCOME_CHANNEL_ID"]
AUTO_ROLE_ID = _config["AUTO_ROLE_ID"]
handler = _config["handler"]
intents = _config["intents"]

