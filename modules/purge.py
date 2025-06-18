import discord
from discord.ext import commands

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
        await bevestiging.delete(delay=5)

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 Je hebt geen permissie om berichten te verwijderen.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Gebruik: `!purge <aantal>` (bijv. `!purge 10`).")
        else:
            await ctx.send("⚠️ Er ging iets mis.")
