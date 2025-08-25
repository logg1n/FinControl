# users/management/commands/test_advice_notifications.py
import os
import asyncio
import random
from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction as db_tx
from aiogram import Bot

from transactions.models import Transaction
from services.advice_generator import get_ai_advice
from services import advice_triggers as trg  # trigger_on_new_transaction, trigger_anomaly

class Command(BaseCommand):
    help = "Тестовая проверка всех уведомлений ИИ-помощника (еженедельная, после добавления, начало месяца, аномалия)."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="Логин пользователя")
        parser.add_argument("--telegram-id", required=True, type=int, help="Telegram ID пользователя")
        parser.add_argument("--create-user", action="store_true", help="Создать пользователя, если не найден")
        parser.add_argument("--days", type=int, default=30, help="Глубина анализа (дни)")
        parser.add_argument("--seed", type=int, default=42, help="Seed для воспроизводимости")
        parser.add_argument("--currency", default="RUB", help="Валюта для тестовых транзакций")

    def handle(self, *args, **opts):
        random.seed(opts["seed"])

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            raise CommandError("TELEGRAM_BOT_TOKEN не задан в окружении")

        if not os.getenv("OPENAI_API_KEY"):
            self.stderr.write(self.style.WARNING("OPENAI_API_KEY не задан — get_ai_advice может упасть."))

        username = opts["username"]
        telegram_id = opts["telegram_id"]
        days = opts["days"]
        currency = opts["currency"]

        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if not user and not opts["create_user"]:
            raise CommandError(f"Пользователь '{username}' не найден. Добавь --create-user для автосоздания.")

        if not user:
            user = User.objects.create_user(username=username, password="demo12345", email=f"{username}@example.com")
            for k, v in {"full_name": "Тест Пользователь", "gender": "male", "age": 30, "position": "QA"}.items():
                if hasattr(user, k):
                    setattr(user, k, v)
            self.stdout.write(self.style.SUCCESS(f"Создан пользователь '{username}' с паролем demo12345"))

        # Привяжем Telegram
        if getattr(user, "telegram_id", None) != telegram_id:
            if hasattr(user, "telegram_id"):
                user.telegram_id = telegram_id
                user.save(update_fields=["telegram_id"])
                self.stdout.write(self.style.SUCCESS(f"Привязан telegram_id={telegram_id}"))
            else:
                self.stdout.write(self.style.WARNING("У модели User нет поля telegram_id — уведомления не отправятся."))

        # 1) Базовая история расходов за последние N дней (для средних и аномалий)
        today = timezone.now().date()
        start_date = today - timedelta(days=days)

        # Создаём умеренную базу, если у пользователя мало расходов в периоде
        existing = Transaction.objects.filter(user=user, type="expense", date__gte=start_date).count()
        to_create = max(0, 12 - existing)  # цель — иметь ~12 транзакций для среднего
        categories = ["Еда", "Транспорт", "Коммуналка", "Здоровье", "Одежда", "Развлечения"]
        payment_methods = ["card", "cash", "bank"]

        if to_create:
            with db_tx.atomic():
                for _ in range(to_create):
                    amt = Decimal(random.randint(300, 2500))
                    Transaction.objects.create(
                        user=user,
                        amount=amt,
                        date=start_date + timedelta(days=random.randint(0, days)),
                        type="expense",
                        payment_method=random.choice(payment_methods),
                        currency=currency,
                        tag="baseline",
                        category=random.choice(categories),
                        subcategory=""
                    )
            self.stdout.write(self.style.SUCCESS(f"Создано базовых расходов: {to_create}"))

        # Подготовим бота для прямых отправок
        bot = Bot(token=bot_token)

        # 2) Тест еженедельной рассылки: отправим совет напрямую
        try:
            advice_weekly = get_ai_advice(user, days=days)
            asyncio.run(bot.send_message(chat_id=telegram_id, text=f"💡 Тест еженедельной рассылки:\n\n{advice_weekly}"))
            self.stdout.write(self.style.SUCCESS("Еженедельная рассылка — OK"))
        except Exception as e:
            self.stderr.write(f"[weekly] Ошибка: {e}")

        # 3) Тест триггера «после добавления транзакции» (обходит cooldown, т.к. вызывает напрямую)
        try:
            new_tx = Transaction.objects.create(
                user=user,
                amount=Decimal("1500.00"),
                date=today,
                type="expense",
                payment_method="card",
                currency=currency,
                tag="после-добавления",
                category="Еда",
                subcategory=""
            )
            asyncio.run(trg.trigger_on_new_transaction(new_tx))
            self.stdout.write(self.style.SUCCESS("Триггер после добавления — OK"))
        except Exception as e:
            self.stderr.write(f"[on_new_tx] Ошибка: {e}")

        # 4) Тест «начало месяца»: эмулируем вручную (без проверки calendar day)
        try:
            advice_month = get_ai_advice(user, days=days)
            asyncio.run(bot.send_message(chat_id=telegram_id, text=f"📅 Тест начала месяца — итоги и план:\n\n{advice_month}"))
            self.stdout.write(self.style.SUCCESS("Начало месяца — OK (эмуляция)"))
        except Exception as e:
            self.stderr.write(f"[month_start] Ошибка: {e}")

        # 5) Тест «аномальная трата»: сумма сильно больше среднего
        try:
            huge_tx = Transaction.objects.create(
                user=user,
                amount=Decimal("50000.00"),
                date=today,
                type="expense",
                payment_method="card",
                currency=currency,
                tag="аномалия",
                category="Развлечения",
                subcategory=""
            )
            asyncio.run(trg.trigger_anomaly(huge_tx, threshold=1.5))
            self.stdout.write(self.style.SUCCESS("Аномальная трата — OK"))
        except Exception as e:
            self.stderr.write(f"[anomaly] Ошибка: {e}")

        # Закрыть сессию бота
        try:
            bot.session.close()
        except Exception:
            pass

        self.stdout.write(self.style.SUCCESS("Тест уведомлений завершён. Проверь Telegram."))
