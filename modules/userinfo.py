import discord
from discord import app_commands
from discord.ext import commands
from bot_config import GUILD_ID

class UserInfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info", description="Bekijk informatie over een gebruiker.")
    async def user_info(self, interaction: discord.Interaction, gebruiker: discord.Member = None):
        gebruiker = gebruiker or interaction.user

        roles = [role.mention for role in gebruiker.roles if role.name != "@everyone"]
        roles_text = ", ".join(roles) if roles else "Geen rollen"

        embed = discord.Embed(
            title=f"👤 Info over {gebruiker}",
            color=gebruiker.color if hasattr(gebruiker, "color") else discord.Color.blurple()
        )
        embed.set_thumbnail(url=gebruiker.display_avatar.url)
        embed.add_field(name="🆔 Gebruikers-ID", value=gebruiker.id, inline=True)
        embed.add_field(name="📅 Account aangemaakt op", value=gebruiker.created_at.strftime("%d-%m-%Y %H:%M"), inline=True)
        embed.add_field(name="👋 Lid sinds", value=gebruiker.joined_at.strftime("%d-%m-%Y %H:%M") if gebruiker.joined_at else "Onbekend", inline=True)
        embed.add_field(name="🎭 Rollen", value=roles_text, inline=False)
        embed.set_footer(text=f"Aangevraagd door {interaction.user}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    async def cog_load(self):
        self.bot.tree.add_command(self.user_info, guild=GUILD_ID)
