import os
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from aiogram import Bot
from users.models import User
from transactions.models import Transaction
from services.advice_generator import get_ai_advice

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

# Хранилище времени последней отправки для ограничения частоты
_last_sent = {}

def _can_send(user_id, cooldown_hours=24):
    """Проверка, можно ли отправить совет (не чаще cooldown_hours)."""
    now = timezone.now()
    last_time = _last_sent.get(user_id)
    if not last_time or (now - last_time) > timedelta(hours=cooldown_hours):
        _last_sent[user_id] = now
        return True
    return False

async def trigger_on_new_transaction(transaction):
    """Отправка совета при добавлении транзакции (с ограничением частоты)."""
    user = transaction.user
    if not user.telegram_id:
        return
    if not _can_send(user.id):
        return
    advice_text = get_ai_advice(user, days=30)
    await bot.send_message(user.telegram_id, f"💡 Совет по вашим последним тратам:\n\n{advice_text}")

async def trigger_month_start():
    """Отправка итогов и плана в начале месяца."""
    today = timezone.now().date()
    if today.day != 1:
        return
    for user in User.objects.exclude(telegram_id=None):
        advice_text = get_ai_advice(user, days=30)
        await bot.send_message(user.telegram_id, f"📅 Итоги месяца и план:\n\n{advice_text}")

async def trigger_anomaly(transaction, threshold=1.5):
    """Отправка уведомления при аномальных тратах."""
    if transaction.type != "expense":
        return
    user = transaction.user
    if not user.telegram_id:
        return

    # Средний расход за последние 30 дней
    start_date = timezone.now().date() - timedelta(days=30)
    avg_expense = (
        Transaction.objects
        .filter(user=user, type="expense", date__gte=start_date)
        .aggregate(total=Sum("amount"))["total"] or 0
    )
    count = Transaction.objects.filter(user=user, type="expense", date__gte=start_date).count() or 1
    avg_per_tx = avg_expense / count

    if transaction.amount > avg_per_tx * threshold:
        advice_text = get_ai_advice(user, days=30)
        await bot.send_message(
            user.telegram_id,
            f"⚠️ Аномальная трата {transaction.amount} {transaction.currency}!\n\n{advice_text}"
        )
