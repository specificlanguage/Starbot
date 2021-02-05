from discord.ext import commands
import helpers


class Starboard(commands.Cog, name="Starboard"):
    def __init__(self, bot):
        self.bot = bot

    """on_raw_reaction_add: updates starboard and database when reaction is set."""

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        results = await helpers.validate_reaction(self.bot, payload)
        if results is None:
            return  # no need to update db
        board_name, query = results[0], results[1]
        coll = self.bot.db[board_name]
        coll.insert_one(query)
        message = await self.bot.get_channel(payload.channel_id).fetch_message(query["message"])
        await self.update_starboard(message, board_name)

    """on_raw_reaction_remove: updates starboard and database when reaction removed."""

    # TODO: literally the opposite
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        results = await helpers.validate_reaction(self.bot, payload)
        if results is None:
            return  # no need to update db
        board_name, query = results[0], results[1]
        coll = self.bot.db[board_name]
        coll.delete_one(query)
        message = await self.bot.get_channel(payload.channel_id).fetch_message(query["message"])
        await self.update_starboard(message, board_name)

    # top command for starboard settings command.
    @commands.group(name="starboard", help="Creates, manages, and removes starboards." 
                                           "!starboard remove [board name]",
                    brief="Manages starboards")
    async def starboard(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Incorrect subcommand! Try !help starboard for more info.")

    """ create -
        When command is run, given name, reaction, and threshold,
        creates a new starboard in the channel that the command is run.
    """

    # create() = is a subcommand for starboard settings.
    # creates a new channel
    @starboard.command(help="!starboard create [board name] [reaction] {threshold}\n")
    async def create(self, ctx, name: str, reaction: str, threshold: int):
        guild = ctx.guild.id
        channel = ctx.channel.id
        threshold = threshold
        new_channel = {'name': helpers.get_board_name(guild, name), 'guild': guild, 'channel': channel,
                       'reaction': reaction, 'threshold': threshold, 'antistar': ""}
        if self.bot.db.channels.count_documents({"guild": guild}) >= 2:
            await ctx.send("Reached limit (2) of starboards! Can't create another one!")
            return
        elif threshold <= 0:
            await ctx.send("You can't set a threshold that's equal to or less than 0.")
            return
        elif self.bot.db.channels.count_documents({"guild": guild, "reaction": reaction}) >= 1:
            await ctx.send("You're already using that reaction in this discord.")
            return
        elif self.bot.db.channels.count_documents({"channel": channel}) >= 1:  # we could delete this tbh
            await ctx.send("This channel is already being used for a starboard. Try another channel.")
            return
        elif self.bot.db.channels.count_documents({"guild": guild, "name": name}) >= 1:
            await ctx.send("You've already made a starboard with that name.")
            return
        self.bot.db.create_collection(helpers.get_board_name(guild, name))
        self.bot.db.channels.insert_one(new_channel)
        await ctx.send("Starboard '" + name + "' created in this channel, with " + reaction +
                       " as reaction and threshold " + str(threshold))

    # modify - Subcommand for starboards to modify settings
    # Modifies properties for settings already here.
    """ modify - 
        Modifies threshold and anti-star feature.
        Setting threshold: `!starboard modify threshold [threshold]`
        Setting anti-star: `!starboard modify antistar [emoji]`
        or `!starboard modify antistar clear` to clear """

    @starboard.command(help="!starboard modify [board name] [antistar/threshold] [reaction/value]")
    async def modify(self, ctx, name: str, option: str, value: str):
        board_name = helpers.get_board_name(ctx.guild.id, name)
        search = {"guild": ctx.guild.id, "name": board_name}
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
                                       or self.bot.db.channels.count_documents(
                    {"guild": ctx.guild.id, "antistar": value})):
            await ctx.send("You're already using that emoji in this discord!")
            return
        elif option == 'threshold' and int(value) <= 0:
            await ctx.send("You can't set a threshold that's equal to or less than 0.")
            return
        if value == "clear":
            value_to_assign = ""
            self.clear_antistars(board_name)
            await ctx.send("Starboard " + name + "'s antistars cleared.")
        elif option == "threshold":
            value_to_assign = int(value)
            await ctx.send("Starboard " + name + "'s threshold settings set to " + value + ".")
        else:
            value_to_assign = value
            await ctx.send("Starboard " + name + "'s anti-star reaction set to " + value + ".")
        self.bot.db.channels.find_one_and_update(filter=search, update={"$set": {option: value_to_assign}}, upsert=False)

    @starboard.command(help="!starboard create [board name] [reaction] {threshold}")
    async def remove(self, ctx, name: str):
        board_name = helpers.get_board_name(ctx.guild.id, name)
        search = {"guild": ctx.guild.id, "name": board_name}
        board = self.bot.db.channels.find_one(search)
        if board is None:
            await ctx.send("Starboard " + name + " does not exist!")
            return
        self.bot.db.star_messages.delete_many({"board_name": board_name})
        self.bot.db.drop_collection(board_name)
        self.bot.db.channels.find_one_and_delete(search)
        await ctx.send("Starboard " + name + " has been deleted!")

    # TODO: starboard list/remove subcommand to list starboards

    """
    update_starboard
    Given a reacted message and a board name, checks and sends a message to the respective star channel.
    """
    async def update_starboard(self, message, board_name):
        coll = self.bot.db[board_name]
        reaction_entry = coll.find_one({"message": message.id, "antistar": False})
        if reaction_entry is None:  # there aren't no stars, so there's no more need to update
            return
        stars = coll.count_documents({"message": message.id, "antistar": False})
        antistars = coll.count_documents({"message": message.id, "antistar": True})
        board = self.bot.db.channels.find_one({"guild": message.guild.id, "name": board_name})
        star_message = self.bot.db.star_messages.find_one({"board_name": board_name, "message": message.id})
        star_channel = self.bot.get_channel(board["channel"])

        # check star_messages if it's already sent as a message, then edit it
        if star_message is not None:
            update_message = await star_channel.fetch_message(star_message["star_message"])
            await update_message.edit(content=str(int(stars - antistars)) + " " + reaction_entry["reaction"])
            return

        # if not a message yet, send a new one.
        if stars - antistars >= board["threshold"]:
            sb_message = await star_channel.send(content=str(int(stars - antistars)) + " " + reaction_entry["reaction"],
                                                 embed=helpers.create_embed(message))
            self.bot.db.star_messages.insert_one({
                "board_name": board_name,
                "message": message.id,
                "star_message": sb_message.id,
                "stars": stars + antistars,
            })

    def clear_antistars(self, board_name):
        coll = self.bot.db[board_name]
        coll.delete_many(filter={"antistar": True})
        self.bot.db.channels.find_one_and_update({"name": board_name}, {"$set": {"antistar": ""}})

def setup(bot):
    bot.add_cog(Starboard(bot))
