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
CONFIG_FILE = "reaction_config.json"

bot = commands.Bot(command_prefix='!', intents=intents)

# ─────── Backend Reaction Role Command ───────
class ReactionRoleManager:
    def __init__(self, bot):
        self.bot = bot
        self.role_message_id = None
        self.config_file = CONFIG_FILE
        self.emoji_to_role = {
            discord.PartialEmoji(name='🔴'): 1382401490462838839,  # Vul echte rol-ID’s in
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
        if not role or not payload.member:
            return
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

# ─────── Setup Reaction Role Command ───────
class SetupCog(commands.Cog):
    def __init__(self, bot, rr_manager: ReactionRoleManager):
        self.bot = bot
        self.rr_manager = rr_manager

    @app_commands.command(name="setup_reactierollen", description="Stelt een reactie-rollen bericht in.")
    async def setup_reactierollen(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        message = await interaction.channel.send(
            "📌 Reageer met een emoji om een rol te krijgen:\n🔴 = Rood\n🟡 = Geel"
        )

        for emoji in self.rr_manager.emoji_to_role.keys():
            await message.add_reaction(emoji)

        self.rr_manager.set_message_id(message.id)
        await interaction.followup.send("✅ Reactierollen bericht ingesteld!", ephemeral=True)

    async def cog_load(self):
        self.bot.tree.add_command(self.setup_reactierollen, guild=GUILD_ID)

# ─────── Anime Command ───────
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

# ─────── on_ready ───────
@bot.event
async def on_ready():
    print(f'✅ Ingelogd als {bot.user} (ID: {bot.user.id})')

    try:
        rr_manager = ReactionRoleManager(bot)
        await bot.add_cog(AnimeCog(bot))
        await bot.add_cog(SetupCog(bot, rr_manager))
        await bot.tree.sync(guild=GUILD_ID)
        print(f"📡 Slash commands gesynchroniseerd.")
    except Exception as e:
        print(f"❌ Fout bij sync: {e}")

# ─────── Start Bot ───────
bot.run(token, log_handler=handler, log_level=logging.DEBUG)