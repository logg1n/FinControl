import os
import asyncio
import django
from django.core.management.base import BaseCommand
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from analytics.advice_scheduler import start_scheduler
from bot.config import BOT_TOKEN
from bot.handlers import menu, add_record_flow, start_flow


class Command(BaseCommand):
    help = "Запуск Telegram-бота с планировщиком (aiogram 3.x + AsyncIOScheduler)"

    def handle(self, *args, **options):
        # Настройка Django окружения
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fincontrol.settings")
        django.setup()

        async def main():
            # Инициализация бота и диспетчера
            bot = Bot(token=BOT_TOKEN)
            dp = Dispatcher(storage=MemoryStorage())

            # Подключаем роутеры
            dp.include_router(start_flow.router)
            dp.include_router(menu.router)
            dp.include_router(add_record_flow.router)

            # Запускаем планировщик
            start_scheduler()

            self.stdout.write(self.style.SUCCESS("✅ Бот и планировщик запущены"))
            await dp.start_polling(bot)

        asyncio.run(main())
