import contextlib
from datetime import datetime
from pyrogram import Client, filters, types
from bot.utils import get_group_admins, get_group_info_text
from bot.database import group_db
from bot.config import Script, Config

@Client.on_callback_query(filters.regex('^validity'))
async def change_validity_cb(c, m: types.CallbackQuery):
    _, group_id, time_in_s = m.data.split("#")
    await group_db.update_group(int(group_id), {"access_days": int(time_in_s), "last_verified": datetime.now()})
    text = await get_group_info_text(c, group_id)
    await m.edit_message_text(text, reply_markup=m.message.reply_markup)
    await m.answer("Updated Successfully", show_alert=True)

    bin_text = "Your group has been updated\n\n"
    text = bin_text+text

    admins = await get_group_admins(c, group_id)

    for user_id in admins:
        with contextlib.suppress(Exception):
            await c.send_message(user_id, text)


@Client.on_callback_query(filters.regex('^removeaccess'))
async def removeaccess_cb(c, m: types.CallbackQuery):
    _, group_id = m.data.split("#")
    group_id = int(group_id)
    await group_db.update_group(group_id=group_id, value={"last_verified": datetime(1970, 1, 1), "access_days": 0})
    text = await get_group_info_text(c, group_id)
    await m.edit_message_text(text, reply_markup=m.message.reply_markup)
    await m.answer("Access has been removed", show_alert=True)

    bin_text = "Your group has been updated\n\n"
    text = bin_text+text

    admins = await get_group_admins(c, group_id)
    for user_id in admins:
        with contextlib.suppress(Exception):
            await c.send_message(user_id, text)



@Client.on_callback_query(filters.regex("about"))
async def about_cmd_handler(bot, m: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton(text="Home", callback_data="home"),
                types.InlineKeyboardButton(text="Help", callback_data="help"),
            ],
            [types.InlineKeyboardButton(text="Close", callback_data="delete")],
        ]
    )

    await m.edit_message_text(Script.ABOUT_MESSAGE, reply_markup=markup)
    return


@Client.on_callback_query(filters.regex("home"))
async def start_cb_handler(bot, m: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton(text="Help", callback_data="help"),
                types.InlineKeyboardButton(text="About", callback_data="about"),
            ],
            [types.InlineKeyboardButton(text="Close", callback_data="delete")],
        ]
    )

    await m.edit_message_text(Script.START_MESSAGE, reply_markup=markup)
    return


@Client.on_callback_query(filters.regex("help"))
async def help_cmd_handler(bot, m: types.CallbackQuery):
    s = Script.ADMIN_HELP_MESSAGE if m.from_user.id in Config.ADMINS else Script.USER_HELP_MESSAGE
    
    markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton(text="Home", callback_data="home"),
                types.InlineKeyboardButton(text="About", callback_data="about"),
            ],
            [types.InlineKeyboardButton(text="Close", callback_data="delete")],
        ]
    )

    await m.edit_message_text(s, reply_markup=markup)
    return


@Client.on_callback_query(filters.regex("delete"))
async def delete_cmd_handler(bot, m: types.CallbackQuery):
    await m.message.delete()
    return


