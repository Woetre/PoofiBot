import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import sys
import logging

# ─────── Omgeving ───────
env_choice = os.getenv("ENV")
if not env_choice:
    env_choice = "production" if "--env=production" in sys.argv else "development"
os.environ["ENV"] = env_choice  # Zodat andere modules dit ook kunnen lezen
print(f"🚀 Bot gestart in '{env_choice}' modus.")

# ─────── .env laden ───────
dotenv_path = os.path.join("config", f".env.{env_choice}")
load_dotenv(dotenv_path)

# ─────── Config ophalen ───────
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN ontbreekt in je .env bestand.")

GUILD_ID = discord.Object(id=int(os.getenv("GUILD_ID")))
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
AUTO_ROLE_ID = int(os.getenv("AUTO_ROLE_ID"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# ─────── Logging ───────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/discord.log", encoding="utf-8", mode="w"),
        logging.StreamHandler(sys.stdout)
    ],
    format="[{asctime}] [{levelname:<8}] {name}: {message}",
    style="{"
)

# ─────── Intents ───────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ─────── Bot initialiseren ───────
bot = commands.Bot(command_prefix="!", intents=intents)
bot.synced = False  # Toevoegen van attribuut om dubbel syncen te vermijden

# ─────── Setup Hook ───────
@bot.event
async def setup_hook():
    from modules.core import Core
    await bot.add_cog(Core(bot, db_config=DB_CONFIG))

    # Slash commands slechts één keer syncen
    if not bot.synced:
        await bot.tree.sync(guild=GUILD_ID)
        bot.synced = True
        logging.info("🔁 Slash commands gesynchroniseerd met Discord.")

# ─────── Bot starten ───────
bot.run(TOKEN)
