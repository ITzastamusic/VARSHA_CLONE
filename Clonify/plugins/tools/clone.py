import re, requests, importlib, logging, asyncio
from sys import argv
from pyrogram import idle
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import (
    AccessTokenExpired,
    AccessTokenInvalid,
)
from Clonify.utils.database import get_assistant
from Clonify import app
from Clonify.misc import SUDOERS
from Clonify.utils.database import get_assistant, clonebotdb
from Clonify.utils.database.clonedb import has_user_cloned_any_bot
from Clonify.utils.decorators.language import language
import pyrogram.errors

from Clonify.utils.database.clonedb import get_owner_id_from_db
from config import SUPPORT_CHAT, OWNER_ID, LOGGER_ID, CLONE_LOGGER, API_ID, API_HASH
from datetime import datetime

CLONES = set()

C_BOT_DESC = "ᴡᴀɴᴛ ᴀ ʙᴏᴛ ʟɪᴋᴇ ᴛʜɪs ? ᴄʟᴏɴᴇ ɪᴛ ɴᴏᴡ! ✅\n\nᴠɪsɪᴛ : @varshaamusicbot ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ!\n\n - ᴜᴘᴅᴀᴛᴇ : @ixasta1 \n - sᴜᴘᴘᴏʀᴛ : @odsnetwork"

C_BOT_COMMANDS = [
    {"command": "/start", "description": "sᴛᴀʀᴛs ᴛʜᴇ ᴍᴜsɪᴄ ʙᴏᴛ"},
    {"command": "/help", "description": "ɢᴇᴛ ʜᴇʟᴩ ᴍᴇɴᴜ ᴡɪᴛʜ ᴇxᴩʟᴀɴᴀᴛɪᴏɴ ᴏғ ᴄᴏᴍᴍᴀɴᴅs."},
    {"command": "/play", "description": "sᴛᴀʀᴛs sᴛʀᴇᴀᴍɪɴɢ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴛʀᴀᴄᴋ ᴏɴ ᴠɪᴅᴇᴏᴄʜᴀᴛ."},
    {"command": "/pause", "description": "ᴩᴀᴜsᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ."},
    {"command": "/resume", "description": "ʀᴇsᴜᴍᴇ ᴛʜᴇ ᴩᴀᴜsᴇᴅ sᴛʀᴇᴀᴍ."},
    {"command": "/skip", "description": "sᴋɪᴩ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ sᴛʀᴇᴀᴍ ᴀɴᴅ sᴛᴀʀᴛ ɴᴇxᴛ ᴛʀᴀᴄᴋ."},
    {"command": "/end", "description": "ᴄʟᴇᴀʀ ᴛʜᴇ ǫᴜᴇᴜᴇ ᴀɴᴅ ᴇɴᴅ ᴛʜᴇ sᴛʀᴇᴀᴍ."},
    {"command": "/ping", "description": "ᴘɪɴɢ & sʏsᴛᴇᴍ sᴛᴀᴛs."}
]

@app.on_message(filters.command("clone"))
@language
async def clone_txt(client, message, _):
    userbot = await get_assistant(message.chat.id)

    userid = message.from_user.id
    has_already_cbot = await has_user_cloned_any_bot(userid)

    if has_already_cbot:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_H_0"])
    else:
        pass

    if len(message.command) > 1:
        bot_token = message.text.split("/clone", 1)[1].strip()
        mi = await message.reply_text(_["C_B_H_2"])
        try:
            ai = Client(
                bot_token,
                API_ID,
                API_HASH,
                bot_token=bot_token,
                plugins=dict(root="PurviBots.cplugin"), 
            )
            await ai.start()
            bot = await ai.get_me()
            bot_users = await ai.get_users(bot.username)
            bot_id = bot_users.id
            c_b_owner_fname = message.from_user.first_name
            c_bot_owner = message.from_user.id

        except (AccessTokenExpired, AccessTokenInvalid):
            await mi.edit_text(_["C_B_H_3"])
            return
        except Exception as e:
            if "database is locked" in str(e).lower():
                await message.reply_text(_["C_B_H_4"])
            else:
                await mi.edit_text(f"ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ:\n `{str(e)}`")
            return

        await mi.edit_text(_["C_B_H_5"])
        try:
            await app.send_message(
                CLONE_LOGGER,
                f"**#ɴᴇᴡ_ᴄʟᴏɴᴇᴅ_ʙᴏᴛ**\n\n"
                f"**ʙᴏᴛ :** {bot.mention}\n"
                f"**ᴜsᴇʀɴᴀᴍᴇ :** @{bot.username}\n"
                f"**ʙᴏᴛ ɪᴅ :** `{bot_id}`\n\n"
                f"**ᴏᴡɴᴇʀ :** [{c_b_owner_fname}](tg://user?id={c_bot_owner})"
            )

            await userbot.send_message(bot.username, "/start")

            details = {
                "bot_id": bot.id,
                "is_bot": True,
                "user_id": message.from_user.id,
                "name": bot.first_name,
                "token": bot_token,
                "username": bot.username,
                "channel": "iamvillain77",
                "support": "odsnetwork",
                "premium": False,
                "Date": False,
            }
            clonebotdb.insert_one(details)
            CLONES.add(bot.id)

            def set_bot_commands():
                url = f"https://api.telegram.org/bot{bot_token}/setMyCommands"
                params = {"commands": C_BOT_COMMANDS}
                response = requests.post(url, json=params)
                print(response.json())

            set_bot_commands()

            def set_bot_desc():
                url = f"https://api.telegram.org/bot{bot_token}/setMyDescription"
                params = {"description": C_BOT_DESC}
                response = requests.post(url, data=params)
                if response.status_code == 200:
                    logging.info(f"sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘᴅᴀᴛᴇᴅ ʙᴏᴛ ᴅᴇsᴄ : {bot_token}")
                else:
                    logging.error(f"ғᴀɪʟᴇᴅ ᴛᴏ ᴜᴘᴅᴀᴛᴇ ᴅᴇsᴄ : {response.text}")

            set_bot_desc()

            await mi.edit_text(_["C_B_H_6"].format(bot.username))

        except BaseException as e:
            logging.exception("ᴇʀʀᴏʀ ᴡʜɪʟᴇ ᴄʟᴏɴɪɴɢ ʙᴏᴛ.")
            await mi.edit_text(
                f"⚠️ **ᴇʀʀᴏʀ :**\n\n`{e}`\n\n"
                "**ᴋɪɴᴅʟʏ ғᴏʀᴡᴀʀᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ @iamakki001 ғᴏʀ ʜᴇʟᴘ**"
            )
    else:
        await message.reply_text(_["C_B_H_1"])


@app.on_message(filters.command(
    ["delbot","rmbot","delcloned","delclone","deleteclone","removeclone","cancelclone"]
))
@language
async def delete_cloned_bot(client, message, _):
    try:
        if len(message.command) < 2:
            return await message.reply_text(_["C_B_H_8"])

        query_value = " ".join(message.command[1:])
        if query_value.startswith("@"):
            query_value = query_value[1:]

        await message.reply_text(_["C_B_H_9"])

        cloned_bot = clonebotdb.find_one(
            {"$or": [{"token": query_value}, {"username": query_value}]}
        )

        if cloned_bot:
            bot_info = (
                f"**ʙᴏᴛ ɪᴅ :** `{cloned_bot['bot_id']}`\n"
                f"**ʙᴏᴛ ɴᴀᴍᴇ :** {cloned_bot['name']}\n"
                f"**ᴜsᴇʀɴᴀᴍᴇ :** @{cloned_bot['username']}\n"
                f"**ᴛᴏᴋᴇɴ :** `{cloned_bot['token']}`\n"
                f"**ᴏᴡɴᴇʀ :** `{cloned_bot['user_id']}`\n"
            )

            C_OWNER = get_owner_id_from_db(cloned_bot['bot_id'])
            OWNERS = [OWNER_ID, C_OWNER]

            if message.from_user.id not in OWNERS:
                return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))

            clonebotdb.delete_one({"_id": cloned_bot["_id"]})
            CLONES.remove(cloned_bot["bot_id"])

            await message.reply_text(_["C_B_H_10"])
            await app.send_message(CLONE_LOGGER, bot_info)

        else:
            await message.reply_text(_["C_B_H_11"])

    except Exception as e:
        await message.reply_text(_["C_B_H_12"])
        logging.exception(e)


async def start_clone(bot_data):
    bot_token = bot_data["token"]

    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    r = requests.get(url)

    if r.status_code != 200:
        logging.error(f"ᴇxᴘɪʀᴇᴅ ᴛᴏᴋᴇɴ ʀᴇᴍᴏᴠᴇᴅ : {bot_token}")
        clonebotdb.delete_one({"token": bot_token})
        return None

    try:
        ai = Client(
            f"{bot_token}",
            API_ID,
            API_HASH,
            bot_token=bot_token,
            plugins=dict(root="PurviBots.cplugin"),
        )

        await ai.start()
        bot = await ai.get_me()
        CLONES.add(bot.id)

        return bot.id

    except Exception as e:
        logging.error(f"ᴇʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ʙᴏᴛ : {e}")
        return None


async def restart_bots():
    global CLONES
    logging.info("ʀᴇsᴛᴀʀᴛɪɴɢ ᴄʟᴏɴᴇᴅ ʙᴏᴛs...")

    bots = list(clonebotdb.find())
    tasks = [start_clone(bot) for bot in bots]
    results = await asyncio.gather(*tasks)

    active_bots = [r for r in results if r]

    await app.send_message(
        CLONE_LOGGER, f"**» sᴛᴀʀᴛᴇᴅ {len(active_bots)} ᴄʟᴏɴᴇ ʙᴏᴛs sᴜᴄᴄᴇssғᴜʟʟʏ!**"
    )


@app.on_message(filters.command("delallclone") & filters.user(OWNER_ID))
@language
async def delete_all_cloned_bots(client, message, _):
    try:
        await message.reply_text(_["C_B_H_14"])

        clonebotdb.delete_many({})
        CLONES.clear()

        await message.reply_text(_["C_B_H_15"])
    except:
        await message.reply_text("**» ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ᴅᴇʟᴇᴛɪɴɢ ᴀʟʟ ʙᴏᴛs.**")


@app.on_message(filters.command(["mybot","mybots"], prefixes=["/", "."]))
@language
async def my_cloned_bots(client, message, _):
    try:
        user_id = message.from_user.id
        cloned_bots = list(clonebotdb.find({"user_id": user_id}))

        if not cloned_bots:
            return await message.reply_text(_["C_B_H_16"])

        total = len(cloned_bots)
        text = f"**ʏᴏᴜʀ ᴄʟᴏɴᴇᴅ ʙᴏᴛs : {total}**\n\n"

        for bot in cloned_bots:
            text += (
                f"**ɴᴀᴍᴇ :** {bot['name']}\n"
                f"**ᴜsᴇʀɴᴀᴍᴇ :** @{bot['username']}\n\n"
            )

        await message.reply_text(text)

    except Exception as e:
        logging.exception(e)
        await message.reply_text("ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ.")


@app.on_message(filters.command("cloned") & SUDOERS)
@language
async def list_cloned_bots(client, message, _):
    try:
        cloned_bots = list(clonebotdb.find())

        if not cloned_bots:
            return await message.reply_text(_["C_B_H_13"])

        total = len(cloned_bots)
        text = f"**» ᴛᴏᴛᴀʟ ᴄʟᴏɴᴇᴅ ʙᴏᴛs : `{total}`**\n\n"

        chunk_size = 10
        chunks = [cloned_bots[i:i + chunk_size] for i in range(0, len(cloned_bots), chunk_size)]

        for chunk in chunks:
            chunk_text = text
            for bot in chunk:
                try:
                    owner = await client.get_users(bot['user_id'])
                    owner_name = owner.first_name
                    owner_link = f"tg://user?id={bot['user_id']}"
                except:
                    owner_name = "ᴜɴᴋɴᴏᴡɴ"
                    owner_link = "#"

                chunk_text += (
                    f"**ʙᴏᴛ ɪᴅ :** `{bot['bot_id']}`\n"
                    f"**ɴᴀᴍᴇ :** {bot['name']}\n"
                    f"**ᴜsᴇʀɴᴀᴍᴇ :** @{bot['username']}\n"
                    f"**ᴏᴡɴᴇʀ :** [{owner_name}]({owner_link})\n\n"
                )

            await message.reply_text(chunk_text)

    except Exception as e:
        await message.reply_text("» ᴇʀʀᴏʀ ʟɪsᴛɪɴɢ ʙᴏᴛs.")


@app.on_message(filters.command("totalbots") & SUDOERS)
async def list_total(client, message):
    cloned_bots = list(clonebotdb.find())

    if not cloned_bots:
        return await message.reply_text("**» ɴᴏ ʙᴏᴛs ᴄʟᴏɴᴇᴅ ʏᴇᴛ.**")

    await message.reply_text(f"**» ᴛᴏᴛᴀʟ ʙᴏᴛs : `{len(cloned_bots)}`**")


@app.on_message(filters.command("premiumadd") & filters.user(OWNER_ID))
async def premium_add(client, message):
    if len(message.command) < 2:
        return await message.reply_text("**» ᴜsᴀɢᴇ :** /premiumadd @username")

    username = message.command[1].replace("@","")

    bot_data = clonebotdb.find_one({"username": username})
    if not bot_data:
        return await message.reply_text("**❌ ʙᴏᴛ ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ᴄʟᴏɴᴇ ʟɪsᴛ.**")

    clonebotdb.update_one({"username": username}, {"$set":{"premium": True}})
    await message.reply_text(f"**✅ @{username} ɪs ɴᴏᴡ ᴀᴅᴅᴇᴅ ɪɴ ᴘʀᴇᴍɪᴜᴍ ʟɪsᴛ.**")


@app.on_message(filters.command("premiumremove") & filters.user(OWNER_ID))
async def premium_remove(client, message):
    if len(message.command) < 2:
        return await message.reply_text("**» ᴜsᴀɢᴇ :** `/premiumremove @username`")

    username = message.command[1].replace("@","")

    bot_data = clonebotdb.find_one({"username": username})
    if not bot_data:
        return await message.reply_text("**❌ ʙᴏᴛ ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ᴄʟᴏɴᴇ ʟɪsᴛ.**")

    clonebotdb.update_one({"username": username}, {"$set":{"premium": False}})
    await message.reply_text(f"**⚠️ @{username} ʀᴇᴍᴏᴠᴇᴅ ғʀᴏᴍ ᴘʀᴇᴍɪᴜᴍ ʟɪsᴛ.**")


def chunk_text(text, limit=4000):
    chunks = []
    while len(text) > limit:
        chunks.append(text[:limit])
        text = text[limit:]
    chunks.append(text)
    return chunks


@app.on_message(filters.command("premiumbots") & filters.user(OWNER_ID))
async def premium_bots_list(client, message):
    bots = list(clonebotdb.find({"premium": True}))

    if not bots:
        return await message.reply_text("ɴᴏ ᴘʀᴇᴍɪᴜᴍ ʙᴏᴛs.")

    txt = "💎 **ᴘʀᴇᴍɪᴜᴍ ʙᴏᴛs :**\n\n"

    for bot in bots:
        try:
            owner = await client.get_users(bot["user_id"])
            owner_name = owner.first_name
        except:
            owner_name = "ᴜɴᴋɴᴏᴡɴ"

        txt += (
            f"🤖 **ɴᴀᴍᴇ :** {bot['name']}\n"
            f"🌀 **ᴜsᴇʀɴᴀᴍᴇ :** @{bot['username']}\n"
            f"👤 **ᴏᴡɴᴇʀ :** {owner_name} (`{bot['user_id']}`)\n\n"
        )

    for part in chunk_text(txt):
        await message.reply_text(part)


@app.on_message(filters.command("cbotdata") & filters.user(OWNER_ID))
async def cloned_bot_data(client, message):
    bots = list(clonebotdb.find())

    if not bots:
        return await message.reply_text("**» ɴᴏ ᴄʟᴏɴᴇᴅ ʙᴏᴛs ғᴏᴜɴᴅ.**")

    total_bots = len(bots)

    text = "📦 **ᴀʟʟ ᴄʟᴏɴᴇᴅ ʙᴏᴛ ᴅᴀᴛᴀ :**\n\n"

    for bot in bots:
        text += (
            f"🤖 **ɴᴀᴍᴇ :** {bot['name']}\n"
            f"🌀 **ᴜsᴇʀɴᴀᴍᴇ :** @{bot['username']}\n"
            f"🔑 **ᴛᴏᴋᴇɴ :** `{bot['token']}`\n"
            f"👤 **ᴏᴡɴᴇʀ :** `{bot['user_id']}`\n"
            "**---------------------------**\n\n"
        )

    chunks = chunk_text(text)

    for part in chunks[:-1]:
        await message.reply_text(part)

    last_part = chunks[-1] + f"\n\n**» ᴛᴏᴛᴀʟ ʙᴏᴛs ᴅᴀᴛᴀ :** `{total_bots}`"
    await message.reply_text(last_part)
