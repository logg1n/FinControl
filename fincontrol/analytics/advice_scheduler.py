import os
import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from django.db.models import Sum, Q
from django.core.cache import cache
from asgiref.sync import sync_to_async

from analytics.advice_triggers import trigger_month_start
from analytics.advice_generator import get_ai_advice
from transactions.models import Transaction
from users.models import User

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

# ===== ORM helpers =====
@sync_to_async
def get_all_telegram_users():
    return list(User.objects.filter(~Q(telegram_id=None)))

@sync_to_async
def get_user_expenses_for_month(user, month_start):
    return list(
        Transaction.objects
        .filter(user=user, date__gte=month_start, amount__lt=0)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("total")
    )

# ===== Jobs =====
async def generate_daily_ai_tip():
    """Генерация AI‑совета дня и кэширование до полуночи."""
    tip = get_ai_advice(None, days=1)  # общий совет
    now = datetime.datetime.now()
    midnight = datetime.datetime.combine(
        now.date() + datetime.timedelta(days=1),
        datetime.time.min
    )
    seconds_until_midnight = int((midnight - now).total_seconds())
    cache.set("ai_tip_of_the_day", tip, timeout=seconds_until_midnight)
    print(f"💡 Совет дня сгенерирован и закэширован: {tip}")

async def send_weekly_advice():
    """Еженедельная персонализированная рассылка в Telegram."""
    today = datetime.date.today()
    month_start = today.replace(day=1)

    users = await get_all_telegram_users()
    for u in users:
        expenses = await get_user_expenses_for_month(u, month_start)

        if not expenses:
            await bot.send_message(u.telegram_id, "💡 В этом месяце у вас пока нет расходов.")
            continue

        summary_lines = [
            f"• {e['category__name']}: {abs(e['total']):.2f} BYN"
            for e in expenses
        ]
        summary_text = "\n".join(summary_lines)

        ai_prompt = (
            "Проанализируй эти расходы по категориям и дай 1–2 совета, "
            "как можно оптимизировать бюджет:\n\n" + summary_text
        )
        ai_tip = get_ai_advice(u, prompt_override=ai_prompt)

        await bot.send_message(
            u.telegram_id,
            f"📊 *Ваши расходы за {today.strftime('%B %Y')}*\n\n"
            f"{summary_text}\n\n"
            f"💡 *Рекомендация:*\n{ai_tip}",
            parse_mode="Markdown"
        )

async def run_month_start_trigger():
    await trigger_month_start()

def start_scheduler():
    scheduler = AsyncIOScheduler(timezone="Europe/Minsk")
    scheduler.add_job(generate_daily_ai_tip, CronTrigger(hour=0, minute=0))
    scheduler.add_job(send_weekly_advice, CronTrigger(day_of_week="mon", hour=9, minute=0))
    scheduler.add_job(run_month_start_trigger, CronTrigger(day=1, hour=9, minute=0))
    scheduler.start()
    print("✅ Планировщик запущен: AI‑совет дня + рассылка + триггеры")
