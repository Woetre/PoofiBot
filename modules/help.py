import discord
from discord.ext import commands
from discord import app_commands
from bot_config import GUILD_ID  # Zorg dat GUILD_ID uit bot_config komt

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Toont een overzicht van alle slash commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Beschikbare Commands",
            description="Hieronder zie je een lijst met alle slash commands die je kunt gebruiken:",
            color=discord.Color.blurple()
        )

        for cmd in self.bot.tree.get_commands(guild=interaction.guild):
            embed.add_field(
                name=f"/{cmd.name}",
                value=cmd.description or "Geen beschrijving",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cog_load(self):
        self.bot.tree.add_command(self.help_command, guild=GUILD_ID)