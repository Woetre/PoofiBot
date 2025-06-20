import discord
from discord.ext import commands
from bot_config import GUILD_ID

from modules.help import HelpCog
from modules.regels import RegelsCog
from modules.poll import PollCog
from modules.coinflip import CoinflipCog
from modules.dobbel import DobbelCog
from modules.purge import PurgeCog
from modules.welcome import WelcomeCog
from modules.quotes import MarritQuoteCog
from modules.reaction_roles import ReactionRoleCog
from modules.userinfo import UserInfoCog

class Core(commands.Cog):
    def __init__(self, bot, db_pool):
        self.bot = bot
        self.db_pool = db_pool

    async def cog_load(self):
        # ───── Reaction Roles ─────
        rr_cog = ReactionRoleCog(self.bot, self.db_pool)
        await self.bot.add_cog(rr_cog)
        await rr_cog.cog_load()

        # ───── Losse cogs ─────
        await self.bot.add_cog(WelcomeCog(self.bot))
        await self.bot.add_cog(PurgeCog(self.bot))
        await self.bot.add_cog(HelpCog(self.bot))
        await self.bot.add_cog(RegelsCog(self.bot))
        await self.bot.add_cog(PollCog(self.bot))
        await self.bot.add_cog(CoinflipCog(self.bot))
        await self.bot.add_cog(DobbelCog(self.bot))
        await self.bot.add_cog(MarritQuoteCog(self.bot, self.db_pool))
        await self.bot.add_cog(UserInfoCog(self.bot))
        print("✅ Alle modules zijn geladen.")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="twitch.tv/LiveMetMarrit")
        )
        print(f'👾 Ingelogd als {self.bot.user} (ID: {self.bot.user.id})')

