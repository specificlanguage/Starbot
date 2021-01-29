from discord.ext import commands
import CivBot

database = CivBot.db.database

class Starboard(commands.Cog, name="Starboard"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, message):
        return

    # top command for starboard settings command.
    @commands.group(name="starboard", help="Manages starboards:\n" +
            "!starboard create [name] [reaction] {threshold}\n" +
            "!starboard modify [name] [threshold] [value]\n" +
            "!starboard remove [name]",
        brief="Manages starboards")
    async def starboard(self, ctx, *args):
        if ctx.invoked_summond is None:
            await ctx.send("Incorrect subcommand! Try !help starboard for more info.")

    # create() = is a subcommand for starboard settings.
    # creates a new channel
    @starboard.command(help="Creates a new starboard.\nRequires a name, reaction, and threshold amt.")
    async def create(self, ctx, name: str, reaction: str, args):
        guild = ctx.guild.id
        channel = ctx.channel.id
        try:
            threshold = args[0]
        except IndexError:
            threshold = 3
        new_channel = {'name': name, 'guild': guild, 'channel': channel,
                       'reaction': reaction, 'threshold': threshold, 'anti_star': ""}
        results = database.channels.find({"guild": guild})
        if results.count_documents() >= 2:
            await ctx.send("Reached limit (2) of starboards! Can't create another one!")
            return
        elif database.channels.find({"guild": guild, "reaction": reaction}).count_documents >= 1:
            await ctx.send("You're already using that reaction in this discord.")
            return
        elif database.channels.find({"channel": channel}).count_documents >= 1:
            await ctx.send("This channel is already being used for a starboard. Try something else.")
            return
        elif database.channels.find({"guild": guild, "name": name}).count_documents >= 1:
            await ctx.send("You've already made a starboard with that name.")
            return
        database.create_collection(name)
        database.channels.insert_one(new_channel)
        await ctx.send("Starboard '" + name + "' created in this channel, with " + reaction +
                       " as reaction and threshold " + str(threshold))

    # modify - Subcommand for starboards to modify settings
    # Modifies properties for settings already here.
    @starboard.command(help="Modifies threshold and anti-star feature.\n"
                            "Setting threshold: `!starboard modify threshold [threshold]`\n"
                            "Setting anti-star: `!starboard modify antistar [emoji]`"
                            " or `!starboard modify antistar clear` to clear")
    async def modify(self, ctx, name: str, option: str, value: str):
        search = {"guild": ctx.guild.id, "name": name}
        results = database.channels.find(search)
        if results.count_documents == 0:
            await ctx.send("You don't have a starboard with this name.")
            return
        valid_options = ["threshold", "antistar"]
        if option not in valid_options:
            await ctx.send("Not a valid option! Valid options: " + str(valid_options))
            return
        elif value == "" or value is None:
            await ctx.send("Incorrect values! Threshold requires a number, antistar requires a reaction.")
            return
        else:
            database.channels.find_and_modify(query=search, update={"$set":{option, value}}, upsert=False)
            await ctx.send("Starboard " + name + " updated.")sub

def setup(bot):
    bot.add_cog(Starboard(bot))
