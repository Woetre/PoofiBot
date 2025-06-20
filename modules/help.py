#-- final --#

import discord
from discord.ext import commands
from discord import app_commands
from bot_config import GUILD_ID
import math

class HelpView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, commands_list, per_page=5):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.commands_list = commands_list
        self.per_page = per_page
        self.page = 0
        self.max_pages = math.ceil(len(commands_list) / per_page)

    def get_embed(self):
        embed = discord.Embed(
            title="📖 Beschikbare Commands",
            description=f"Pagina {self.page + 1} van {self.max_pages}",
            color=discord.Color.blurple()
        )

        start = self.page * self.per_page
        end = start + self.per_page
        for cmd in self.commands_list[start:end]:
            embed.add_field(
                name=f"/{cmd.name}",
                value=cmd.description or "Geen beschrijving",
                inline=False
            )

        return embed

    async def send_error(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message, ephemeral=True, delete_after=3)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def vorige(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message("⛔ Alleen jij kunt deze knoppen gebruiken.", ephemeral=True)

        if self.page == 0:
            return await self.send_error(interaction, "❌ Je zit al op de eerste pagina.")

        self.page -= 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def volgende(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message("⛔ Alleen jij kunt deze knoppen gebruiken.", ephemeral=True)

        if self.page >= self.max_pages - 1:
            return await self.send_error(interaction, "❌ Je zit al op de laatste pagina.")

        self.page += 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Toont een overzicht van alle slash commands")
    async def help_command(self, interaction: discord.Interaction):
        commands_list = self.bot.tree.get_commands(guild=interaction.guild)

        if not commands_list:
            return await interaction.response.send_message("⚠️ Geen commands gevonden.", ephemeral=True)

        view = HelpView(interaction, commands_list)
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def cog_load(self):
        self.bot.tree.add_command(self.help_command, guild=GUILD_ID)
