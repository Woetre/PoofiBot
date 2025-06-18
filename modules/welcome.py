import discord
from discord.ext import commands
import os

WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
AUTO_ROLE_ID = int(os.getenv("AUTO_ROLE_ID"))

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Welkombericht versturen
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            await channel.send(
                f"Hoi {member.mention} , welkom op de server van Marrit!👋\n"
                f"\n• ✅ Selecteer de rollen in #rollen"
                f"\n• 📢 Blijf op de hoogte via #stream-meldingen"
                f"\n• 💬 Klets gezellig mee in #de-babbel-hoek of spring in #babbelen!"
                f"\n\nVeel plezier & wees lief voor elkaar!💜"
            )

        # Automatisch rol geven
        role = member.guild.get_role(AUTO_ROLE_ID)
        if role:
            try:
                await member.add_roles(role, reason="Automatisch toegekende rol bij joinen.")
            except discord.Forbidden:
                print(f"❌ Bot mist permissies om rol toe te voegen aan {member}.")
