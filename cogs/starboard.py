from discord.ext import commands
import CivBot

class Starboard(commands.Cog, name="Starboard"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, message):
        return

    @commands.command(name="starboard", help="Manages starboards:\n" +
            "!starboard create [name] [reaction] {threshold}\n" +
            "!starboard modify [name] [threshold] [value]\n" +
            "!starboard remove [name]",
        brief="Manages starboards")
    async def starboard(self, ctx, *args):
        # create subcommand
        if len(args) >= 3 and args[0] == 'create':
            guild = ctx.guild.id
            channel = ctx.channel.id
            name = args[1]
            reaction = args[2]
            try:
                threshold = args[3]
            except IndexError:
                threshold = 3
            # TODO: check for duplicates
            CivBot.db.database.channels.insert_one({
                'name': name,
                'guild': guild,
                'channel': channel,
                'reaction': reaction,
                'threshold': threshold
            })
            await ctx.send("Starboard '" + name + "' created in this channel, with " + reaction +
                           " as reaction and threshold " + str(threshold))
            return
        # modify subcommand
        elif len(args) >= 4 and args[0] == 'modify':
            # modify an entry
            return
        else:
            await ctx.send()

def setup(bot):
    bot.add_cog(Starboard(bot))
