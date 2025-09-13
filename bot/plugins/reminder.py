import asyncio
import datetime
import logging
import random
import string
import time
import traceback

import aiofiles
import aiofiles.os
from bot.database import group_db
from bot.utils import human_time, get_group_admins
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, PeerIdInvalid
from pyrogram.types import Message

from bot.config import Config, Script


broadcast_ids = {}



async def send_msg(group_id, msg, client: Client):
    try:
        admins = await get_group_admins(client, group_id)
        for user_id in admins:
            await client.send_message(user_id, msg)
        return 200, None
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return send_msg(group_id, msg, client)
    except PeerIdInvalid:
        return 400, f"{group_id} : group id invalid\n"
    except Exception as e:
        return 500, f"{group_id} : {traceback.format_exc()}\n"


async def main_reminder_handler(client: Client, m: Message):
    all_groups = await group_db.filter_groups()

    while True:
        broadcast_id = "".join([random.choice(string.ascii_letters) for _ in range(3)])
        if not broadcast_ids.get(broadcast_id):
            break
    out = await m.reply_text(
        text="Reminder Message Started Sending to groups! You will be notified with log file when all the groups are notified."
    )

    start_time = time.time()
    total_groups = 0
    done = 0
    failed = 0
    success = 0
    broadcast_ids[broadcast_id] = dict(
        total=total_groups, current=done, failed=failed, success=success
    )
    owner_mention = (await client.get_users(Config.OWNER_ID)).mention
    async with aiofiles.open("reminder.txt", "w") as broadcast_log_file:
        async for group in all_groups:
            expiry_date_str, time_remaining = await group_db.expiry_date(
                group["group_id"]
            )

            if time_remaining <= 172800:
                subscription_date = group["last_verified"]
                if not await group_db.is_group_verified(group["group_id"]):
                    subscription_date = expiry_date_str = time_remaining = "Expired"

                tg_group = await client.get_chat(group["group_id"])

                text = Script.SUBSCRIPTION_REMINDER_MESSAGE.format(owner=owner_mention)

                text += Script.GROUP_INFO_TEXT.format(
                    group_id=group["group_id"],
                    group_link=tg_group.invite_link,
                    subscription_date=subscription_date,
                    expiry_date=expiry_date_str,
                    time_remaining=human_time(time_remaining)
                    if type(time_remaining) is int
                    else time_remaining,
                    shortener_api=group["shortener_api"],
                    shortener_site=group["shortener_site"],
                    auto_delete=group["auto_delete"],
                    auto_delete_time=group["auto_delete_time"],
                    fsub=group["fsub"],
                    fsub_channel=group["fsub_channel"],
                    index_channel=group["index_channel"],
                )

                sts, msg = await send_msg(int(group["group_id"]), text, client=client)
                total_groups += 1
                if msg is not None:
                    await broadcast_log_file.write(msg)
                if sts == 200:
                    success += 1
                else:
                    failed += 1
                done += 1
                if broadcast_ids.get(broadcast_id) is None:
                    break
                else:
                    broadcast_ids[broadcast_id].update(
                        dict(current=done, failed=failed, success=success)
                    )

    if broadcast_ids.get(broadcast_id):
        broadcast_ids.pop(broadcast_id)
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await asyncio.sleep(3)
    await out.delete()
    if failed == 0:
        await m.reply_text(
            text=f"Reminder Notification completed in `{completed_in}`\n\nTotal groups {total_groups}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True,
        )

    else:
        await m.reply_document(
            document="broadcast.txt",
            caption=f"Reminder Notification completed in `{completed_in}`\n\nTotal groups {total_groups}.\nTotal done {done}, {success} success and {failed} failed.",
            quote=True,
        )

    await aiofiles.os.remove("reminder.txt")
