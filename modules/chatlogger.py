import discord
from discord.ext import commands
import datetime
import os
import asyncpg

LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))

class LoggerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_log(self, message: str, level: str = "info"):
        emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "event": "📌"
        }.get(level, "🪵")

        channel = self.bot.get_channel(LOG_CHANNEL_ID)
        if channel:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await channel.send(f"{emoji} `[LOG - {timestamp}]` {message}")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.send_log("Bot is opgestart ✅", level="event")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.send_log(f"👋 Lid toegetreden: {member}", level="event")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.send_log(f"👋 Lid vertrokken: {member}", level="event")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.Forbidden):
            await self.send_log(f"🚫 Permissiefout bij `{ctx.command}` door {ctx.author}: {error}", level="warning")
        else:
            await self.send_log(f"❌ Fout bij `{ctx.command}` door {ctx.author}: {error}", level="error")

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.Command):
        user = interaction.user
        await self.send_log(
            f"📥 Slash command uitgevoerd: `{command.name}` door {user} (ID: {user.id})",
            level="info"
        )

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        user = interaction.user
        command_name = interaction.command.name if interaction.command else "onbekend"
        await self.send_log(
            f"❌ Slash command fout: `{command_name}` door {user} (ID: {user.id}) – {type(error).__name__}: {error}",
            level="error"
        )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        await self.send_log(f"📁 Kanaal aangemaakt: {channel.name}", level="info")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        await self.send_log(f"🗑️ Kanaal verwijderd: {channel.name}", level="warning")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot:
            await self.send_log(f"🗑️ Bericht verwijderd van {message.author}: {message.content} -- in #{message.channel}", level="info")

    @commands.Cog.listener()
    async def on_disconnect(self):
        await self.send_log("🔌 Bot is tijdelijk offline (disconnect)", level="warning")

    @commands.Cog.listener()
    async def on_resumed(self):
        await self.send_log("🔁 Verbinding hervat met Discord", level="info")

    async def cog_load(self):
        print("✅ LoggerCog geladen")

        # Test databaseconnectie bij opstart (indien pool beschikbaar)
        db_pool = getattr(self.bot, "db_pool", None)
        if db_pool:
            try:
                async with db_pool.acquire() as conn:
                    await conn.execute("SELECT 1")
                await self.send_log("💾 Databaseconnectie succesvol.", level="info")
            except asyncpg.PostgresError as e:
                await self.send_log(f"❌ Databasefout bij opstart: {type(e).__name__}: {e}", level="error")

async def setup(bot):
    await bot.add_cog(LoggerCog(bot))
