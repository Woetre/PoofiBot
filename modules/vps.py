#-- final --#

import discord
from discord.ext import commands
import psutil
import platform
import datetime

class VpsStatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vps")
    @commands.has_permissions(administrator=True)
    async def vps_status(self, ctx):
        """Geeft info over CPU, geheugen, uptime en schijfgebruik."""
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time

        embed = discord.Embed(
            title="📊 VPS Status",
            color=discord.Color.blurple()
        )
        embed.add_field(name="🖥️ CPU gebruik", value=f"{cpu_usage}%", inline=False)
        embed.add_field(name="🧠 Geheugen", value=f"{memory.used // (1024 ** 2)}MB / {memory.total // (1024 ** 2)}MB ({memory.percent}%)", inline=False)
        embed.add_field(name="💾 Schijf", value=f"{disk.used // (1024 ** 3)}GB / {disk.total // (1024 ** 3)}GB ({disk.percent}%)", inline=False)
        embed.add_field(name="⏱️ Uptime", value=str(uptime).split('.')[0], inline=False)
        embed.set_footer(text=platform.platform())

        await ctx.send(embed=embed)

    @vps_status.error
    async def vps_status_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Je hebt geen toestemming om dit commando te gebruiken.")
        else:
            await ctx.send(f"⚠️ Er ging iets mis: {str(error)}")
