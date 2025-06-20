import discord
from discord.ext import commands
from discord import app_commands
import asyncpg
import random
import datetime
from math import floor, sqrt
from bot_config import GUILD_ID

# Levelberekening
def calculate_level(xp: int) -> int:
    return floor(0.1 * sqrt(xp))

# XP nodig voor volgend level
def xp_for_next_level(level: int) -> int:
    return int((level + 1) ** 2 * 100)

# Rollen per level (pas deze IDs aan!)
LEVEL_ROLES = {
    5: 123456789012345678,
    10: 223456789012345678,
    20: 323456789012345678
}


class XPCog(commands.Cog):
    def __init__(self, bot, db_pool):
        self.bot = bot
        self.db_pool: asyncpg.Pool = db_pool

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or len(message.content) < 5:
            return

        user_id = message.author.id
        now = datetime.datetime.utcnow()

        async with self.db_pool.acquire() as conn:
            data = await conn.fetchrow("SELECT xp, last_message_ts FROM xp_users WHERE user_id = $1", user_id)

            if data and data["last_message_ts"]:
                delta = now - data["last_message_ts"]
                if delta.total_seconds() < 60:
                    return

            gained_xp = random.randint(5, 10)
            new_xp = (data["xp"] if data else 0) + gained_xp
            new_level = calculate_level(new_xp)
            old_level = calculate_level(data["xp"]) if data else 0

            if data:
                await conn.execute("""
                    UPDATE xp_users SET xp = $1, last_message_ts = $2 WHERE user_id = $3
                """, new_xp, now, user_id)
            else:
                await conn.execute("""
                    INSERT INTO xp_users (user_id, xp, last_message_ts) VALUES ($1, $2, $3)
                """, user_id, gained_xp, now)

        if new_level > old_level:
            await self.check_and_assign_level_roles(message.author, new_level)
            await message.channel.send(f"🎉 {message.author.mention} is level {new_level} geworden!")

    async def check_and_assign_level_roles(self, member: discord.Member, level: int):
        for lvl, role_id in LEVEL_ROLES.items():
            if level >= lvl:
                role = member.guild.get_role(role_id)
                if role and role not in member.roles:
                    await member.add_roles(role, reason="Level behaald")

    @app_commands.command(name="xp", description="Bekijk je XP en level")
    async def xp_check(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        async with self.db_pool.acquire() as conn:
            data = await conn.fetchrow("SELECT xp FROM xp_users WHERE user_id = $1", user_id)

        xp = data["xp"] if data else 0
        level = calculate_level(xp)
        next_xp = xp_for_next_level(level)
        progress = f"{xp}/{next_xp} XP"

        embed = discord.Embed(
            title=f"📈 XP Overzicht voor {interaction.user.display_name}",
            description=f"**Level:** {level}\n**XP:** {progress}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim je dagelijkse XP")
    async def claim_daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        today = datetime.date.today()

        async with self.db_pool.acquire() as conn:
            data = await conn.fetchrow("SELECT xp, last_daily_claim FROM xp_users WHERE user_id = $1", user_id)

            if data and data["last_daily_claim"] == today:
                await interaction.response.send_message("⏳ Je hebt je daily al geclaimd vandaag!", ephemeral=True)
                return

            gained = random.randint(50, 100)
            new_xp = (data["xp"] if data else 0) + gained

            if data:
                await conn.execute("""
                    UPDATE xp_users SET xp = $1, last_daily_claim = $2 WHERE user_id = $3
                """, new_xp, today, user_id)
            else:
                await conn.execute("""
                    INSERT INTO xp_users (user_id, xp, last_daily_claim) VALUES ($1, $2, $3)
                """, user_id, gained, today)

        await interaction.response.send_message(f"✅ Je hebt {gained} XP geclaimd!", ephemeral=True)

    @app_commands.command(name="leaderboard", description="Bekijk de top 10 XP gebruikers")
    async def leaderboard(self, interaction: discord.Interaction):
        async with self.db_pool.acquire() as conn:
            top = await conn.fetch("""
                SELECT user_id, xp FROM xp_users ORDER BY xp DESC LIMIT 10
            """)

        embed = discord.Embed(
            title="🏆 XP Leaderboard",
            color=discord.Color.gold()
        )

        for i, row in enumerate(top, start=1):
            user = self.bot.get_user(row["user_id"]) or f"<@{row['user_id']}>"
            level = calculate_level(row["xp"])
            embed.add_field(
                name=f"{i}. {user}",
                value=f"Level {level} - {row['xp']} XP",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    async def cog_load(self):
        # Database-tabel aanmaken
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS xp_users (
                    user_id BIGINT PRIMARY KEY,
                    xp INTEGER NOT NULL DEFAULT 0,
                    last_message_ts TIMESTAMP,
                    last_daily_claim DATE
                );
            """)

        # Slash commands syncen naar guild
        self.bot.tree.add_command(self.xp_check, guild=GUILD_ID)
        self.bot.tree.add_command(self.claim_daily, guild=GUILD_ID)
        self.bot.tree.add_command(self.leaderboard, guild=GUILD_ID)