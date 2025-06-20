#-- final --#

import discord
from discord.ext import commands
import asyncpg

class ReactionRoleCog(commands.Cog):
    def __init__(self, bot, db_pool):
        self.bot = bot
        self.pool = db_pool
        self.role_message_ids = {}  # guild_id: message_id

        # Emoji's gekoppeld aan rol-ID’s per guild/server
        self.config = {
            1359579900868038806: {  # Live server ID
                discord.PartialEmoji(name="live", id=1384887057280929933): 1384469398651146271,
                discord.PartialEmoji(name="valorant", id=1384836401450975242): 1384234778127106168,
                discord.PartialEmoji(name="minecraft", id=1384836426599759902): 1384234855155368058
            },
            1198629275687981146: {  # Test server ID
                discord.PartialEmoji(name="livee", id=1384887113735995452): 1384887712502255636,
                discord.PartialEmoji(name="valorante", id=1384211801260163112): 1382401490462838839,
                discord.PartialEmoji(name="minecrafte", id=1384211982634451005): 1382403336837267577
            }
        }

    async def cog_load(self):
        await self.load_configs()
        self.bot.add_listener(self.on_raw_reaction_add)
        self.bot.add_listener(self.on_raw_reaction_remove)

    async def load_configs(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT guild_id, message_id FROM reaction_roles_config")
            self.role_message_ids = {row["guild_id"]: row["message_id"] for row in rows}
            print("📥 Reactie-rol bericht IDs geladen uit database.")

    async def save_config(self, guild_id: int, message_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO reaction_roles_config (guild_id, message_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id) DO UPDATE SET message_id = EXCLUDED.message_id
            """, guild_id, message_id)
            self.role_message_ids[guild_id] = message_id
            print(f"💾 Message ID opgeslagen voor guild {guild_id}: {message_id}")

    @commands.command(name="setup_reactierollen", help="Plaats een bericht voor reactierollen")
    @commands.has_permissions(administrator=True)
    async def setup_reactierollen(self, ctx):
        guild_id = ctx.guild.id
        if guild_id not in self.config:
            await ctx.send("⚠️ Deze server heeft geen ingestelde configuratie.")
            return

        beschrijving = "📌 Reageer met een emoji om een rol te krijgen:\n\n"
        emoji_to_description = {
            "live": "Voor notificaties wanneer Marrit live gaat",
            "livee": "Voor notificaties wanneer Marrit live gaat",
            "valorant": "Voor alles wat betreft valorant",
            "valorante": "Voor alles wat betreft valorant",
            "minecraft": "Voor alles wat betreft minecraft",
            "minecrafte": "Voor alles wat betreft minecraft"
        }

        for emoji in self.config[guild_id]:
            name = emoji.name
            desc = emoji_to_description.get(name, "Geen beschrijving")
            beschrijving += f"{emoji} - {desc}\n"

        # Verzend bericht en voeg emoji's toe
        bericht = await ctx.send(beschrijving)
        for emoji in self.config[guild_id]:
            await bericht.add_reaction(emoji)

        # Opslaan in database
        await self.save_config(guild_id, bericht.id)

        # Verwijder admin command message
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("⚠️ Kan het commando bericht niet verwijderen.", delete_after=5)

        bevestiging = await ctx.send("✅ Reactierollen bericht geplaatst en opgeslagen!", delete_after=5)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id not in self.role_message_ids:
            return
        if payload.message_id != self.role_message_ids[payload.guild_id]:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        role_id = self.config.get(payload.guild_id, {}).get(payload.emoji)
        if not role_id:
            return

        role = guild.get_role(role_id)
        member = payload.member
        if role and member:
            await member.add_roles(role)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id not in self.role_message_ids:
            return
        if payload.message_id != self.role_message_ids[payload.guild_id]:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        role_id = self.config.get(payload.guild_id, {}).get(payload.emoji)
        if not role_id:
            return

        role = guild.get_role(role_id)
        member = guild.get_member(payload.user_id)
        if role and member:
            await member.remove_roles(role)
