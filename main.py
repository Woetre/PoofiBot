import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

import re

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='*', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if re.search(r"uwu", message.content, re.IGNORECASE):
        await message.channel.send("UwU")

    await bot.process_commands(message)


# *kiekeboe
@bot.command()
async def kiekeboe(ctx):
    await ctx.send(f"kiekeboe {ctx.author.mention}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
