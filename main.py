import discord
from discord.ext import commands
from discord import app_commands
import logging
import aiohttp
import asyncio
from dotenv import load_dotenv
import os
import json
import random

# ─────── Setup ───────
env_choice = os.getenv("ENV")  # via OS of hieronder instellen
if not env_choice:
    # fallback naar argument of standaard
    import sys
    env_choice = "production" if "--env=production" in sys.argv else "development"
    print(f"🚀 Bot gestart in '{env_choice}' modus.")

# Laad het juiste bestand
dotenv_file = os.path.join("config", f".env.{env_choice}")
load_dotenv(dotenv_file)

WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
AUTO_ROLE_ID = int(os.getenv("AUTO_ROLE_ID"))

ENV = os.getenv("ENV")
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = discord.Object(id=int(os.getenv("GUILD_ID")))

os.makedirs("data", exist_ok=True)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ─────── Backend ReactionRole Command ───────
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
        if self.role_message_id is None:
            return  # Geen ID opgeslagen, dus negeren

        if payload.message_id != self.role_message_id:
            return  # Geen foutmelding meer, gewoon negeren

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
            "\n<:livee:1384887113735995452> = Voor notificaties wanneer Marrit live gaat"
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
        # Welkombericht versturen
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if channel:
            await channel.send(
                f"👋 Welkom {member.mention} op de server! 🎉"
                f"\n• ✅ Haal je rollen op in #rollen."
                f"\n• 📺 Bekijk wanneer Marrit live is in #stream-meldingen"
                f"\n• 💬 Chat mee in #de-babbel-hoek of spring in een voicechannel."
                f"\n\nVeel plezier en wees lief voor elkaar! 💜"
            )

        # Automatisch rol geven
        role = member.guild.get_role(AUTO_ROLE_ID)
        if role:
            try:
                await member.add_roles(role, reason="Automatisch toegekende rol bij joinen.")
            except discord.Forbidden:
                print(f"❌ Bot mist permissies om rol toe te voegen aan {member}.")

# ─────── Purge Prefix Command ───────
class PurgeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", help="Verwijder een aantal berichten (alleen voor mods).")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, aantal: int):
        if aantal < 1 or aantal > 100:
            await ctx.send("❌ Geef een getal tussen 1 en 100 op.")
            return

        await ctx.channel.purge(limit=aantal + 1)  # +1 zodat het commando zelf ook verdwijnt
        bevestiging = await ctx.send(f"✅ {aantal} berichten verwijderd.")
        await bevestiging.delete(delay=5)  # Verwijder bevestiging na 5 seconden

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Je hebt geen permissie om berichten te verwijderen.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Gebruik: `!purge <aantal>` (bijv. `!purge 10`).")
        else:
            await ctx.send("⚠️ Er ging iets mis.")

# ─────── Help Slash Command ───────
class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Toont een overzicht van alle slash commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Beschikbare Commands",
            description="Hieronder zie je een lijst met alle slash commands die je kunt gebruiken:",
            color=discord.Color.blurple()
        )

        for cmd in self.bot.tree.get_commands(guild=interaction.guild):
            embed.add_field(
                name=f"/{cmd.name}",
                value=cmd.description or "Geen beschrijving",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cog_load(self):
        self.bot.tree.add_command(self.help_command, guild=GUILD_ID)

# ─────── Regels Slash Command + Regels Prefix Command ───────
class RegelsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="regels", description="Toon de serverregels.")
    async def regels_command(self, interaction: discord.Interaction):
        regels_tekst = (
            "**📜 Onze Serverregels**\n\n"
            "1️⃣ **Wees Respectvol** - Ga altijd met respect met elkaar om, dus geen haatdragende opmerkingen, pesten, racisme, seksisme of discriminatie van welke aard dan ook.\n"
            "2️⃣ **Geen zelfpromotie** - Maak geen reclame of ga niet jezelf promoten.\n"
            "3️⃣ **Houd het gezellig** -  Geen drama of negativiteit onnodig creëren.\n"
            "4️⃣ **Geen NSFW** - Denk hier bij aan naaktheid of andere expliciete dingen.\n"
            "5️⃣ **Geen Spam** - Spam niet heel de discord vol.\n"
            "6️⃣ **Luister naar staff leden** - Zij zijn er om de server goed te laten draaien.\n\n"
            
            "🩵 Door op de server te blijven ga je akkoord met deze regels.\n"
        )
        await interaction.response.send_message(regels_tekst, ephemeral=True)  # Alleen zichtbaar voor de gebruiker

    @commands.command(name="regels", help="Toont de serverregels.")
    @commands.has_permissions(administrator=True)
    async def regels_prefix(self, ctx):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # Bot heeft geen rechten om berichten te verwijderen

        regels_tekst = (
            "**📜 Onze Serverregels**\n\n"
            "1️⃣ **Wees Respectvol** - Ga altijd met respect met elkaar om, dus geen haatdragende opmerkingen, pesten, racisme, seksisme of discriminatie van welke aard dan ook.\n"
            "2️⃣ **Geen zelfpromotie** - Maak geen reclame of ga niet jezelf promoten.\n"
            "3️⃣ **Houd het gezellig** - Geen drama of negativiteit onnodig creëren.\n"
            "4️⃣ **Geen NSFW** - Denk hier bij aan naaktheid of andere expliciete dingen.\n"
            "5️⃣ **Geen Spam** - Spam niet heel de discord vol.\n"
            "6️⃣ **Luister naar staff leden** - Zij zijn er om de server goed te laten draaien.\n"
            "7️⃣ **/Regels** - Toont de serverregels.\n\n"
            "🩵 Door op de server te blijven ga je akkoord met deze regels.\n"
        )
        await ctx.send(regels_tekst)

    @regels_prefix.error
    async def regels_prefix_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Je hebt geen toestemming om dit commando te gebruiken.", delete_after=5)

    async def cog_load(self):
        self.bot.tree.add_command(self.regels_command, guild=GUILD_ID)

# ─────── Poll Slash Command ───────
class PollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="poll", description="Start een poll met maximaal 10 opties.")
    @app_commands.describe(
        vraag="De pollvraag die je wilt stellen",
        opties="Kiesopties gescheiden door komma’s (bijv: Ja,Nee,Misschien)"
    )
    async def poll_command(self, interaction: discord.Interaction, vraag: str, opties: str):
        emoji_cijfers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        opties_lijst = [opt.strip() for opt in opties.split(",") if opt.strip()]

        if not 2 <= len(opties_lijst) <= 10:
            await interaction.response.send_message("❌ Geef tussen de 2 en 10 opties op.", ephemeral=True)
            return

        await interaction.response.defer()

        beschrijving = ""
        for i, optie in enumerate(opties_lijst):
            beschrijving += f"{emoji_cijfers[i]} {optie}\n"

        embed = discord.Embed(
            title=f"📊 {vraag}",
            description=beschrijving,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Gemaakt door: {interaction.user.display_name}")

        bericht = await interaction.channel.send(embed=embed)
        for i in range(len(opties_lijst)):
            await bericht.add_reaction(emoji_cijfers[i])

        await interaction.followup.send("✅ Poll is geplaatst!", ephemeral=True)

    async def cog_load(self):
        # Verwijder eerst als het command al bestaat
        try:
            self.bot.tree.remove_command("poll", type=discord.AppCommandType.chat_input, guild=GUILD_ID)
        except Exception as e:
            print(f"⚠️ Kan oud poll commando niet verwijderen: {e}")

        # Voeg daarna veilig toe
        self.bot.tree.add_command(self.poll_command, guild=GUILD_ID)

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

# ─────── /marritquote Slash Command ───────
class MarritQuoteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quotes_file = os.path.join("data", f"quotes.{ENV}.json")

        self.quotes = self.load_quotes()

    def load_quotes(self):
        if os.path.exists(self.quotes_file):
            with open(self.quotes_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_quotes(self):
        with open(self.quotes_file, "w", encoding="utf-8") as f:
            json.dump(self.quotes, f, indent=4)

    @app_commands.command(name="marritquote", description="Toont een random quote van Marrit")
    async def marritquote(self, interaction: discord.Interaction):
        if not self.quotes:
            await interaction.response.send_message("😕 Er zijn nog geen quotes toegevoegd.")
            return
        quote = random.choice(self.quotes)
        await interaction.response.send_message(f"💬 _{quote}_")

    @commands.command(name="addquote", help="Voegt een quote toe aan de lijst (alleen admins)")
    @commands.has_permissions(administrator=True)
    async def addquote(self, ctx, *, quote: str = None):
        if not quote or not quote.strip():
            await ctx.send("❌ Je moet wel een quote opgeven. Voorbeeld: `!addquote Dit is een legendarische uitspraak.`")
            return

        self.quotes.append(quote.strip())
        self.save_quotes()
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
        if not self.quotes:
            await ctx.send("📭 Er zijn geen quotes om te verwijderen.")
            return

        beschrijving = ""
        for i, q in enumerate(self.quotes, start=1):
            beschrijving += f"{i}. {q}\n"

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
            if 1 <= keuze <= len(self.quotes):
                verwijderde = self.quotes.pop(keuze - 1)
                self.save_quotes()
                await ctx.send(f"✅ Quote verwijderd:\n`{verwijderde}`")
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
        self.bot.tree.add_command(self.marritquote, guild=GUILD_ID)

# ─────── /Coinflip Slash Command ───────
class CoinflipCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="coinflip", description="Gooi een munt op: kop of munt?")
    async def coinflip(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Zeg alvast dat we bezig zijn

        # Verstuur tijdelijk bericht met animatie-effect
        bericht = await interaction.followup.send("🪙 Gooit de munt...")

        await asyncio.sleep(2)  # Wacht even voor het 'animatie' effect

        resultaat = random.choice(["Kop 🪙", "Munt 🪙"])
        await bericht.edit(content=f"🪙 De munt landt op: **{resultaat}**")

    async def cog_load(self):
        self.bot.tree.add_command(self.coinflip, guild=GUILD_ID)

class DobbelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dobbel", description="Gooi een dobbelsteen (1 t/m 6)")
    async def dobbel(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Geef aan dat het even duurt

        # Laat eerst een 'animatie' zien
        bericht = await interaction.followup.send("🎲 Gooi de dobbelsteen...")

        await asyncio.sleep(2)  # Simuleer een korte wachttijd

        uitkomst = random.randint(1, 6)
        dobbel_emoji = {
            1: "🎲 ➀",
            2: "🎲 ➁",
            3: "🎲 ➂",
            4: "🎲 ➃",
            5: "🎲 ➄",
            6: "🎲 ➅"
        }

        await bericht.edit(content=f"{dobbel_emoji[uitkomst]} **{interaction.user.display_name}** gooide een **{uitkomst}**!")

    async def cog_load(self):
        self.bot.tree.add_command(self.dobbel, guild=GUILD_ID)

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

        # ───── Adding Prefix Commands ─────
        await self.bot.add_cog(PurgeCog(self.bot))

        # ───── Adding Slash Commands ─────
        await self.bot.add_cog(HelpCog(self.bot))
        await self.bot.add_cog(RegelsCog(self.bot))
        await self.bot.add_cog(PollCog(self.bot))
        await self.bot.add_cog(AnimeCog(self.bot))
        await self.bot.add_cog(MarritQuoteCog(self.bot))
        await self.bot.add_cog(CoinflipCog(self.bot))
        await self.bot.add_cog(DobbelCog(self.bot))

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
bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
