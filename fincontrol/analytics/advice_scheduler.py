from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from services.advice_triggers import trigger_month_start
from django.db.models import Q
from aiogram import Bot
from users.models import User
from services.advice_generator import get_ai_advice
import os
import asyncio

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

def send_weekly_advice():
    users = User.objects.filter(~Q(telegram_id=None))
    for u in users:
        advice_text = get_ai_advice(u, days=30)
        asyncio.run(bot.send_message(u.telegram_id, f"💡 Еженедельные советы:\n\n{advice_text}"))

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="Europe/Minsk")
    scheduler.add_job(send_weekly_advice, CronTrigger(day_of_week="mon", hour=9, minute=0))
    scheduler.add_job(lambda: asyncio.run(trigger_month_start()), CronTrigger(day=1, hour=9, minute=0))
    scheduler.start()
