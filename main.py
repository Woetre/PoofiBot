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

# ─────── Backend ReactionRole Command ───────
class ReactionRoleManager:
    def __init__(self, bot):
        self.bot = bot
        self.role_message_id = None
        self.config_file = CONFIG_FILE
        self.emoji_to_role = {
            discord.PartialEmoji(name='minecraft', id=1384211982634451005): 1382403336837267577,
            discord.PartialEmoji(name='valorant', id=1384211801260163112): 1382401490462838839,
        }
        self.load_config()
        bot.add_listener(self.on_raw_reaction_add)
        bot.add_listener(self.on_raw_reaction_remove)

    def set_message_id(self, msg_id):
        self.role_message_id = msg_id
        self.save_config()

    def save_config(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump({"role_message_id": self.role_message_id}, f)
            print(f"✅ Config opgeslagen met message ID: {self.role_message_id}")
        except Exception as e:
            print(f"❌ Fout bij opslaan config: {e}")

    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.role_message_id = data.get("role_message_id")
                    print(f"📂 Config geladen: {self.role_message_id}")
        except Exception as e:
            print(f"❌ Fout bij laden config: {e}")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.message_id != self.role_message_id:
            if self.role_message_id:
                print(f"⚠️ Geen match met opgeslagen message_id ({self.role_message_id}). Misschien verwijderd?")
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


# ─────── Frontend ReactionRole Command ───────
class ReactionRoleCog(commands.Cog):
    def __init__(self, client, rr_manager):
        self.bot = client
        self.rr_manager = rr_manager

    @commands.command(name="setup_reactierollen", help="Stelt een reactie-rollen bericht in.")
    @commands.has_permissions(administrator=True)
    async def setup_reactierollen(self, ctx):
        message = await ctx.send(
            "📌 Reageer met een emoji om een rol te krijgen:"
            "\n"
            "\n<:valorant:1384211801260163112> = Voor alles wat betreft valorant"
            "\n<:minecraft:1384211982634451005> = Voor alles wat betreft minecraft"
        )
        for emoji in self.rr_manager.emoji_to_role:
            await message.add_reaction(emoji)

        self.rr_manager.set_message_id(message.id)
        await ctx.send("✅ Reactierollen bericht is ingesteld!", delete_after=15)

# ─────── Welkomstbericht Class ───────
class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            await channel.send(
                f"👋 Welkom {member.mention} op de server! 🎉"
                f"\n"             
                f"• ✅ Haal je rollen op in #rollen.\n"
                f"• 📺 Bekijk wanneer Marrit live is in #live-aankondigingen.\n"
                f"• 💬 Chat mee in #algemeen of spring in een voicechannel.\n\n"
                f"Veel plezier en wees lief voor elkaar! 💜"
            )


# ─────── Anime Slash Command ───────
class AnimeCog(commands.Cog):
    def __init__(self, client):
        self.bot = client

    @app_commands.command(name="anime", description="Toon een willekeurige anime GIF")
    async def animegif_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nekosapi.com/v4/images/random?type=gif&category=safe") as response:
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

        #───── Adding reactionrole ─────
        rr_manager = ReactionRoleManager(self.bot)
        rr_cog = ReactionRoleCog(self.bot, rr_manager)
        await self.bot.add_cog(rr_cog)
        await rr_cog.cog_load()

        # ───── Adding welcomemessage ─────
        await self.bot.add_cog(WelcomeCog(self.bot))

        # ───── Adding Commands ─────
        await self.bot.add_cog(AnimeCog(self.bot))

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
