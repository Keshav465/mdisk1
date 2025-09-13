from pyrogram import Client, filters, types, enums
from bot.config import Config, Script
from bot.plugins.reminder import main_reminder_handler
from bot.utils import get_group_info_button, get_group_info_text, group_admin_check, group_wrapper, is_bot_admin, is_int, is_premium_group, remove_link, remove_mention
from bot.database import group_db
from bot import Bot
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid


@Client.on_message(filters.command("start") & (filters.private | filters.group) & filters.incoming)
async def start(c: Bot, m: types.Message):
    
    if len(m.command) == 2:
        if "help" in m.command:
            s = Script.ADMIN_HELP_MESSAGE if m.from_user.id in Config.ADMINS else Script.USER_HELP_MESSAGE
            await m.reply_text(
                s, disable_web_page_preview=True
            )
            return
        else:
            _, file_id, chat_id = m.command[1].split("_")

            chnl_msg = await c.get_messages(int(chat_id), int(file_id))
            caption = chnl_msg.caption
            caption = remove_mention(remove_link(caption))
            btn = [[types.InlineKeyboardButton(
                text="How to Download?", url=Config.FILE_HOW_TO_DOWNLOAD_LINK)]]

            reply_markup = types.InlineKeyboardMarkup(
                btn) if Config.FILE_HOW_TO_DOWNLOAD_LINK else None
            await chnl_msg.copy(m.from_user.id, caption, reply_markup=reply_markup)
        return
        
    markup = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton(text="Help", callback_data="help"),
                types.InlineKeyboardButton(text="About", callback_data="about"),
            ],
            [types.InlineKeyboardButton(text="Close", callback_data="delete")],
        ]
    )
    
    await m.reply_text(
        Script.START_MESSAGE, disable_web_page_preview=True, reply_markup=markup
    )


@Client.on_message(filters.command("help") & filters.private & filters.incoming)
async def help(c: Client, m: types.Message):
    s = Script.ADMIN_HELP_MESSAGE if m.from_user.id in Config.ADMINS else Script.USER_HELP_MESSAGE
    await m.reply_text(
        s, disable_web_page_preview=True
    )


@Client.on_message(filters.command("help") & filters.group & filters.incoming)
async def help_group(c: Client, m: types.Message):
    text = "Contact me in PM for help!"
    btn = [[types.InlineKeyboardButton(
        text="Click me for help", url=f"https://t.me/{c.username.replace('@', '')}?start=help")]]
    await m.reply_text(
        text, disable_web_page_preview=True,
        reply_markup=types.InlineKeyboardMarkup(btn)
    )


@Client.on_message(filters.command("about") & filters.private & filters.incoming)
async def about(c: Client, m: types.Message):

    await m.reply_text(
        Script.ABOUT_MESSAGE, disable_web_page_preview=True
    )


@Client.on_message(filters.command("index") & filters.group & filters.incoming)
@group_wrapper
async def index(c: Bot, m: types.Message):
    grp_id = m.chat.id
    group_info = await group_db.get_group(grp_id)
    text = Script.INDEX_TEXT.format(group_info["index_channel"])
    if len(m.command) != 2:
        await m.reply(text)
        return

    elif is_int(m.command[1]):
        index_channel = int(m.command[1])

        bot_admin = await is_bot_admin(c, index_channel)
        if not bot_admin:
            await m.reply(f"Make {c.username} admin in given channel {index_channel}")
            return

        channel_info = await c.get_chat(index_channel)

        if not channel_info.type.CHANNEL:
            await m.reply("This is not a channel")
            return

        if not channel_info.username:
            await m.reply("This is a private channel, Index any public channel")
            return

        invite_link = await c.export_chat_invite_link(index_channel)

        try:
            await c.USER.join_chat(invite_link)
        except Exception as e:
            print(e)

        await group_db.update_group(grp_id, {"index_channel": index_channel})
        photo = Config.TELEGRAM_JPEG
        text = f"<b>Name:</b> {channel_info.title}\n<b>Username:</b> @{channel_info.username}\n<b>Members:</b> {channel_info.members_count}\n<b>Description:</b> {channel_info.description}\n<b>Is channel verified:</b> {'Yes' if channel_info.is_verified else 'No'}"
        await m.reply_photo(photo, caption=f"Indexed Successfully\n\n{text}")
        return
    else:
        await m.reply("Channel ID invalid.")

    return


@Client.on_message(filters.command("auto_delete") & filters.group & filters.incoming)
@group_wrapper
async def auto_delete(c: Client, m: types.Message):
    grp_id = m.chat.id
    group_info = await group_db.get_group(grp_id)
    text = Script.AUTO_DELETE_TEXT.format(group_info["auto_delete"])
    if len(m.command) != 2:
        await m.reply(text)
        return

    elif m.command[1] in ["True", "False"]:
        fsub = m.command[1] == "True"
        await group_db.update_group(grp_id, {"auto_delete": fsub})
        await m.reply("Updated Successfully. /auto_delete")
        return
    else:
        await m.reply(text)
    return


@Client.on_message(filters.command("set_auto_delete") & filters.group & filters.incoming)
@group_wrapper
async def set_auto_delete(c: Client, m: types.Message):
    grp_id = m.chat.id
    group_info = await group_db.get_group(grp_id)
    text = Script.SET_AUTO_DELETE_TEXT.format(group_info["auto_delete_time"])
    if len(m.command) != 2:
        await m.reply(text)
        return

    elif is_int(m.command[1]):
        auto_delete_time = int(m.command[1])
        await group_db.update_group(grp_id, {"auto_delete_time": auto_delete_time})
        await m.reply("Updated Successfully. /set_auto_delete")
        return
    else:
        await m.reply("Time is invalid.")

    return


@Client.on_message(filters.command('request') & filters.group)
async def request_cmd_handler(bot: Client, m):

    is_admin = await group_admin_check(bot, m.from_user.id, m)

    if not is_admin:
        return

    owner = (await bot.get_users(Config.OWNER_ID)).mention

    try:
        await bot.send_message(m.from_user.id, f"Contact {owner} to get access")
    except Exception as e:
        btn = [[types.InlineKeyboardButton(
            "Start", url=f"https://telegram.me/{bot.username.replace('@','')}")]]
        await m.reply("Start me in PM and try this command again", reply_markup=types.InlineKeyboardMarkup(btn))
        return

    await m.reply("Check Bot PM")


@Client.on_message(filters.command("premium_groups") & filters.private & filters.incoming & filters.user(Config.OWNER_ID))
async def premium_groups(c: Client, m: types.Message):
    premium_groups = await group_db.filter_groups()
    total_premium_groups = 0
    bin_text = ""
    async for group in premium_groups:
        try:
            if await is_premium_group(group["group_id"]):
                total_premium_groups += 1
                tg_group = await c.get_chat(group["group_id"])
                bin_text += "~ `{group_id}` {group_link}\n".format(
                    group_id=group["group_id"], group_link=tg_group.invite_link)
        except Exception as e:
            print(e)

    bin_text = bin_text or "None"
    text = f"List of premium groups - Total {total_premium_groups} groups\n\n"
    await m.reply(text+bin_text)


@Client.on_message(filters.command("info") & (filters.private | filters.group) & filters.incoming)
async def info(c: Client, m: types.Message):
    try:
        if (
            m.chat.type == enums.chat_type.ChatType.PRIVATE
            and len(m.command) == 1
            and m.from_user.id in Config.ADMINS
        ):
            return await m.reply_text("`/info id`")

        elif m.chat.type in [enums.chat_type.ChatType.GROUP, enums.chat_type.ChatType.SUPERGROUP]:
            if not await group_admin_check(client=c, message=m, userid=m.from_user.id):
                return

        group_id = int(
            m.command[1]) if m.from_user.id in Config.ADMINS and m.chat.type == enums.chat_type.ChatType.PRIVATE else m.chat.id

        btn = await get_group_info_button(group_id)
        text = await get_group_info_text(c, group_id)
        await m.reply(text, reply_markup=types.InlineKeyboardMarkup(btn) if m.from_user.id in Config.ADMINS and m.chat.type == enums.chat_type.ChatType.PRIVATE else None)

    except ChannelInvalid:
        await m.reply("Bot is not a admin of given group")
        return

    except Exception as e:
        print(e)


@Client.on_message(filters.command("set_api") & filters.group & filters.incoming)
@group_wrapper
async def set_api(c: Client, m: types.Message):
    grp_id = m.chat.id
    sts = await m.reply("Checking api")
    if len(m.command) != 3:
        return await sts.edit("No Input!!\n\n`/set_api domain api`\n\nFor example: /set_api shareus.in 1aab74171e9891abd0ba7xxx")

    site = m.command[1]
    api = m.command[2]

    await group_db.update_group(grp_id, {'shortener_api': api, "shortener_site": site})
    return await sts.edit("API has been set")


@Client.on_message(filters.command('api') & filters.group)
@group_wrapper
async def api(client: Client, message):
    grp_id = message.chat.id
    sts = await message.reply("Checking...")
    group_info = await group_db.get_group(grp_id)

    text = Script.API_COMMAND_TEXT.format(
        api=group_info["shortener_api"],
        shortener_site=group_info["shortener_site"]
    )
    await sts.edit(text)


@Client.on_message(filters.command('remove_api') & filters.group)
@group_wrapper
async def remove_api(client: Client, message):
    sts = await message.reply("Checking...")
    grp_id = message.chat.id
    await group_db.update_group(grp_id, {'shortener_api': None, "shortener_site": None})
    await sts.edit("Removed API and domain successfully. /api")


@Client.on_message(filters.command('id'))
async def showid(client, message: types.Message):

    def get_file_id(msg: types.Message):
        if msg.media:
            for message_type in (
                "photo",
                "animation",
                "audio",
                "document",
                "video",
                "video_note",
                "voice",
                "sticker"
            ):
                obj = getattr(msg, message_type)
                if obj:
                    setattr(obj, "message_type", message_type)
                    return

    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        user_id = message.chat.id
        first = message.from_user.first_name or None
        last = message.from_user.last_name or None
        username = message.from_user.username or None
        dc_id = message.from_user.dc_id or None
        text = f"<b>➲ First Name:</b> {first}\n<b>➲ Last Name:</b> {last}\n<b>➲ Username:</b> {username}\n<b>➲ Telegram ID:</b> <code>{user_id}</code>\n<b>➲ Data Centre:</b> <code>{dc_id}</code>"

        await message.reply_text(
            text,
            quote=True
        )

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        _id = ""
        _id += (
            "<b>➲ Chat ID</b>: "
            f"<code>{message.chat.id}</code>\n"
        )
        if message.reply_to_message:
            _id += (
                "<b>➲ User ID</b>: "
                f"<code>{message.from_user.id if message.from_user else 'Anonymous'}</code>\n"
                "<b>➲ Replied User ID</b>: "
                f"<code>{message.reply_to_message.from_user.id if message.reply_to_message.from_user else 'Anonymous'}</code>\n"
            )
            file_info = get_file_id(message.reply_to_message)
        else:
            _id += (
                "<b>➲ User ID</b>: "
                f"<code>{message.from_user.id if message.from_user else 'Anonymous'}</code>\n"
            )
            file_info = get_file_id(message)
        if file_info:
            _id += (
                f"<b>{file_info.message_type}</b>: "
                f"<code>{file_info.file_id}</code>\n"
            )
        await message.reply_text(
            _id,
            quote=True
        )


@Client.on_message(
    filters.command("premium_reminder") & filters.private & filters.user(
        Config.ADMINS)
)
async def reminder_handler(c: Client, m: types.Message):
    try:
        await main_reminder_handler(c, m)
    except Exception as e:
        print("Failed to execute reminder")

@Client.on_message(filters.regex("This bot was made using @LivegramBot"))
async def dllivegram(_, m: types.Message):
    await m.delete()

@Client.on_message(filters.regex("You cannot forward someone else's messages."))
async def dlfrwdlg(_, m: types.Message):
    await m.delete()
    
@Client.on_message(filters.regex("Livegram Ads"))
async def dlllivegram(_, m: types.Message):
    await m.delete()