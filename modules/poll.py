#-- final --#
import discord
from discord import app_commands
from discord.ext import commands
from bot_config import GUILD_ID
import asyncio

class PollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Start een poll met maximaal 10 opties.")
    @app_commands.describe(
        vraag="De pollvraag die je wilt stellen",
        opties="Kiesopties gescheiden door komma’s (bijv: Ja,Nee,Misschien)"
    )
    async def poll_command(self, interaction: discord.Interaction, vraag: str, opties: str):
        emoji_cijfers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        opties_lijst = [opt.strip() for opt in opties.split(",") if opt.strip()]

        if not 2 <= len(opties_lijst) <= 5:
            await interaction.response.send_message("❌ Geef tussen de 2 en 5 opties op.", ephemeral=True)
            return

        await interaction.response.defer()

        beschrijving = ""
        for i, optie in enumerate(opties_lijst):
            beschrijving += f"{emoji_cijfers[i]} {optie}\n"

        embed = discord.Embed(
            title=f"📊 {vraag}",
            description=beschrijving,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Gemaakt door: {interaction.user.display_name}")

        bericht = await interaction.channel.send(embed=embed)
        for i in range(len(opties_lijst)):
            await bericht.add_reaction(emoji_cijfers[i])

        response = await interaction.followup.send("✅ Poll is geplaatst!")
        await asyncio.sleep(5)
        await response.delete()

    async def cog_load(self):
        self.bot.tree.add_command(self.poll_command, guild=GUILD_ID)

