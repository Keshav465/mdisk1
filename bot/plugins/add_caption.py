import asyncio
import datetime

# Logger
import logging

from bot.config import Config

from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.errors.exceptions.flood_420 import FloodWait
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)


logger = logging.getLogger(__name__)

lock = asyncio.Lock()

class temp(object):
    CANCEL=False

cancel_button = [[InlineKeyboardButton("Cancel 🔐", callback_data="cancel_process")]]


@Client.on_message(filters.private & filters.command("add_caption") & filters.user(Config.ADMINS))
async def add_caption_cmd(c, m: Message):

    if len(m.command) < 2:
        await m.reply_text("/add_caption channel_id")
    else:
        try:
            channel_id = int(m.command[1])
        except ValueError:
            return await m.reply("Invalid channel_id")

        buttons = [
            [
                InlineKeyboardButton(
                    "Add caption 🏕", callback_data=f"addcaption#{channel_id}"
                )
            ],
            [InlineKeyboardButton("Cancel 🔐", callback_data="cancel")],
        ]

        return await m.reply(
            text=f"Are you sure you want to add caption?\n\nChannel: {channel_id}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


@Client.on_callback_query(
    filters.regex(r"^cancel") | filters.regex(r"^addcaption") & filters.user(Config.ADMINS)
)
async def addcaption_handler(c: Client, m: CallbackQuery):

    if m.data == "cancel":
        await m.message.delete()
        return
    
    elif m.data.startswith("addcaption"):
        if lock.locked():
            return await m.answer(
                "Wait until previous process complete.", show_alert=True
            )

        channel_id = int(m.data.split("#")[1])
        try:
            txt = await c.send_message(channel_id, ".")
            _id = txt.id
            await txt.delete()

        except ChatWriteForbidden:
            return await m.message.edit("Bot is not an admin in the given channel")
        except PeerIdInvalid:
            return await m.message.edit("Given channel ID is invalid")
        except Exception as e:
            logging.exception(e)
            return await m.message.edit(e)

        start_time = datetime.datetime.now()
        txt = await m.message.edit(
            text=f"Process Started!\n\n Channel: {channel_id}\n\nTo Cancel /cancel",
        )
        logger.info(f"Processg Started for {channel_id}")

        success = 0
        fail = 0
        total = 0
        empty = 0

        total_messages = range(_id, 1, -1)
        try:
            temp.CANCEL = False
            for i in range(0, len(total_messages), 200):
                channel_posts = await c.get_messages(channel_id, total_messages[i : i + 200])
                
                async with lock:
                    for message in channel_posts:
                        message: Message
                        if temp.CANCEL:
                            break
                            
                        if message.document or message.video or message.audio:
                            try:
                                if not message.caption and not message.forward_date:
                                    if message.document:
                                        filename = message.document.file_name
                                    elif message.video:
                                        filename = message.video.file_name
                                    elif message.audio:
                                        filename = message.audio.file_name
                                
                                    caption = filename
                                    await message.edit_caption(caption)
                                    success += 1

                            except FloodWait as e:
                                logger.info(f"Sleeping for {e.value} seconds")
                                await asyncio.sleep(e.value)
                            except Exception as e:
                                logger.error(e)
                                fail += 1
                            await asyncio.sleep(1)
                        else:
                            empty += 1
                        total += 1

                        if total % 10 == 0:
                            msg = f"Processing !\n\nTotal: {total}\nSuccess: {success}\nFailed: {fail}\nEmpty: {empty}\n\nTo cancel: /cancel"
                            await txt.edit((msg))
        except Exception as e:
            logger.error(e)
            await m.message.reply(
                f"Error Occured while processing: `{e.message}`"
            )
        finally:
            end_time = datetime.datetime.now()
            await asyncio.sleep(10)
            t = end_time - start_time
            time_taken = str(datetime.timedelta(seconds=t.seconds))
            msg = f"Process Completed!\n\nTime Taken - `{time_taken}`\n\nTotal: `{total}`\nSuccess: `{success}`\nFailed: `{fail}`\nEmpty: `{empty}`"
            await txt.edit(msg)
            logger.info(f"Process Completed for {channel_id}")


@Client.on_message(filters.private & filters.command("cancel") & filters.user(Config.ADMINS))
async def stop_button(c, m):
    temp.CANCEL = True
    msg = await c.send_message(
        text="<i>Trying To Stoping.....</i>", chat_id=m.chat.id
    )

    await asyncio.sleep(5)
    await msg.edit("Process Stopped Successfully 👍")
    logger.info("Process Stopped Successfully 👍")
