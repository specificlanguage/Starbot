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
    total_stars = int(stars - antistars)

    # check star_messages if it's already sent as a message, then edit it
    if star_message is not None:
        update_message = await star_channel.fetch_message(star_message["star_message"])
        await update_message.edit(content=str(total_stars) + " " + reaction_entry["reaction"])
        return

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
            "guild": message.guild.id,
            "reaction": reaction_entry["reaction"],
            "author": message.author.name
        })

async def all_leaderboards(bot, ctx):
    embed = discord.Embed(title="Top posts:", color=discord.Colour.blue())
    channels = list(bot.db.channels.find({"guild": ctx.guild.id}))
    for i in range(len(channels)):
        await send_leaderboard(bot, ctx, channels[i]["name"], embed, short=True)
    return embed

async def send_leaderboard(bot, ctx, board_name, embed, short=False):
    top_posts = list(bot.db.star_messages.find({"board_name": board_name}).sort("stars", pymongo.DESCENDING))
    leaderboard = ""

    for j in range(min(len(top_posts), 5)):
        message = ctx.channel.get_partial_message(top_posts[j]["message"])
        leaderboard += "{} [{}]({}) - {} {}\n" \
            .format(helpers.rank_list[j], str(message.id), message.jump_url,
                    str(top_posts[j]["stars"]), top_posts[j]["reaction"])

    if leaderboard != "":
        embed.add_field(name="Top posts in " + helpers.get_raw_board_name(board_name), value=leaderboard)
    if short:
        return

    received_pipeline = [{'$match': {'guild': ctx.guild.id, 'antistar': False}},
                         {'$group': {'_id': '$message_author', 'count': {'$sum': 1}}},
                         {'$sort': {'count': -1}}]

    gave_pipeline = [{'$match': {'guild': ctx.guild.id, 'antistar': False}},
                     {'$group': {'_id': '$reactor', 'count': {'$sum': 1}}},
                     {'$sort': {'count': -1}}]

    top_receivers = helpers.aggregate_to_str(bot, "stars", received_pipeline)
    top_givers = helpers.aggregate_to_str(bot, "stars", gave_pipeline)

    if top_receivers != "":
        embed.add_field(name="Top star receivers: ", value=top_receivers, inline=False)
    if top_givers != "":
        embed.add_field(name="Top star givers: ", value=top_givers, inline=False)

    return embed

async def all_user_leaderboards(bot, ctx, user):
    embed = discord.Embed(title="Top posts:", color=discord.Colour.blue())
    channels = list(bot.db.channels.find({"guild": ctx.guild.id}))
    for i in range(len(channels)):
        await send_user_leaderboard(bot, ctx, user, channels[i]["name"], embed, short=True)
    return embed


async def send_user_leaderboard(bot, ctx, user, board_name, embed, short=False):
    raw_bn = helpers.get_raw_board_name(board_name)
    embed.set_author(name=user.name, icon_url=user.avatar_url)
    top_posts = list(bot.db.star_messages.find({"author": user.name}).sort("stars", pymongo.DESCENDING))
    leaderboard = ""

    for j in range(min(len(top_posts), 5)):
        message = ctx.channel.get_partial_message(top_posts[j]["message"])
        leaderboard += "{}. [{}]({}) - {}{}\n" \
            .format(str(j+1), str(message.id), message.jump_url,
                    str(top_posts[j]["stars"]), top_posts[j]["reaction"])
    if leaderboard != "":
        embed.add_field(name="{}'s top posts in {}: ".format(user.name, raw_bn),
                        value=leaderboard, inline=True)
    if short:
        return embed

    received_pipeline = [
        {"$match": {"board_name": board_name, "antistar": False, "message_author": user.name}},
        {"$group": {"_id": "$reactor", "count": {"$sum": 1}}},
        {"$sort": {'count': -1}}]
    given_pipeline = [{"$match": {"board_name": board_name, "antistar": False, "reactor": user.name}},
        {"$group": {"_id": "$message_author", "count": {"$sum": 1}}},
        {"$sort": {'count': -1}}]

    top_receivers = helpers.aggregate_to_str(bot, "stars", received_pipeline)
    top_givers = helpers.aggregate_to_str(bot, "stars", given_pipeline)

    if top_receivers != "":
        embed.add_field(name="Your beta orbiters in {}: ".format(helpers.get_raw_board_name(board_name)),
                        value=top_receivers, inline=False)
    if top_givers != "":
        embed.add_field(name="Your idols in {}: ".format(helpers.get_raw_board_name(board_name)),
                        value=top_givers, inline=False)

    return embed
