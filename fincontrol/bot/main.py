 
# fincontrol/bot/main.py
import asyncio
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fincontrol.settings")
django.setup()

from aiogram import Bot, Dispatcher
from .config import BOT_TOKEN
from .handlers import start # stats

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(link.router)  # ← добавили
#    dp.include_router(stats.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
