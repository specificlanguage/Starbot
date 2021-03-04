from discord.ext import commands
import discord, helpers
import cogs.messages as messages

class Starboard(commands.Cog, name="Starboard"):
    def __init__(self, bot):
        self.bot = bot

    """on_raw_reaction_add: updates starboard and database when reaction is set."""

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        results = await helpers.validate_reaction(self.bot, payload)
        if results is None:
            return  # no need to update db
        board_name, query = results
        self.bot.db.stars.insert_one(query)
        message = await self.bot.get_channel(payload.channel_id).fetch_message(query["message"])
        await messages.update_starboard(self.bot, message, board_name)

    """on_raw_reaction_remove: updates starboard and database when reaction removed."""

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        results = await helpers.validate_reaction(self.bot, payload)
        if results is None:
            return  # no need to update db
        board_name, query = results[0], results[1]
        self.bot.db.stars.delete_one(query)
        message = await self.bot.get_channel(payload.channel_id).fetch_message(query["message"])
        await messages.update_starboard(self.bot, message, board_name)

    # top command for starboard settings command.
    @commands.group(name="starboard", help="Creates, manages, lists and removes starboards",
                    brief="Manages starboards")
    async def starboard(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Incorrect subcommand! Try !help starboard for more info.")


    """ create -
        When command is run, given name, reaction, and threshold,
        creates a new starboard in the channel that the command is run.
    """
    @starboard.command(help="!starboard create [board name] [reaction] {threshold}\n")
    async def create(self, ctx, name: str, reaction: str, threshold: str):

        if not threshold.isnumeric():
            ctx.send("Threshold must be a number.")
            return

        # set up variables
        guild, channel, threshold = ctx.guild.id, ctx.channel.id, int(threshold)
        coll_name = helpers.get_db_board_name(guild_id=guild, board_name=name)
        starboards = list(self.bot.db.channels.find({"guild": guild}))

        checks = {"name_too_long": len("starbot." + coll_name) >= 100,
                  "name_too_short": len(name) < 0,
                  "channel_being_used": channel in [i["channel"] for i in starboards],
                  "too_many": len(starboards) >= helpers.get_board_limit(),
                  "name_used": name in [i["name"] for i in starboards],
                  "reaction_used": reaction in ([i["reaction"] for i in starboards] +
                                                [i["antistar"] for i in starboards]),
                  "is_not_emoji": not helpers.is_emoji(self.bot, reaction),
                  "threshold_low": threshold <= 0,
                  "threshold_high": threshold >= 1000000}

        for key, value in checks.items():
            if value:
                await ctx.send(helpers.get_error_message(key))
                return

        new_channel = {'name': coll_name, 'guild': guild, 'channel': channel,
                       'reaction': reaction, 'threshold': threshold, 'antistar': ""}
        self.bot.db.channels.insert_one(new_channel)
        await ctx.send("Starboard '" + name + "' created in this channel, with " + reaction +
                       " as reaction and threshold " + str(threshold))

    # modify - Subcommand for starboards to modify settings
    """ modify - 
        Modifies threshold and anti-star feature.
        Setting threshold: `!starboard modify threshold [threshold]`
        Setting anti-star: `!starboard modify antistar [emoji]`
        or `!starboard modify antistar clear` to clear """
    @starboard.command(help="!starboard modify [board name] [antistar/threshold] [reaction/value]")
    async def modify(self, ctx, name: str, option: str, value: str):
        board_name = helpers.get_db_board_name(ctx.guild.id, name)
        search = {"guild": ctx.guild.id, "name": board_name}
        valid_options = ["threshold", "antistar"]

        if self.bot.db.channels.count_documents(search) == 0:
            await ctx.send("You don't have a starboard with this name.")
            return

        # Update threshold of board
        if option == valid_options[0]:
            if not value.isnumeric():
                await ctx.send("Threshold must be a number.")
                return
            threshold = int(value)
            checks = {"threshold_low": threshold <= 0,
                      "threshold_high": threshold >= 1000000}
            for key, val in checks.items():
                if val:
                    await ctx.send(helpers.get_error_message(key))
                    return
            self.bot.db.channels.find_one_and_update(filter=search, update={"$set": {"threshold": value}},
                                                     upsert=False)
            await ctx.send("Starboard '" + name + "' threshold set to " + value)
            return

        # Update antistar option
        if option == valid_options[1]:
            if value.lower() == "clear":
                self.clear_antistars(board_name)
                await ctx.send("Cleared antistars. (You won't get them back!)")
                await ctx.send("Restar a starred message to update that message.")
                return
            starboards = list(self.bot.db.channels.find({"guild": ctx.guild.id}))

            checks = {"reaction_used": value in [i["reaction"] for i in starboards] +
                                             [i["antistar"] for i in starboards],
                      "is_not_emoji": not helpers.is_emoji(self.bot, value)}

            for key, val in checks.items():
                if val:
                    await ctx.send(helpers.get_error_message(key))
                    return

            self.bot.db.channels.find_one_and_update(search, {"$set":{"antistar": value}})
            await ctx.send("Starboard '" + name + "' antistar changed to " + value)
            return

        else:
            await ctx.send("Not a valid option! Valid options: " + str(valid_options))
            return

    @starboard.command(help="- Removes starboard  -  !starboard remove [board name]", aliases=["delete"])
    async def remove(self, ctx, name: str):
        board_name = helpers.get_db_board_name(ctx.guild.id, name)
        search = {"guild": ctx.guild.id, "name": board_name}
        board = self.bot.db.channels.find_one(search)
        if board is None:
            await ctx.send("Starboard " + name + " does not exist!")
            return
        self.bot.db.star_messages.delete_many({"board_name": board_name})
        self.bot.db.channels.find_one_and_delete(search)
        await ctx.send("Starboard '" + name + "' has been deleted!")

    @starboard.command(help="Lists starboards  -  !starboard list")
    async def list(self, ctx):
        channels = list(self.bot.db.channels.find({"guild": ctx.guild.id}))
        embed = discord.Embed(title="Starboards in this discord:")
        for channel in channels:
            ch_name, guild_id = channel["name"].split("-")
            ch_id = channel["channel"]
            ch = self.bot.get_channel(ch_id)
            star = channel["reaction"]
            antistar = channel["antistar"]
            result = "Star: " + star + "\n"
            if antistar != "":
                result += "Antistar: " + antistar + "\n"
            result += "Threshold: " + str(channel["threshold"]) + "\n" + "Starboard feed: " + ch.name + "\n"
            embed.add_field(name=ch_name, value=result)
        await ctx.send(embed=embed)

    @commands.command(name="stars", help="Finds highest starred messages from all starboards, and links them. \n"
                                         "Mention a user to get their highest posts.")
    async def leaderboard(self, ctx):
        if not ctx.message.raw_mentions:
            embed = await messages.send_leaderboard(self.bot, ctx)
            await ctx.send(embed=embed)
            return
        user = self.bot.get_user(ctx.raw_mentions[0])
        embed = await messages.send_user_leaderboard(self.bot, user, guild_id=ctx.guild.id)
        await ctx.send(embed=embed)

    """
    update_starboard
    Given a reacted message and a board name, checks and sends a message to the respective star channel.
    """

    def clear_antistars(self, board_name):
        self.bot.db.stars.delete_many(filter={"board_name": board_name, "antistar": True})
        self.bot.db.channels.find_one_and_update({"name": board_name}, {"$set": {"antistar": ""}})

def setup(bot):
    bot.add_cog(Starboard(bot))
