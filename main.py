import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

#voor image generator
import aiohttp

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
GUILD_ID = discord.Object(id=1198629275687981146)

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    try:
        bot.tree.clear_commands(guild=None)
        synced = await bot.tree.sync(guild=GUILD_ID)
        print(f"Slash commands gesynchroniseerd: {len(synced)}")
    except Exception as e:
        print(f"Fout bij sync: {e}")

@bot.tree.command(name="anime", description="Toon een willekeurige anime GIF", guild=GUILD_ID)
async def animegif_command(interaction: discord.Interaction):
    await interaction.response.defer()  # optioneel: laat "aan het denken..." zien
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.nekosapi.com/v4/images/random?type=gif") as response:
            if response.status == 200:
                data = await response.json()
                gif_url = data[0]["url"]
                await interaction.followup.send(gif_url)
            else:
                await interaction.followup.send("Kon geen anime gif ophalen 😢")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)

