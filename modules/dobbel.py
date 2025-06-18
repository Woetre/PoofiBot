import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from bot_config import GUILD_ID

class DobbelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="dobbel", description="Gooi een dobbelsteen (1 t/m 6)")
    async def dobbel(self, interaction: discord.Interaction):
        await interaction.response.defer()

        bericht = await interaction.followup.send("🎲 Gooi de dobbelsteen...")
        await asyncio.sleep(2)

        uitkomst = random.randint(1, 6)
        dobbel_emoji = {
            1: "🎲 ➀",
            2: "🎲 ➁",
            3: "🎲 ➂",
            4: "🎲 ➃",
            5: "🎲 ➄",
            6: "🎲 ➅"
        }

        await bericht.edit(content=f"{dobbel_emoji[uitkomst]} **{interaction.user.display_name}** gooide een **{uitkomst}**!")

    async def cog_load(self):
        self.bot.tree.add_command(self.dobbel, guild=GUILD_ID)
