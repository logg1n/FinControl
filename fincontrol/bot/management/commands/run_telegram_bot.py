import os
import asyncio
import django
from django.core.management.base import BaseCommand
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from analytics.advice_scheduler import start_scheduler
from bot.config import BOT_TOKEN
from bot.handlers import start, link  # твои роутеры


async def set_bot_commands(bot):
    commands = [
        BotCommand(command="start", description="Приветствие и список возможностей"),
        BotCommand(command="link", description="Привязать Telegram к аккаунту"),
        BotCommand(command="today", description="Показать расходы за сегодня"),
        BotCommand(command="week", description="Показать расходы за неделю"),
        BotCommand(command="category", description="Расходы по категории"),
        BotCommand(command="report", description="Ежедневный отчёт"),
        BotCommand(command="help", description="Справка по командам"),
    ]

class Command(BaseCommand):
    help = "Запуск Telegram-бота с планировщиком (aiogram 3.x + AsyncIOScheduler)"

    def handle(self, *args, **options):
        # Настройка Django окружения
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fincontrol.settings")
        django.setup()

        async def main():
            # Инициализация бота и диспетчера
            bot = Bot(token=BOT_TOKEN)
            dp = Dispatcher()

            # Подключаем роутеры
            dp.include_router(start.router)
            dp.include_router(link.router)

            # Запускаем планировщик
            start_scheduler()

            await bot.set_my_commands(commands)

            self.stdout.write(self.style.SUCCESS("✅ Бот и планировщик запущены"))
            await dp.start_polling(bot)

        asyncio.run(main())
