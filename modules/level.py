import discord
from discord.ext import commands
from discord import app_commands
import asyncpg
import random
import datetime
import math
from math import floor, sqrt
from bot_config import GUILD_ID

# Levelberekening
def calculate_level(xp: int) -> int:
    return floor(0.1 * sqrt(xp))

def xp_for_next_level(level: int) -> int:
    return int((level + 1) ** 2 * 100)

# Rollen per level
LEVEL_ROLES = {
    5: 1385726023387320392,
    10: 1385726078370451486,
    20: 1385726108619509760
}

class LeaderboardView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, leaderboard_data, per_page=10):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.data = leaderboard_data
        self.per_page = per_page
        self.page = 0
        self.max_pages = math.ceil(len(self.data) / per_page)

    def get_embed(self):
        embed = discord.Embed(
            title=f"🏆 XP Leaderboard",
            description=f"Pagina {self.page + 1} van {self.max_pages}",
            color=discord.Color.gold()
        )
        start = self.page * self.per_page
        end = start + self.per_page

        for i, row in enumerate(self.data[start:end], start=start + 1):
            user = self.interaction.client.get_user(row["user_id"]) or f"<@{row['user_id']}>"
            level = calculate_level(row["xp"])
            embed.add_field(
                name=f"{i}. {user}",
                value=f"Level {level} – {row['xp']} XP",
                inline=False
            )
        return embed

    async def send_error(self, interaction, msg):
        await interaction.response.send_message(msg, ephemeral=True, delete_after=3)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def vorige(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await self.send_error(interaction, "⛔ Alleen jij mag bladeren.")
        if self.page == 0:
            return await self.send_error(interaction, "🚫 Eerste pagina.")
        self.page -= 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def volgende(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await self.send_error(interaction, "⛔ Alleen jij mag bladeren.")
        if self.page >= self.max_pages - 1:
            return await self.send_error(interaction, "🚫 Laatste pagina.")
        self.page += 1
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

class LevelCog(commands.Cog):
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
                if delta.total_seconds() < 5:
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

    @app_commands.command(name="level", description="Bekijk de level en xp van jezelf of een ander")
    @app_commands.describe(user="De gebruiker waarvan je level/xp wilt bekijken (optioneel)")
    async def xp_check(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        user_id = target.id
        today = datetime.date.today()

        async with self.db_pool.acquire() as conn:
            data = await conn.fetchrow("""
                SELECT xp, last_daily_claim FROM xp_users WHERE user_id = $1
            """, user_id)
            xp = data["xp"] if data else 0
            rank = await conn.fetchval("SELECT COUNT(*) FROM xp_users WHERE xp > $1", xp)
            total = await conn.fetchval("SELECT COUNT(*) FROM xp_users")

        last_daily = data["last_daily_claim"] if data else None
        level = calculate_level(xp)
        next_xp = xp_for_next_level(level)
        progress = f"{xp}/{next_xp} XP"
        daily_emoji = "✅" if last_daily == today else "❌"

        embed = discord.Embed(
            title=f"📈 XP Overzicht voor {target.display_name}",
            description=(
                f"**Level:** {level}\n"
                f"**XP:** {progress}\n"
                f"**Daily geclaimd:** {daily_emoji}\n"
                f"**🏆 Rank:** #{(rank or 0) + 1} van {total}"
            ),
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Bekijk het XP leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, xp FROM xp_users ORDER BY xp DESC LIMIT 100")

        if not rows:
            return await interaction.response.send_message("⚠️ Geen data beschikbaar.", ephemeral=True)

        view = LeaderboardView(interaction, rows)
        embed = view.get_embed()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="dailyxp", description="Claim je dagelijkse XP")
    async def claim_daily(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        today = datetime.date.today()

        async with self.db_pool.acquire() as conn:
            data = await conn.fetchrow("SELECT xp, last_daily_claim FROM xp_users WHERE user_id = $1", user_id)

            if data and data["last_daily_claim"] == today:
                return await interaction.response.send_message("⏳ Je hebt je daily al geclaimd vandaag!", ephemeral=True)

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

    @commands.command(name="givexp")
    @commands.has_permissions(administrator=True)
    async def givexp(self, ctx, user: discord.User, amount: int):
        async with self.db_pool.acquire() as conn:
            data = await conn.fetchrow("SELECT xp FROM xp_users WHERE user_id = $1", user.id)
            new_xp = (data["xp"] if data else 0) + amount

            if data:
                await conn.execute("UPDATE xp_users SET xp = $1 WHERE user_id = $2", new_xp, user.id)
            else:
                await conn.execute("INSERT INTO xp_users (user_id, xp) VALUES ($1, $2)", user.id, amount)

        await ctx.send(f"✅ {amount} XP toegekend aan {user.mention}.")

    @commands.command(name="resetxp")
    @commands.has_permissions(administrator=True)
    async def resetxp(self, ctx, user: discord.User):
        async with self.db_pool.acquire() as conn:
            await conn.execute("UPDATE xp_users SET xp = 0 WHERE user_id = $1", user.id)

        await ctx.send(f"🔄 XP van {user.mention} is gereset naar 0.")

    async def cog_load(self):
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS xp_users (
                    user_id BIGINT PRIMARY KEY,
                    xp INTEGER NOT NULL DEFAULT 0,
                    last_message_ts TIMESTAMP,
                    last_daily_claim DATE
                );
            """)

        self.bot.tree.add_command(self.xp_check, guild=GUILD_ID)
        self.bot.tree.add_command(self.claim_daily, guild=GUILD_ID)
        self.bot.tree.add_command(self.leaderboard, guild=GUILD_ID)
