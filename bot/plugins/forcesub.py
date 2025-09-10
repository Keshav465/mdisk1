# START OF FILE: iPMxBT-main/bot/plugins/forcesub.py

import contextlib
from pyrogram import Client, filters, types
from pyrogram.errors import UserNotParticipant
from bot.config import Config
from bot.utils import add_new_user


@Client.on_message(filters.private & filters.incoming)
async def forcesub_handler(c: Client, m: types.Message):
    await add_new_user(c, m.from_user.id, m.from_user.mention)

    # === YAHAN PAR BADA BADLAV KIYA GAYA HAI ===
    
    # Agar UPDATE_CHANNEL set nahi hai, to aage badhne do
    if not Config.UPDATE_CHANNEL:
        await m.continue_propagation()
        return

    try:
        # Check karo ki user channel ka member hai ya nahi
        user = await c.get_chat_member(Config.UPDATE_CHANNEL, m.from_user.id)
        if user.status == "kicked":
            # Agar banned hai to message bhejkar rok do
            await m.reply_text("**Hey you are banned 😜**", quote=True)
            await m.stop_propagation()
            return
    except UserNotParticipant:
        # Agar user member nahi hai, to join karne ke liye message bhejo
        invite_link = await c.create_chat_invite_link(Config.UPDATE_CHANNEL)
        buttons = [
            [
                types.InlineKeyboardButton(
                    text="Updates Channel 🔖", url=invite_link.invite_link
                )
            ]
        ]
        await m.reply_text(
            f"Hey {m.from_user.mention(style='md')} you need join My updates channel in order to use me 😉\n\n"
            "Press the Following Button to join Now 👇",
            reply_markup=types.InlineKeyboardMarkup(buttons),
            quote=True,
        )
        # YEH SABSE ZAROORI LINE HAI: Baki commands ko chalne se rok do
        await m.stop_propagation()
        return
    except Exception as e:
        print(e)
        await m.reply_text(
            f"Something Wrong. Please try again later or contact {c.owner.mention(style='md')}",
            quote=True,
        )
        # Error aane par bhi baki commands ko rok do
        await m.stop_propagation()
        return

    # Agar user ne channel join kiya hua hai, to hi baki commands ko chalne do
    await m.continue_propagation()
    # ========================================================

async def force_sub_func(c, channel_id, m):
    # Yeh function ab direct use nahi hoga, iska logic upar handler me daal diya gaya hai.
    # Isko aise hi rehne de sakte hain ya hata sakte hain, koi fark nahi padega.
    owner = c.owner
    if not channel_id:
        return True

    invite_link = await c.create_chat_invite_link(channel_id)
    try:
        user = await c.get_chat_member(channel_id, m.from_user.id)
        if user.status == "kicked":
            return await m.reply_text("**Hey you are banned 😜**", quote=True)
    except UserNotParticipant:
        buttons = [
            [
                types.InlineKeyboardButton(
                    text="Updates Channel 🔖", url=invite_link.invite_link
                )
            ]
        ]
        return await m.reply_text(
            f"Hey {m.from_user.mention(style='md')} you need join My updates channel in order to use me 😉\n\n"
            "Press the Following Button to join Now 👇",
            reply_markup=types.InlineKeyboardMarkup(buttons),
            quote=True,
        )
    except Exception as e:
        print(e)
        return await m.reply_text(
            f"Something Wrong. Please try again later or contact {owner.mention(style='md')}",
            quote=True,
        )
    return True
        
@Client.on_callback_query(filters.regex("sub_refresh"))
async def refresh_cb(c, m: types.CallbackQuery):
    owner = c.owner
    if Config.UPDATE_CHANNEL:
        try:
            user = await c.get_chat_member(Config.UPDATE_CHANNEL, m.from_user.id)
            if user.status == "kicked":
                with contextlib.suppress(Exception):
                    await m.message.edit("**Hey you are banned**")
                return
        except UserNotParticipant:
            await m.answer(
                "You have not yet joined our channel. First join and then press refresh button",
                show_alert=True,
            )
            return
        except Exception as e:
            print(e)
            await m.message.edit(
                f"Something Wrong. Please try again later or contact {owner.mention(style='md')}"
            )
            return
        
    await m.message.delete()
