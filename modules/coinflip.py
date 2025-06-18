import random
import asyncio
import discord

from discord.ext import commands
from discord import app_commands
from bot_config import GUILD_ID

class CoinflipCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="coinflip", description="Gooi een munt op: kop of munt?")
    async def coinflip(self, interaction: discord.Interaction):
        resultaat = random.choice(["Kop 🪙", "Munt 🪙"])
        await interaction.response.send_message(f"🪙 De munt landt op: **{resultaat}**!")

    async def cog_load(self):
        self.bot.tree.add_command(self.coinflip, guild=GUILD_ID)
