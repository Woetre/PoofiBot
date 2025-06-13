import discord
from discord.ext import commands
from discord import app_commands
import logging
import aiohttp
from dotenv import load_dotenv
import os
import json

# ─────── Setup ───────
load_dotenv()
token = os.getenv("DISCORD_TOKEN")
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

GUILD_ID = discord.Object(id=1198629275687981146)
WELCOME_CHANNEL_ID = 1382064446285025320  # ← vervang dit door jouw kanaal-ID

CONFIG_FILE = "reaction_config.json"

bot = commands.Bot(command_prefix='!', intents=intents)

# ─────── Reaction Role Manager ───────
class ReactionRoleManager:
    def __init__(self, bot):
        self.bot = bot
        self.role_message_id = None
        self.config_file = CONFIG_FILE
        self.emoji_to_role = {
            discord.PartialEmoji(name='🔴'): 1382401490462838839,
            discord.PartialEmoji(name='🟡'): 1382403336837267577,
        }
        self.load_config()
        bot.add_listener(self.on_raw_reaction_add)
        bot.add_listener(self.on_raw_reaction_remove)

    def set_message_id(self, msg_id):
        self.role_message_id = msg_id
        self.save_config()

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump({"role_message_id": self.role_message_id}, f)

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                data = json.load(f)
                self.role_message_id = data.get("role_message_id")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.role_message_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role_id = self.emoji_to_role.get(payload.emoji)
        if not role_id:
            return
        role = guild.get_role(role_id)
        if role and payload.member:
            await payload.member.add_roles(role)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.role_message_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role_id = self.emoji_to_role.get(payload.emoji)
        if not role_id:
            return
        role = guild.get_role(role_id)
        if not role:
            return
        member = guild.get_member(payload.user_id)
        if member:
            await member.remove_roles(role)

# ─────── Welkomstbericht Class ───────
class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            await channel.send(f"👋 Welkom {member.mention} op de server! 🎉")

# ─────── Setup Slash Command ───────
class SetupCog(commands.Cog):
    def __init__(self, bot, rr_manager):
        self.bot = bot
        self.rr_manager = rr_manager

    @app_commands.command(name="setup_reactierollen", description="Stelt een reactie-rollen bericht in.")
    async def setup_reactierollen(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send("🚫 Alleen beheerders kunnen dit commando gebruiken.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        message = await interaction.channel.send(
            "📌 Reageer met een emoji om een rol te krijgen:\n🔴 = Rood\n🟡 = Geel"
        )
        for emoji in self.rr_manager.emoji_to_role:
            await message.add_reaction(emoji)

        self.rr_manager.set_message_id(message.id)
        await interaction.followup.send("✅ Reactierollen bericht is ingesteld!", ephemeral=True)

    async def cog_load(self):
        self.bot.tree.add_command(self.setup_reactierollen, guild=GUILD_ID)

# ─────── Anime Slash Command ───────
class AnimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="anime", description="Toon een willekeurige anime GIF")
    async def animegif_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nekosapi.com/v4/images/random?type=gif") as response:
                if response.status == 200:
                    data = await response.json()
                    gif_url = data[0]["url"]
                    await interaction.followup.send(gif_url)
                else:
                    await interaction.followup.send("Kon geen anime gif ophalen 😢")

    async def cog_load(self):
        self.bot.tree.add_command(self.animegif_command, guild=GUILD_ID)

# ─────── Core Functionaliteit ───────
class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # Starttaken zoals slash commands en cogs laden
        rr_manager = ReactionRoleManager(self.bot)
        await self.bot.add_cog(WelcomeCog(self.bot))
        await self.bot.add_cog(AnimeCog(self.bot))
        await self.bot.add_cog(SetupCog(self.bot, rr_manager))
        await self.bot.tree.sync(guild=GUILD_ID)
        print("📡 Slash commands gesynchroniseerd.")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="twitch.tv/LiveMetMarrit")
        )
        print(f'✅ Ingelogd als {self.bot.user} (ID: {self.bot.user.id})')

# ─────── Run Bot ───────
@bot.event
async def setup_hook():
    await bot.add_cog(Core(bot))
bot.run(token, log_handler=handler, log_level=logging.DEBUG)
