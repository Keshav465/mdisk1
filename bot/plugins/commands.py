# START OF FILE: bot/plugins/commands.py (FINAL FIXED VERSION)

from pyrogram import Client, filters, types, enums
import asyncio
import base64 
from datetime import datetime
from bot.config import Config, Script
from bot.plugins.reminder import main_reminder_handler
from bot.utils import get_group_info_button, get_group_info_text, group_admin_check, group_wrapper, is_bot_admin, is_int, is_premium_group, remove_link, remove_mention, schedule_delete, short_from_text, human_time
from bot.database import group_db, user_db
from bot.database.subscribers import sub_db
from bot import Bot
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid
from bot.plugins.search_logic import perform_search

@Client.on_message(filters.command("start") & filters.private, group=2)
async def start(c: Bot, m: types.Message):
    if m.forward_date:
        return
    await user_db.get_user(m.from_user.id)
    
    if len(m.command) > 1:
        payload = m.command[1]
        
        # === YEH HAI FINAL BUG FIX ===
        # file_... link ke liye: SEEDHI FILE DO, KOI VERIFICATION NAHI
        # Yeh GPlinks aur purane links, dono ke liye kaam karega.
        if payload.startswith("file_"):
            try:
                parts = payload.split("_")
                # parts[0] is "file", parts[1] is file_id, parts[2] is chat_id
                if len(parts) >= 3:
                    file_id = parts[1]
                    chat_id = parts[2]
                    
                    # Force subscribe check (optional, but good to have for new users)
                    if Config.UPDATE_CHANNEL:
                        try:
                            user = await c.get_chat_member(Config.UPDATE_CHANNEL, m.from_user.id)
                            if user.status == "kicked":
                                return await m.reply("Sorry, you are banned!")
                        except: # If user is not a member, continue and give the file anyway
                            pass
                    
                    chnl_msg = await c.get_messages(int(chat_id), int(file_id))
                    caption = chnl_msg.caption or ""
                    clean_caption = remove_mention(remove_link(caption))
                    
                    # File bhej de, bina koi sawal pooche
                    await chnl_msg.copy(m.from_user.id, caption=clean_caption)
                else:
                    await m.reply("Sorry, this link is invalid.")
            except Exception as e:
                await m.reply(f"Sorry, this link is broken or expired.\nError: {e}")
            return # Yahan par function rok do, taaki neeche ka code na chale
        # === END OF FINAL BUG FIX ===

        # Normal premium khareedne wala link
        elif payload == "subscribe":
            user_name = m.from_user.first_name
            welcome_text = f"**__Hey, {user_name},\nWelcome To Our Premium Access 😉**\n\nSelect Subscribtion Plans Here!\n\nCheck: /status __"
            PLAN_BUTTONS = [
                [types.InlineKeyboardButton(f"{days} Days Plan @ ₹{price}", callback_data=f"subscribe_{days}")] 
                for days, price in Config.SUBSCRIPTION_PLANS.items()
            ]
            await m.reply(welcome_text, reply_markup=types.InlineKeyboardMarkup(PLAN_BUTTONS))
            return

        # Deep search link
        elif payload.startswith("search_"):
            try:
                encoded_query = payload.replace("search_", "", 1)
                padding = '=' * (-len(encoded_query) % 4)
                query = base64.urlsafe_b64decode(encoded_query + padding).decode()
                sts = await m.reply(f"`Searching for: {query}...`")
                await perform_search(c, sts, query)
            except Exception as e:
                await m.reply(f"Sorry, something is wrong with this search link.\nError: {e}")
            return

    # Normal /start
    markup = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("💎 Go Premium 💎", callback_data="go_premium")],
        [
            types.InlineKeyboardButton(text="Help", callback_data="help"),
            types.InlineKeyboardButton(text="About", callback_data="about"),
        ],
        [types.InlineKeyboardButton(text="Close", callback_data="delete")],
    ])
    await m.reply_text(Script.START_MESSAGE, disable_web_page_preview=True, reply_markup=markup)

@Client.on_message(filters.command(["help", "userrights"]) & filters.private, group=2)
async def help_command(c: Client, m: types.Message):
    await m.reply_text(Script.USER_HELP_MESSAGE, disable_web_page_preview=True)

@Client.on_message(filters.command("about") & filters.private, group=2)
async def about(c: Client, m: types.Message):
    await m.reply_text(Script.ABOUT_MESSAGE, disable_web_page_preview=True)
    
@Client.on_message(filters.command('id'), group=2)
async def showid(client, message: types.Message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        await message.reply_text(f"Your Telegram ID is: `{message.chat.id}`")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        _id = f"**Chat ID**: `{message.chat.id}`\n"
        if message.from_user:
            _id += f"**Your ID**: `{message.from_user.id}`"
        elif message.sender_chat:
            _id += f"**Channel ID**: `{message.sender_chat.id}`"
        if message.reply_to_message:
            if message.reply_to_message.from_user:
                _id += f"\n**Replied User ID**: `{message.reply_to_message.from_user.id}`"
            elif message.reply_to_message.sender_chat:
                _id += f"\n**Replied Channel ID**: `{message.reply_to_message.sender_chat.id}`"
        await message.reply_text(_id)

@Client.on_message(filters.command("index") & filters.group, group=2)
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
            bot_info = await c.get_me()
            await m.reply(f"Make {bot_info.mention} admin in given channel {index_channel}")
            return
        channel_info = await c.get_chat(index_channel)
        if channel_info.type != enums.ChatType.CHANNEL:
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

@Client.on_message(filters.command("auto_delete") & filters.group, group=2)
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

@Client.on_message(filters.command("set_auto_delete") & filters.group, group=2)
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

@Client.on_message(filters.command('request') & filters.group, group=2)
async def request_cmd_handler(bot: Client, m):
    is_admin = await group_admin_check(bot, m.from_user.id, m)
    if not is_admin:
        return
    owner = (await bot.get_users(Config.OWNER_ID)).mention
    bot_info = await bot.get_me()
    try:
        await bot.send_message(m.from_user.id, f"Contact {owner} to get access")
    except Exception as e:
        btn = [[types.InlineKeyboardButton(
            "Start", url=f"https://telegram.me/{bot_info.username}")]]
        await m.reply("Start me in PM and try this command again", reply_markup=types.InlineKeyboardMarkup(btn))
        return
    await m.reply("Check Bot PM")

@Client.on_message(filters.command("premium_groups") & filters.private & filters.user(Config.OWNER_ID), group=2)
async def premium_groups(c: Client, m: types.Message):
    premium_groups = await group_db.filter_groups()
    total_premium_groups = 0
    bin_text = ""
    async for group in premium_groups:
        try:
            if await is_premium_group(group["group_id"]):
                total_premium_groups += 1
                tg_group = await c.get_chat(group["group_id"])
                bin_text += f"~ `{group['group_id']}` {tg_group.invite_link}\n"
        except Exception as e:
            print(e)
    bin_text = bin_text or "None"
    text = f"List of premium groups - Total {total_premium_groups} groups\n\n"
    await m.reply(text+bin_text)

@Client.on_message(filters.command("info") & (filters.private | filters.group), group=2)
async def info(c: Client, m: types.Message):
    try:
        if (
            m.chat.type == enums.ChatType.PRIVATE
            and len(m.command) == 1
            and m.from_user.id in Config.ADMINS
        ):
            return await m.reply_text("`/info id`")
        elif m.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            if not await group_admin_check(client=c, message=m, userid=m.from_user.id):
                return
        group_id = int(
            m.command[1]) if m.from_user.id in Config.ADMINS and m.chat.type == enums.ChatType.PRIVATE else m.chat.id
        btn = await get_group_info_button(group_id)
        text = await get_group_info_text(c, group_id)
        await m.reply(text, reply_markup=types.InlineKeyboardMarkup(btn) if m.from_user.id in Config.ADMINS and m.chat.type == enums.ChatType.PRIVATE else None)
    except ChannelInvalid:
        await m.reply("Bot is not a admin of given group")
        return
    except Exception as e:
        print(e)

@Client.on_message(filters.command("set_api") & filters.group, group=2)
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

@Client.on_message(filters.command('api') & filters.group, group=2)
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

@Client.on_message(filters.command('remove_api') & filters.group, group=2)
@group_wrapper
async def remove_api(client: Client, message):
    sts = await message.reply("Checking...")
    grp_id = message.chat.id
    await group_db.update_group(grp_id, {'shortener_api': None, "shortener_site": None})
    await sts.edit("Removed API and domain successfully. /api")

@Client.on_message(filters.command("premium_reminder") & filters.private & filters.user(Config.ADMINS), group=2)
async def reminder_handler(c: Client, m: types.Message):
    try:
        await main_reminder_handler(c, m)
    except Exception as e:
        print("Failed to execute reminder")

@Client.on_message(filters.command("admincheck") & filters.private, group=1)
async def admin_check_command(c: Client, m: types.Message):
    user_id = m.from_user.id
    if user_id not in Config.ADMINS:
        return await m.reply("You are not authorized to use this command.")
    try:
        owner_id_from_config = Config.OWNER_ID
    except Exception as e:
        owner_id_from_config = f"Error loading: {e}"
    try:
        admins_list_from_config = Config.ADMINS
    except Exception as e:
        admins_list_from_config = f"Error loading: {e}"
    debug_text = (
        f"--- 🛠️ Admin Configuration Check 🛠️ ---\n\n"
        f"👤 **Your User ID:** `{user_id}`\n"
        f"🔑 **OWNER_ID from config:** `{owner_id_from_config}`\n"
        f"📋 **ADMINS list from config:** `{admins_list_from_config}`\n\n"
        f"✅ **Status:** You are a verified admin.\n\n"
        f"----------------------------------------"
    )
    final_message = debug_text + Script.ADMIN_HELP_MESSAGE
    await m.reply_text(final_message)

@Client.on_message(filters.regex("This bot was made using @LivegramBot"))
async def dllivegram(_, m: types.Message):
    await m.delete()

@Client.on_message(filters.regex("You cannot forward someone else's messages."))
async def dlfrwdlg(_, m: types.Message):
    await m.delete()
    
@Client.on_message(filters.regex("Livegram Ads"))
async def dlllivegram(_, m: types.Message):
    await m.delete()
    
@Client.on_message(filters.command("status") & filters.private, group=2)
async def my_status(c: Client, m: types.Message):
    user_id = m.from_user.id
    subscription_details = await sub_db.is_subscribed(user_id)
    
    if subscription_details:
        expiry_date = subscription_details['expiry_date']
        time_remaining = expiry_date - datetime.now()
        
        formatted_expiry = expiry_date.strftime("%d %B %Y at %I:%M %p")
        formatted_remaining = human_time(time_remaining.total_seconds()) if time_remaining.total_seconds() > 0 else "Expired"
        
        status_message = f"""**💎 Your Premium Status 💎**

✅ You are an active subscriber.

🗓️ **Expires On:** `{formatted_expiry}`
⏳ **Time Remaining:** `{formatted_remaining}`
"""
        await m.reply_text(status_message)
    else:
        not_subscribed_message = """**❌ You Don't Have Premium Subscribtion.**

__To Enjoy Ad-free Entertainment and Get Direct Files Without Any Ads, Consider Subscribing!__
"""
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("💎 Go Premium 💎", callback_data="go_premium")]
        ])
        await m.reply_text(not_subscribed_message, reply_markup=markup)

# END OF FILE: bot/plugins/commands.py
