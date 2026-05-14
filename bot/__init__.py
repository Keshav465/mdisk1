import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from bot.bot import Bot, User
