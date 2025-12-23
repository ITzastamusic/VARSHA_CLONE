import asyncio
from Clonify import app
from pyrogram import filters
from config import OWNER_ID, LOGGER_ID
from Clonify.misc import SUDOERS
from Clonify.utils.database import get_assistant


@app.on_message(filters.command(["leaveall", f"leaveall@{app.username}"]) & SUDOERS)
async def leave_all(client, message):
    if message.from_user.id != OWNER_ID:
        return

    left = 0
    failed = 0
    lol = await message.reply("🔄 **ᴜsᴇʀʙᴏᴛ** ʟᴇᴀᴠɪɴɢ ᴀʟʟ ᴄʜᴀᴛs !")
    try:
        userbot = await get_assistant(message.chat.id)
        async for dialog in userbot.get_dialogs():
            if dialog.chat.id == LOGGER_ID:
                continue
            try:
                await userbot.leave_chat(dialog.chat.id)
                left += 1
                await lol.edit(
                    f"**ᴜsᴇʀʙᴏᴛ ʟᴇᴀᴠɪɴɢ ᴀʟʟ ɢʀᴏᴜᴘ...**\n\n**ʟᴇғᴛ:** {left} ᴄʜᴀᴛs.\n**ғᴀɪʟᴇᴅ:** {failed} ᴄʜᴀᴛs."
                )
            except BaseException:
                failed += 1
                await lol.edit(
                    f"**ᴜsᴇʀʙᴏᴛ ʟᴇᴀᴠɪɴɢ...**\n\n**ʟᴇғᴛ:** {left} chats.\n**ғᴀɪʟᴇᴅ:** {failed} chats."
                )
            await asyncio.sleep(3)
    finally:
        await app.send_message(
            message.chat.id,
            f"**✅ ʟᴇғᴛ ғʀᴏᴍ:* {left} chats.\n**❌ ғᴀɪʟᴇᴅ ɪɴ:** {failed} chats.",
        )
