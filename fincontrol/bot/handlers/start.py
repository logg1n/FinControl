# fincontrol/bot/handlers/stats.py
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from django.utils import timezone
from datetime import timedelta
from transactions.models import Transaction
from django.db.models import Sum
from ..keyboards.report_kb import report_keyboard


router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я твой финансовый помощник 💰\n"
        "/today — расходы за сегодня\n"
        "/week — статистика за неделю\n"
        "/category <название> — траты по категории\n"
        "/report — ежедневный отчёт"
    )

@router.message(Command("today"))
async def cmd_today(message: Message):
    user_id = message.from_user.id
    today = timezone.now().date()
    total = Transaction.objects.filter(
        user__telegram_id=user_id,
        date=today,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0
    await message.answer(f"💸 Расходы за сегодня: {total:.2f}")

@router.message(Command("week"))
async def cmd_week(message: Message):
    user_id = message.from_user.id
    start = timezone.now().date() - timedelta(days=7)
    total = Transaction.objects.filter(
        user__telegram_id=user_id,
        date__gte=start,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0
    await message.answer(f"📊 Расходы за неделю: {total:.2f}")

@router.message(Command("category"))
async def cmd_category(message: Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажи категорию: /category <название>")
        return
    cat = args[1]
    total = Transaction.objects.filter(
        user__telegram_id=user_id,
        category__iexact=cat,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0
    await message.answer(f"📂 Расходы по категории '{cat}': {total:.2f}")

@router.message(Command("report"))
async def cmd_report(message: Message):
    user_id = message.from_user.id
    today = timezone.now().date()
    expenses_today = Transaction.objects.filter(
        user__telegram_id=user_id,
        date=today,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0

    expenses_week = Transaction.objects.filter(
        user__telegram_id=user_id,
        date__gte=today - timedelta(days=7),
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0

    await message.answer(
        f"📅 Сегодня: {expenses_today:.2f}\n"
        f"📆 Неделя: {expenses_week:.2f}",
        reply_markup=report_keyboard()
    )

@router.callback_query()
async def callbacks(call: CallbackQuery):
    if call.data == "details":
        await call.message.edit_text("🔍 Здесь будет подробный отчёт...")
    elif call.data == "compare_week":
        await call.message.edit_text("📊 Сравнение с прошлой неделей...")
    elif call.data == "add_expense":
        await call.message.edit_text("➕ Форма добавления траты (в разработке)")
    await call.answer()
