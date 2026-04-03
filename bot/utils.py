import asyncio
import functools
import re
import random
from pyrogram import enums, types, Client
from bot import Bot
from bot.config import Config, Script
from bot.database import user_db, group_db
from telegraph.aio import Telegraph
from collections import OrderedDict
from shortzy import Shortzy
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
import aiohttp

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

INTERVALS = OrderedDict([
    ('millennium', 31536000000),  # 60 * 60 * 24 * 365 * 1000
    ('century', 3153600000),      # 60 * 60 * 24 * 365 * 100
    ('year', 31536000),           # 60 * 60 * 24 * 365
    # 60 * 60 * 24 * 30.41 (assuming 30.41 days in a month)
    ('month', 2627424),
    ('week', 604800),             # 60 * 60 * 24 * 7
    ('day', 86400),               # 60 * 60 * 24
    ('hour', 3600),               # 60 * 60
    ('minute', 60),
    ('second', 1)
])


async def filter_chat(c: Bot, query, chat_id_list=Config.DATABASE_CHANNEL, offset=0, filter: enums.MessagesFilter = enums.MessagesFilter.EMPTY, num_results=Config.LIMIT):
    search_results = []
    raw_search_results = []
    query_list = query.split()
    results = []

    for q in query_list:
        for chat_id in chat_id_list:
            async for message in c.USER.search_messages(chat_id, query=q, offset=offset, filter=filter, limit=Config.LIMIT):
                if message.text or message.caption:
                    text = message.text or message.caption
                    file_name = text.splitlines()[0].lower()
                    ratio = fuzz.token_set_ratio(query, file_name)
                    results.append((message, ratio))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results[:num_results]]


async def add_new_user(c, user_id, mention):
    is_user = await user_db.is_user_exist(user_id)
    if not is_user:
        await user_db.get_user(user_id)
        await c.send_message(Config.LOG_CHANNEL, f"#NewUser\n\nUser ID: `{user_id}`\nName: {mention}")


async def create_telegraph_post(title, content):
    telegraph = Telegraph(random.choice(Config.TELEGRAPH_ACCESS_TOKEN))
    response = await telegraph.create_page(
        title,
        html_content=content,
    )
    return response['url']


def remove_link(text):
    pattern = r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)'
    return re.sub(
        pattern, "", text
    )


def remove_mention(text):
    pattern = r'@(\w+)'
    return re.sub(
        pattern,
        f"@{Config.USERNAME}",
        text,
    )


async def group_admin_check(client, userid, message):

    if not userid:
        return
    if userid in Config.ADMINS:
        return True

    grp_id = message.chat.id
    st = await client.get_chat_member(grp_id, userid)
    if st.status not in [
        enums.ChatMemberStatus.ADMINISTRATOR,
        enums.ChatMemberStatus.OWNER,
    ]:
        return

    return True


def is_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


async def is_bot_admin(c, channel_id):
    if channel_id:
        try:
            await c.create_chat_invite_link(channel_id)
            return True
        except Exception as e:
            return
    return True


async def is_premium_group(group_id):
    return bool(await group_db.is_group_verified(group_id))


def group_wrapper(func):
    @functools.wraps(func)
    async def wrapper(client, message):
        user_id = getattr(message.from_user, "id", None)
        chat_id = getattr(message.chat, "id", None)
        is_admin = await group_admin_check(client, user_id, message)

        if not is_admin:
            return

        if not await is_premium_group(chat_id):
            await message.reply(Script.NO_SUBSCRIPTION_TEXT)
            return

        return await func(client, message)

    return wrapper


async def get_group_info_button(group_id: int):
    btn = [[types.InlineKeyboardButton(
        text=f"Add {human_time(time_in_s)}", callback_data=f'validity#{group_id}#{time_in_s}')] for time_in_s in Config.VALIDITY]
    btn.append([types.InlineKeyboardButton("Remove access",
               callback_data=f"removeaccess#{group_id}")])
    btn.append([types.InlineKeyboardButton("Close", callback_data="delete")])
    return btn


async def get_group_info_text(client, group_id: int):
    txt = Script.GROUP_INFO_TEXT

    group = await group_db.get_group(group_id)
    expiry_date_str, time_remaining = await group_db.expiry_date(group_id)
    subscription_date = group['last_verified']

    if not await group_db.is_group_verified(group_id):
        subscription_date = expiry_date_str = time_remaining = "Expired"

    tg_group = await client.get_chat(group_id)
    return txt.format(
        group_id=group_id,
        group_link=tg_group.invite_link,
        subscription_date=subscription_date,
        expiry_date=expiry_date_str,
        time_remaining=human_time(time_remaining)
        if type(time_remaining) is int
        else time_remaining,
        shortener_api=group['shortener_api'],
        shortener_site=group['shortener_site'],
        auto_delete=group['auto_delete'],
        auto_delete_time=group['auto_delete_time'],
        index_channel=group['index_channel']
    )


def human_time(seconds, decimals=1):
    '''Human-readable time from seconds (ie. 5 days and 2 hours).

    Examples:
        >>> human_time(15)
        '15 seconds'
        >>> human_time(3600)
        '1 hour'
        >>> human_time(3720)
        '1 hour and 2 minutes'
        >>> human_time(266400)
        '3 days and 2 hours'
        >>> human_time(-1.5)
        '-1.5 seconds'
        >>> human_time(0)
        '0 seconds'
        >>> human_time(0.1)
        '100 milliseconds'
        >>> human_time(1)
        '1 second'
        >>> human_time(1.234, 2)
        '1.23 seconds'

    Args:
        seconds (int or float): Duration in seconds.
        decimals (int): Number of decimals.

    Returns:
        str: Human-readable time.
    '''
    if seconds < 0 or seconds != 0 and not 0 < seconds < 1 and 1 < seconds < INTERVALS['minute']:
        input_is_int = isinstance(seconds, int)
        return f'{str(seconds if input_is_int else round(seconds, decimals))} seconds'
    elif seconds == 0:
        return '0 seconds'
    elif 0 < seconds < 1:
        # Return in milliseconds.
        ms = int(seconds * 1000)
        return '%i millisecond%s' % (ms, 's' if ms != 1 else '')
    res = []
    for interval, count in INTERVALS.items():
        quotient, remainder = divmod(seconds, count)
        if quotient >= 1:
            seconds = remainder
            if quotient > 1:
                # Plurals.
                if interval == 'millennium':
                    interval = 'millennia'
                elif interval == 'century':
                    interval = 'centuries'
                else:
                    interval += 's'
            res.append('%i %s' % (int(quotient), interval))
        if remainder == 0:
            break

    return f'{res[0]} and {res[1]}' if len(res) >= 2 else res[0]


async def get_group_admins(client: Client, group_id):
    administrators = []
    async for m in client.get_chat_members(group_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
        m: types.ChatMember
        None if m.user.is_bot else administrators.append(m.user.id)

    return administrators


async def auto_delete_func(m, auto_delete_time):
    if m.document or m.video:
        return
        
    await asyncio.sleep(auto_delete_time)
    await m.delete()


async def short_link(api_key, base_site, link, from_text=None):
    # return "testlink"
    if bool(api_key and base_site):
        shortzy = Shortzy(api_key, base_site)
        return await shortzy.convert(link, silently_fail=True)
    else:
        return link


async def short_from_text(api_key, base_site, text):
      
    if bool(api_key and base_site):
        shortzy = Shortzy(api_key, base_site)

        return await shortzy.convert_from_text(text, silently_fail=True)
    else:
        return text

