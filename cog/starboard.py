from discord.ext import commands
import CivBot

class Starboard(commands.Cog, name="Starboard"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, message):
        pass

    @commands.command(name="starboard")
    async def starboard(self, ctx, *args):
        if args[0] is "create":
            guild = ctx.guild
            channel = ctx.channel
            emoji = args[1]
            try:
                threshold = args[2]
            except IndexError:
                threshold = 3
            # add database
            ctx.send("Starboard created in this channel.")
            return

