import os
from dotenv import load_dotenv
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from asgiref.sync import async_to_sync
from aiogram import Bot

import logging

from transactions.models import Transaction

logger = logging.getLogger(__name__)

# Создаём экземпляр бота (используем токен из settings)
# Загружаем переменные окружения из .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")

bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode="HTML")

async def trigger_on_new_transaction(transaction: Transaction):
    """
    Асинхронная обработка новой транзакции.
    Отправляет уведомление пользователю в Telegram.
    """
    try:
        # Формируем текст уведомления
        text = (
            f"✅ <b>Новая запись добавлена</b>\n"
            f"Тип: {'Доход' if transaction.type == 'income' else 'Расход'}\n"
            f"Категория: {transaction.category}\n"
            f"Подкатегория: {transaction.subcategory or '—'}\n"
            f"Сумма: {transaction.amount} {transaction.currency}\n"
            f"Дата: {transaction.date.strftime('%d.%m.%Y')}"
        )

        # Отправляем сообщение пользователю
        if transaction.user.telegram_id:
            await bot.send_message(chat_id=transaction.user.telegram_id, text=text)
        else:
            logger.warning(f"У пользователя {transaction.user} нет telegram_id — уведомление не отправлено.")

    except Exception as e:
        logger.exception(f"Ошибка при отправке уведомления о транзакции: {e}")


@receiver(post_save, sender=Transaction)
def transaction_created(sender, instance, created, **kwargs):
    """
    Сигнал вызывается при создании новой транзакции.
    Безопасно запускает асинхронную обработку даже в sync-контексте.
    """
    if created:
        # Запускаем async-функцию в синхронном контексте
        async_to_sync(trigger_on_new_transaction)(instance)
