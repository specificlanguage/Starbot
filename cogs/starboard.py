from discord.ext import commands
import CivBot

# TODO: generally figure out custom emoji and how to treat them

class Starboard(commands.Cog, name="Starboard"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        emoji = str(payload.emoji)
        user = payload.member
        if user == message.author:
            return # reactions made by users do not count.

        valid_reactions = list(self.bot.db.channels.find({"guild": channel.guild.id, "or":
            {"reaction": emoji, "antistar": emoji}}))

        if len(valid_reactions) == 0:
            return  # no need to do anything here.
        board_name = valid_reactions[0]["name"]
        if valid_reactions[0]["reaction"] == emoji:
            antistar = False
        elif valid_reactions[0]["antistar"] == emoji:
            antistar = True
        coll = self.bot.db[board_name]
        coll.insert_one({
            "reactor": user.name,
            "message": message.id,
            "message_author": message.author,
            "reaction": emoji,
            "antistar": False
        })

        update_starboard(message)

    # TODO: literally the opposite

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
        if self.bot.db.channels.count_documents({"guild": guild}) >= 2:
            await ctx.send("Reached limit (2) of starboards! Can't create another one!")
            return
        elif self.bot.db.channels.count_documents({"guild": guild, "reaction": reaction}) >= 1:
            await ctx.send("You're already using that reaction in this discord.")
            return
        elif self.bot.db.channels.count_documents({"channel": channel}) >= 1: # we could delete this tbh
            await ctx.send("This channel is already being used for a starboard. Try another channel.")
            return
        elif self.bot.db.channels.count_documents({"guild": guild, "name": name}) >= 1:
            await ctx.send("You've already made a starboard with that name.")
            return
        self.bot.db.create_collection(name)
        self.bot.db.channels.insert_one(new_channel)
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
        if self.bot.db.channels.count_documents(search) == 0:
            await ctx.send("You don't have a starboard with this name.")
            return
        if option not in valid_options:
            await ctx.send("Not a valid option! Valid options: " + str(valid_options))
            return
        elif value == "" or value is None:
            await ctx.send("Incorrect values! Threshold requires a number, antistar requires a reaction.")
            return
        elif option == 'antistar' and (self.bot.db.channels.count_documents({"guild": ctx.guild.id, "reaction": value})
                or self.bot.db.channels.count_documents({"guild": ctx.guild.id, "antistar": value})):
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
        self.bot.db.channels.find_and_modify(query=search, update={"$set":{option: value_to_assign}}, upsert=False)

def add_star(channel_entry, message, antistar):
    pass
    # Antistar must be passed as a boolean

def recount_reactions(reaction):
    pass

def clear_antistars():
    pass
    # TODO, probably not too hard, because it really just means dump the anti-star entries

def update_starboard(message_id):
    # TODO, check how many positive reactions and negative reactions, and then go to starboard
    pass

def setup(bot):
    bot.add_cog(Starboard(bot))
