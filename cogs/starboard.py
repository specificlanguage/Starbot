from discord.ext import commands
import CivBot

database = CivBot.db.database

# TODO: generally figure out custom emoji and how to treat them

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
    async def starboard(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Incorrect subcommand! Try !help starboard for more info.")

    # create() = is a subcommand for starboard settings.
    # creates a new channel
    @starboard.command(help="Creates a new starboard.\nRequires a name, reaction, and threshold amt.")
    async def create(self, ctx, name: str, reaction: str, threshold: int):
        guild = ctx.guild.id
        channel = ctx.channel.id
        threshold = threshold
        new_channel = {'name': name, 'guild': guild, 'channel': channel,
                       'reaction': reaction, 'threshold': threshold, 'anti_star': ""}
        if database.channels.count_documents({"guild": guild}) >= 2:
            await ctx.send("Reached limit (2) of starboards! Can't create another one!")
            return
        elif database.channels.count_documents({"guild": guild, "reaction": reaction}) >= 1:
            await ctx.send("You're already using that reaction in this discord.")
            return
        elif database.channels.count_documents({"channel": channel}) >= 1: # we could delete this tbh
            await ctx.send("This channel is already being used for a starboard. Try another channel.")
            return
        elif database.channels.count_documents({"guild": guild, "name": name}) >= 1:
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
        valid_options = ["threshold", "antistar"]
        if database.channels.count_documents(search) == 0:
            await ctx.send("You don't have a starboard with this name.")
            return
        if option not in valid_options:
            await ctx.send("Not a valid option! Valid options: " + str(valid_options))
            return
        elif value == "" or value is None:
            await ctx.send("Incorrect values! Threshold requires a number, antistar requires a reaction.")
            return
        elif option == 'antistar' and (database.channels.count_documents({"guild": ctx.guild.id, "reaction": value})
                or database.channels.count_documents({"guild": ctx.guild.id, "antistar": value})):
            await ctx.send("You're already using that emoji in this discord!")
            return
        elif option == 'threshold' and int(value) <= 0:
            await ctx.send("You can't set a threshold that's equal to or less than 0.")
            return
        if value == "clear":
            value_to_assign = ""
            clear_antistars()
            await ctx.send("Starboard " + name + "'s antistars cleared.")
        elif option == "threshold":
            value_to_assign = int(value)
            await ctx.send("Starboard " + name + "'s threshold settings set to " + value + ".")
        else:
            value_to_assign = value
            await ctx.send("Starboard " + name + "'s anti-star reaction set to " + value + ".")
        database.channels.find_and_modify(query=search, update={"$set":{option: value_to_assign}}, upsert=False)

def clear_antistars():
    pass
    # TODO, probably not too hard, because it really just means disregard the anti-star entries

def setup(bot):
    bot.add_cog(Starboard(bot))
