from discord.ext import commands
import discord
import CivBot

class Starboard(commands.Cog, name="Starboard"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, message):
        pass

    @commands.command(name="starboard")
    async def starboard(self, ctx, *args):
        try:
            if args[0] == "create":
                if len(args) == 1:
                    await ctx.send("Usage: !starboard create [emoji])")
                guild = ctx.guild.id
                channel = ctx.channel.id
                reaction = args[1]
                try:
                    threshold = args[2]
                except IndexError:
                    threshold = 3
                CivBot.db.database.channels.insert_one({
                    'guild': guild,
                    'channel': channel,
                    'reaction': reaction,
                    'threshold': threshold
                })
                await ctx.send("Starboard created in this channel, with " + reaction +
                               " as reaction and threshold " + str(threshold))
                return
            elif args[0] == "modify":
                pass
            elif args[0] == "remove":
                pass
        except IndexError:
            ctx.send("Usage: !starboard [create/modify/remove] [args]")

def setup(bot):
    bot.add_cog(Starboard(bot))
