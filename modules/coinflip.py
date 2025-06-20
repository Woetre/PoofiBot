#-- final --#

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random

from bot_config import GUILD_ID

class CoinflipCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="coinflip", description="Gooi een munt op: kop of munt?")
    async def coinflip(self, interaction: discord.Interaction):
        await interaction.response.send_message("🪙 Gooi de munt omhoog...")
        bericht = await interaction.original_response()

        # Simuleer animatie
        await asyncio.sleep(1)
        await bericht.edit(content="🔄 De munt draait in de lucht...")
        await asyncio.sleep(1)
        await bericht.edit(content="🔄🔄 De munt blijft draaien...")
        await asyncio.sleep(1.5)

        resultaat = random.choice(["Kop 🪙", "Munt 🪙"])
        await bericht.edit(content=f"🪙 De munt landt op: **{resultaat}**!")

    async def cog_load(self):
        self.bot.tree.add_command(self.coinflip, guild=GUILD_ID)
