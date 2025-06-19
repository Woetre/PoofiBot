# -- kan nog mooier gemaakt worden --#

import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from bot_config import GUILD_ID

class DobbelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="dobbel", description="Gooi 1 tot 3 dobbelstenen")
    @app_commands.describe(
        aantal="Hoeveel dobbelstenen wil je gooien? (1-3)"
    )
    async def dobbel(self, interaction: discord.Interaction, aantal: int = 1):
        if not 1 <= aantal <= 3:
            await interaction.response.send_message("❌ Kies een aantal tussen 1 en 10.", ephemeral=True)
            return

        await interaction.response.defer()

        if aantal == 1:
            bericht = await interaction.followup.send("🎲 Dobbelsteen wordt gegooid...")
        else:
            bericht = await interaction.followup.send("🎲 Dobbelstenen worden gegooid...")

        await asyncio.sleep(1.2)
        await bericht.edit(content="🔄 Rollen...")
        await asyncio.sleep(1.5)

        # Dobbel emoji's en resultaten
        dobbel_emoji = {
            1: "1️⃣", 2: "2️⃣", 3: "3️⃣",
            4: "4️⃣", 5: "5️⃣", 6: "6️⃣"
        }

        resultaten = [random.randint(1, 6) for _ in range(aantal)]
        emoji_resultaten = [f"🎲 {dobbel_emoji[r]}" for r in resultaten]
        totaal = sum(resultaten)

        beschrijving = "\n".join(emoji_resultaten)

        if aantal ==1:
            embed = discord.Embed(
                title=f"🎲 {interaction.user.display_name} gooide {aantal} dobbelsteen!",
                description=beschrijving,
                color=discord.Color.blurple()
            )
        else:
            embed = discord.Embed(
                title=f"🎲 {interaction.user.display_name} gooide {aantal} dobbelstenen!",
                description=beschrijving,
                color=discord.Color.blurple()
            )

        embed.set_footer(text=f"Totaal: {totaal}")
        await bericht.edit(content=None, embed=embed)

    async def cog_load(self):
        self.bot.tree.add_command(self.dobbel, guild=GUILD_ID)
