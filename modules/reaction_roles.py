import discord
from discord.ext import commands
import os
import json

ENV = os.getenv("ENV")

class ReactionRoleManager:
    def __init__(self, bot):
        self.bot = bot
        self.role_message_id = None
        self.config_file = os.path.join("data", f"reaction_config.{ENV}.json")
        self.emoji_to_role = self.load_emoji_config()
        self.load_config()
        bot.add_listener(self.on_raw_reaction_add)
        bot.add_listener(self.on_raw_reaction_remove)

    def load_emoji_config(self):
        emoji_config_file = os.path.join("config", f"emojis.{ENV}.json")
        emoji_to_role = {}
        try:
            with open(emoji_config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for name, info in data.items():
                    emoji = discord.PartialEmoji(name=name, id=info["id"])
                    emoji_to_role[emoji] = info["role_id"]
            print("🎭 Emoji-config geladen.")
        except Exception as e:
            print(f"⚠️ Kon emoji config niet laden: {e}")
        return emoji_to_role

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
        if self.role_message_id is None or payload.message_id != self.role_message_id:
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


class ReactionRoleCog(commands.Cog):
    def __init__(self, bot, rr_manager):
        self.bot = bot
        self.rr_manager = rr_manager

    @commands.command(name="setup_reactierollen", help="Stelt een reactie-rollen bericht in.")
    @commands.has_permissions(administrator=True)
    async def setup_reactierollen(self, ctx):
        message = await ctx.send(
            "📌 Reageer met een emoji om een rol te krijgen:"
            "\n"
            "\n<:livee:1384887113735995452> = Voor notificaties wanneer Marrit live gaat"
            "\n<:valorant:1384211801260163112> = Voor alles wat betreft valorant"
            "\n<:minecraft:1384211982634451005> = Voor alles wat betreft minecraft"
        )
        for emoji in self.rr_manager.emoji_to_role:
            await message.add_reaction(emoji)

        self.rr_manager.set_message_id(message.id)
        await ctx.send("✅ Reactierollen bericht is ingesteld!", delete_after=15)
