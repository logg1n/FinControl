from django.core.management.base import BaseCommand
from bot.main import main
import asyncio

class Command(BaseCommand):
    help = "Запуск Telegram-бота (aiogram)"

    def handle(self, *args, **options):
        asyncio.run(main())
