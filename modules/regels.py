#-- final --#

import discord
from discord.ext import commands
from discord import app_commands
from bot_config import GUILD_ID  # Zorg dat dit naar je correcte config-bestand wijst

class RegelsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="regels", description="Toon de serverregels.")
    async def regels_command(self, interaction: discord.Interaction):
        regels_tekst = (
            "**📜 Onze Serverregels**\n\n"
            "1️⃣ **Wees Respectvol** - Ga altijd met respect met elkaar om, dus geen haatdragende opmerkingen, pesten, racisme, seksisme of discriminatie van welke aard dan ook.\n"
            "2️⃣ **Geen zelfpromotie** - Maak geen reclame of ga niet jezelf promoten.\n"
            "3️⃣ **Houd het gezellig** -  Geen drama of negativiteit onnodig creëren.\n"
            "4️⃣ **Geen NSFW** - Denk hier bij aan naaktheid of andere expliciete dingen.\n"
            "5️⃣ **Geen Spam** - Spam niet heel de discord vol.\n"
            "6️⃣ **Luister naar staff leden** - Zij zijn er om de server goed te laten draaien.\n\n"
            "💜 Door op de server te blijven ga je akkoord met deze regels.\n"
        )
        await interaction.response.send_message(regels_tekst, ephemeral=True)

    @commands.command(name="regels", help="Toont de serverregels.")
    @commands.has_permissions(administrator=True)
    async def regels_prefix(self, ctx):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        regels_tekst = (
            "**📜 Onze Serverregels**\n\n"
            "1️⃣ **Wees Respectvol** - Ga altijd met respect met elkaar om, dus geen haatdragende opmerkingen, pesten, racisme, seksisme of discriminatie van welke aard dan ook.\n"
            "2️⃣ **Geen zelfpromotie** - Maak geen reclame of ga niet jezelf promoten.\n"
            "3️⃣ **Houd het gezellig** - Geen drama of negativiteit onnodig creëren.\n"
            "4️⃣ **Geen NSFW** - Denk hier bij aan naaktheid of andere expliciete dingen.\n"
            "5️⃣ **Geen Spam** - Spam niet heel de discord vol.\n"
            "6️⃣ **Luister naar staff leden** - Zij zijn er om de server goed te laten draaien.\n"
            "7️⃣ **/Regels** - Toont de serverregels.\n\n"
            "💜 Door op de server te blijven ga je akkoord met deze regels.\n"
        )
        await ctx.send(regels_tekst)

    @regels_prefix.error
    async def regels_prefix_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Je hebt geen toestemming om dit commando te gebruiken.", delete_after=5)

    async def cog_load(self):
        self.bot.tree.add_command(self.regels_command, guild=GUILD_ID)
