from discord.ext import commands
from pymongo import ReturnDocument
import helpers

class Starboard(commands.Cog, name="Starboard"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        emoji = str(payload.emoji)  # this is due to mongodb's limitations. Probably have to fix this.
        user = payload.member
        if user == message.author:
            return # reactions made by users do not count.
        valid_reactions = self.bot.db.channels.find_one({"guild": channel.guild.id, "$or": [
            {"reaction": emoji}, {"antistar": emoji}]})
        if valid_reactions is None:
            return  # no need to do anything here.
        board_name = valid_reactions["name"]
        antistar = False
        change = 1
        try:
            if valid_reactions["antistar"] == emoji:
                antistar = True
                change = -1
        except KeyError:
            pass
        coll = self.bot.db[board_name]
        coll.insert_one({"reactor": user.name, "message": message.id,"message_author": message.author.name,
            "reaction": emoji, "antistar": antistar})

        await self.update_starboard(message, board_name, change)

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
        elif self.bot.db.channels.count_documents({"channel": channel}) >= 1: # we could delete this tbh
            await ctx.send("This channel is already being used for a starboard. Try another channel.")
            return
        elif self.bot.db.channels.count_documents({"guild": guild, "name": name}) >= 1:
            await ctx.send("You've already made a starboard with that name.")
            return
        self.bot.db.create_collection(name + str(guild.id))
        self.bot.db.channels.insert_one(new_channel)
        await ctx.send("Starboard '" + name + "' created in this channel, with " + reaction +
                       " as reaction and threshold " + str(threshold))

    # modify - Subcommand for starboards to modify settings
    # Modifies properties for settings already here.
    """ Modifies threshold and anti-star feature.
        Setting threshold: `!starboard modify threshold [threshold]`
        Setting anti-star: `!starboard modify antistar [emoji]`
        or `!starboard modify antistar clear` to clear """

    @starboard.command()
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
        self.bot.db.channels.find_one_and_update(query=search, update={"$set": {option: value_to_assign}}, upsert=False)

    # TODO: starboard list/remove subcommand to list starboards

    async def update_starboard(self, message, board_name, change):
        if change != 1 or change != -1: # makes it easy to know what the change is
            return
        print("updating starboard...")
        # if already added and there's a message, skip the full posting system
        board = self.bot.db.channels.find_one({"guild": message.guild.id, "name": board_name})
        star_message = self.bot.db.star_messages.find_one_and_update(
            {"board_name": board_name, "star_message": message.id}, {"$inc": {'stars': change}},
            return_document=ReturnDocument.BEFORE, upsert=False)
        if star_message is not None:
            sb_message = await self.bot.fetch_message(star_message[0]["star_message"])
            if star_message[0]["stars"] < board[0]["threshold"]: # removing message: lost threshold
                await sb_message.delete()
            await sb_message.edit(content=str(int(star_message[0]["stars"]) + change))
            # note: getting from star message here will get the ReturnDocument prior to the change.
            return

        # not added into database yet: adding message
        coll = self.bot.db[board_name]
        reaction_entry = coll.find_one(query={"message": message.id})
        stars = coll.count_documents(query={"message": message.id, "antistars": False})
        antistars = coll.count_documents(query={"message": message.id, "antistars": True})

        if stars + antistars >= board[0]["threshold"] and len(list(star_message)) == 0:
            star_channel = await self.bot.getchannel(board[0]["channel"])
            sb_message = await star_channel.send(content=str(stars+antistars) + reaction_entry["reaction"],
                                                 embed=helpers.create_embed(message))
            self.bot.db.star_messages.insert_one({
                "board_name": board_name,
                "message": message.id,
                "star_message": sb_message.id,
                "stars": stars+antistars,
            })



def clear_antistars():
    pass
    # TODO, probably not too hard, because it really just means dump the anti-star entries

def setup(bot):
    bot.add_cog(Starboard(bot))
