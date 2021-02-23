import discord, helpers, pymongo

async def update_starboard(bot, message, board_name):
    reaction_entry = bot.db.stars.find_one({"message": message.id, "antistar": False})
    if reaction_entry is None:  # there aren't no stars, so there's no more need to update
        return
    stars = bot.db.stars.count_documents({"message": message.id, "antistar": False})
    antistars = bot.db.stars.count_documents({"message": message.id, "antistar": True})
    board = bot.db.channels.find_one({"guild": message.guild.id, "name": board_name})
    star_message = bot.db.star_messages.find_one({"board_name": board_name, "message": message.id})
    star_channel = bot.get_channel(board["channel"])

    # check star_messages if it's already sent as a message, then edit it
    if star_message is not None:
        update_message = await star_channel.fetch_message(star_message["star_message"])
        await update_message.edit(content=str(int(stars - antistars)) + " " + reaction_entry["reaction"])
        return

    total_stars = int(stars - antistars)
    # if not a message yet, send a new one.
    if total_stars >= board["threshold"]:
        sb_message = await star_channel.send(
            content=str(total_stars) + " " + reaction_entry["reaction"],
            embed=helpers.create_embed(message))
        bot.db.star_messages.insert_one({
            "board_name": board_name,
            "message": message.id,
            "star_message": sb_message.id,
            "stars": stars + antistars,
        })

"""channels needs to be a dictionary with all starboard channels, requested from mongodb:"""

async def send_leaderboard(bot, ctx):
    embed = discord.Embed(title="Top posts:")
    channels = list(bot.db.channels.find({"guild": ctx.guild.id}))

    for i in range(len(channels)):
        board_name = channels[i]["name"]
        top_posts = list(bot.db.star_messages.find({"board_name": board_name}).sort(board_name, pymongo.DESCENDING))
        if top_posts is None:
            continue
        leaderboard = ""
        for j in range(min(len(top_posts), 5)):
            message = ctx.channel.get_partial_message(top_posts[j]["message"])
            leaderboard += "[" + str(message.id) + "]" + "(" + message.jump_url + ") - " + \
                           str(top_posts[j]["stars"]) + " " + channels[i]["reaction"] + "\n"
        if leaderboard == "":
            continue
        embed.add_field(name="Top posts in " + helpers.get_raw_board_name(board_name),
                        value=leaderboard)
    # still need to get highest user's stars, highest star givers

    top_users, top_givers = "", ""
    stars_received = bot.db.stars.aggregate([
        {"$match": {"guild": ctx.guild.id, "antistar": False}},
        {"$group": {"_id": "$message_author", "total": {"$sum": "$amount"}}}
    ])

    stars_given = bot.db.stars.aggregate([
        {"$match": {"guild": ctx.guild.id, "antistar": False}},
        {"$group": {"_id": "$reactor", "total": {"$sum": "$amount"}}}
    ])

    for doc in stars_received:
        top_users += doc["_id"] + " (" + doc["total"] + " stars)\n"
    for doc in stars_given:
        top_givers += doc["_id"] + " (" + doc["total"] + " stars)\n"
    if top_users != "" or None:
        embed.add_field(name="Top star receivers: ",
                        value=top_users)
    if top_givers != "" or None:
        embed.add_field(name="Top star givers: ",
                        value=top_givers)

    """ 
    # top users:
    index = 0
    for i in range(min(len(stars_received), 5)):
        \n"

    for i in stars_given:
        top_givers += str(index + 1) + ". " + i["_id"] + " (" + i["total"] + " stars)\n"
    """
    return embed

def send_user_leaderboard(bot, user, guild_id):
    embed = discord.Embed()
    top_users, top_givers = "", ""

    stars_received = list(bot.db.stars.aggregate([
        {"$match": {"guild": guild_id, "antistar": False, "message_author": user.name}},
        {"$group": {"_id": "$reactor", "total": {"$sum": "$amount"}}}
    ]))

    stars_given = list(bot.db.stars.aggregate([
        {"$match": {"guild": guild_id, "antistar": False, "reactor": user.name}},
        {"$group": {"_id": "$message_author", "total": {"$sum": "$amount"}}}
    ]))

    print(stars_given, stars_received)

    for i in range(min(len(stars_received), 5)):
        top_users += stars_received[i]["_id"] + "\n"
    embed.add_field(name="Your fans: (top reactors to your messages)", value=top_users)

    for i in range(min(len(stars_given), 5)):
        top_givers += stars_given[i]["_id"] + "\n"
    embed.add_field(name="You're a fan of: (top message authors)", value=top_users)
    return embed
