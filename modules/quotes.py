#-- final --#

import discord
from discord.ext import commands
from discord import app_commands
import asyncpg
import asyncio
import random
import os

GUILD_ID = discord.Object(id=int(os.getenv("GUILD_ID")))

class MarritQuoteCog(commands.Cog):
    def __init__(self, bot, db_pool):
        self.bot = bot
        self.pool = db_pool

    async def setup_db(self):
        print("🔗 Verbonden met database (quotes).")
        async with self.pool.acquire() as conn:
            await conn.execute("""
                               CREATE TABLE IF NOT EXISTS quotes
                               (
                                   id      SERIAL PRIMARY KEY,
                                   content TEXT NOT NULL
                               );
                               """)

    @app_commands.command(name="marritquote", description="Toont een random quote van Marrit")
    async def marritquote(self, interaction: discord.Interaction):
        async with self.pool.acquire() as conn:
            result = await conn.fetch("SELECT content FROM quotes")
            if not result:
                await interaction.response.send_message("😕 Er zijn nog geen quotes toegevoegd.")
                return
            quote = random.choice(result)["content"]
            await interaction.response.send_message(f"💬 _{quote}_")

    @commands.command(name="addquote", help="Voegt een quote toe aan de lijst (alleen admins)")
    @commands.has_permissions(administrator=True)
    async def addquote(self, ctx, *, quote: str = None):
        if not quote or not quote.strip():
            await ctx.send("❌ Je moet wel een quote opgeven. Voorbeeld: `!addquote Dit is een legendarische uitspraak.`")
            return

        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO quotes (content) VALUES ($1)", quote.strip())

        await ctx.send("✅ Quote toegevoegd.")

    @addquote.error
    async def addquote_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Je hebt geen toestemming om dit commando te gebruiken.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Gebruik: `!addquote <quote>`")
        else:
            await ctx.send(f"⚠️ Er is iets fout gegaan: `{str(error)}`")

    @commands.command(name="removequote", help="Verwijder een quote op nummer (alleen admins)")
    @commands.has_permissions(administrator=True)
    async def removequote(self, ctx):
        async with self.pool.acquire() as conn:
            results = await conn.fetch("SELECT id, content FROM quotes ORDER BY id ASC")

            if not results:
                await ctx.send("📭 Er zijn geen quotes om te verwijderen.")
                return

            beschrijving = ""
            for i, row in enumerate(results, start=1):
                beschrijving += f"{i}. {row['content']}\n"

            embed = discord.Embed(
                title="🗑️ Quotes verwijderen",
                description=beschrijving,
                color=discord.Color.red()
            )
            embed.set_footer(text="Typ het nummer van de quote die je wilt verwijderen.")

            await ctx.send(embed=embed)

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

            try:
                antwoord = await self.bot.wait_for("message", check=check, timeout=30)
                keuze = int(antwoord.content)
                if 1 <= keuze <= len(results):
                    quote_id = results[keuze - 1]["id"]
                    await conn.execute("DELETE FROM quotes WHERE id = $1", quote_id)
                    await ctx.send(f"✅ Quote verwijderd:\n`{results[keuze - 1]['content']}`")
                else:
                    await ctx.send("❌ Ongeldig nummer.")
            except asyncio.TimeoutError:
                await ctx.send("⌛ Tijd verstreken. Probeer het opnieuw.")

    @removequote.error
    async def removequote_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Je hebt geen toestemming om dit commando te gebruiken.")
        else:
            await ctx.send("⚠️ Er ging iets fout.")

    async def cog_load(self):
        await self.setup_db()
        self.bot.tree.add_command(self.marritquote, guild=GUILD_ID)
