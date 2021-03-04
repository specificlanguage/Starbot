import discord
import helpers
import pymongo

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
            leaderboard += ":{}: [{}]({}) - {} {}\n" \
                .format(str(j+1), str(message.id), message.jump_url,
                        str(top_posts[j]["stars"]), channels[i]["reaction"])
        if leaderboard == "":
            continue
        embed.add_field(name="Top posts in " + helpers.get_raw_board_name(board_name),
                        value=leaderboard)

    recieved_pipeline = [{'$match': {'guild': ctx.guild.id, 'antistar': False}},
                         {'$group': {'_id': '$message_author', 'count': {'$sum': 1}}},
                         {'$sort': {'count': -1}}]

    gave_pipeline = [{'$match': {'guild': ctx.guild.id, 'antistar': False}},
                     {'$group': {'_id': '$reactor', 'count': {'$sum': 1}}},
                     {'$sort': {'count': -1}}]

    highest_star_receivers = list(bot.db.stars.aggregate(recieved_pipeline))
    highest_star_givers = list(bot.db.stars.aggregate(gave_pipeline))

    top_receivers, top_givers = "", ""
    for i in range(min(len(highest_star_receivers), 5)):
        item = highest_star_receivers[i]
        top_receivers += ":{}: {} ({})\n".format(str(i), item["_id"], item["count"])
    if top_receivers != "":
        embed.add_field(name="Top star receivers: ", value=top_receivers)

    for i in range(min(len(highest_star_givers), 5)):
        item = highest_star_receivers[i]
        top_givers += ":{}: {} ({})\n".format(str(i), item["_id"], item["count"])
    if top_givers != "":
        embed.add_field(name="Top star givers: ", value=top_givers)

    return embed


def send_user_leaderboard(bot, user, guild_id):
    embed = discord.Embed()
    top_receivers, top_givers = "", ""

    received_pipeline = [
        {"$match": {"guild": guild_id, "antistar": False, "message_author": user.name}},
        {"$group": {"_id": "$reactor", "count": {"$sum": 1}}},
        {"$sort": {'count': -1}}]
    given_pipeline = [{"$match": {"guild": guild_id, "antistar": False, "reactor": user.name}},
        {"$group": {"_id": "$reactor", "count": {"$sum": 1}}},
        {"$sort": {'count': -1}}]

    stars_received = list(bot.db.stars.aggregate(received_pipeline))
    stars_given = list(bot.db.stars.aggregate(given_pipeline))

    for i in range(min(len(stars_received), 5)):
        item = stars_received[i]
        top_receivers += ":{}: {} ({})\n".format(str(i), item["_id"], item["count"])

    for i in range(min(len(stars_given), 5)):
        item = stars_given[i]
        top_givers += ":{}: {} ({})\n".format(str(i), item["_id"], item["count"])

    if top_givers != "":
        embed.add_field(name="Your beta orbiters: ", value=top_receivers)
        embed.add_field(name="Your idols: ", value=top_givers)

    return embed
