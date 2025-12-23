import asyncio
from pyrogram import filters, Client
from pyrogram.errors import FloodWait

from Clonify import app
from Clonify.core.mongo import pymongodb
from Clonify.utils.decorators.language import language
from Clonify.utils.database import (
    get_served_chats_clone,
    get_served_users_clone,
)
from config import OWNER_ID, API_ID, API_HASH


clonebotdb = pymongodb.clonebotdb


@app.on_message(filters.command(["cbroadcast", "clonegcast"]))
@language
async def broadcast_message(client, message, _):

    if message.from_user.id != OWNER_ID:
        return await message.reply_text("**» ᴏɴʟʏ ᴍᴀɪɴ ʙᴏᴛ ᴏᴡɴᴇʀ ᴄᴀɴ ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴛᴏ ᴀʟʟ ʙᴏᴛꜱ.**")

    if message.reply_to_message:
        mode = "reply"
        src_chat = message.chat.id
        src_msg = message.reply_to_message.id
        text = ""
    else:
        if len(message.command) < 2:
            return await message.reply_text(
                "**» ᴜꜱᴀɢᴇ:** `/cbroadcast -user -pin ᴛᴇxᴛ`"
            )

        mode = "text"
        text = message.text.split(None, 1)[1]

        for flag in ["-pin", "-pinloud", "-user", "-nobot"]:
            text = text.replace(flag, "")

        text = text.strip()

        if not text:
            return await message.reply_text(
                "**» ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ sᴏᴍᴇ ᴛᴇxᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ.**"
            )

    await message.reply_text("🚀 **ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ ᴛᴏ ᴀʟʟ ᴄʟᴏɴᴇᴅ ʙᴏᴛꜱ…**")

    bots = list(clonebotdb.find({}))

    total_chats = 0
    total_users = 0
    total_pins = 0
    bots_done = 0
    bots_fail = 0

    DELAY = 0.05

    for bot in bots:
        token = bot["token"]
        bot_id = bot["bot_id"]

        ai = Client(
            name=f"clone_{bot_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=token,
            in_memory=True,
        )

        try:
            await ai.start()

            if "-nobot" not in message.text:
                chats = await get_served_chats_clone(bot_id)

                for chat in chats:
                    try:
                        chat_id = int(chat["chat_id"])

                        if mode == "reply":
                            m = await ai.forward_messages(chat_id, src_chat, src_msg)
                        else:
                            m = await ai.send_message(chat_id, text=text)

                        if "-pin" in message.text:
                            try:
                                await m.pin(disable_notification=True)
                                total_pins += 1
                            except:
                                pass

                        elif "-pinloud" in message.text:
                            try:
                                await m.pin(disable_notification=False)
                                total_pins += 1
                            except:
                                pass

                        total_chats += 1
                        await asyncio.sleep(DELAY)

                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except:
                        pass

            if "-user" in message.text:
                users = await get_served_users_clone(bot_id)

                for usr in users:
                    try:
                        user_id = int(usr["user_id"])

                        if mode == "reply":
                            await ai.forward_messages(user_id, src_chat, src_msg)
                        else:
                            await ai.send_message(user_id, text=text)

                        total_users += 1
                        await asyncio.sleep(DELAY)

                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except:
                        pass

            bots_done += 1
            await ai.stop()

        except:
            bots_fail += 1

    await message.reply_text(
        f"🎉 **ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇ**\n\n"
        f"👥 **ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ :** {total_users}\n"
        f"💬 **ᴛᴏᴛᴀʟ ᴄʜᴀᴛꜱ :** {total_chats}\n"
        f"📌 **ᴘɪɴɴᴇᴅ :** {total_pins}\n\n"
        f"🤖 **ᴛᴏᴛᴀʟ ʙᴏᴛꜱ :** {len(bots)}\n"
        f"✔️ **ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ ʙᴏᴛꜱ :** {bots_done}\n"
        f"❌ **ꜰᴀɪʟᴇᴅ ʙᴏᴛꜱ :** {bots_fail}"
    )
