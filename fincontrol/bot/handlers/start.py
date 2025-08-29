from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from django.utils import timezone
from datetime import timedelta
from transactions.models import Transaction
from django.db.models import Sum
from asgiref.sync import sync_to_async
from ..keyboards.report_kb import report_keyboard

router = Router()

# ===== ORM helpers =====
@sync_to_async
def get_today_expenses(user_id):
    today = timezone.now().date()
    return Transaction.objects.filter(
        user__telegram_id=user_id,
        date=today,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0

@sync_to_async
def get_week_expenses(user_id):
    start = timezone.now().date() - timedelta(days=7)
    return Transaction.objects.filter(
        user__telegram_id=user_id,
        date__gte=start,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0

@sync_to_async
def get_category_expenses(user_id, category):
    return Transaction.objects.filter(
        user__telegram_id=user_id,
        category__iexact=category,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0

@sync_to_async
def get_user_by_telegram_id(telegram_id: int):
    return User.objects.filter(telegram_id=telegram_id).first()

# ===== Handlers =====

@router.message(Command("start"))
async def cmd_start(message: Message):
    user = await get_user_by_telegram_id(message.from_user.id)

    if user:
        # Уже привязан
        await message.answer(
            f"👋 Привет, {user.username or 'друг'}!\n\n"
            "Твой Telegram уже привязан к аккаунту ✅\n"
            "Теперь ты можешь:\n"
            "• Получать уведомления о транзакциях\n"
            "• Получать персональные советы\n"
            "• Использовать быстрые команды для анализа\n\n"
            "ℹ️ Введи /help, чтобы увидеть все доступные команды."
        )
    else:
        # Не привязан
        await message.answer(
            "👋 Привет! Я — твой финансовый помощник 💰\n\n"
            "Чтобы я мог присылать тебе уведомления и советы, нужно привязать Telegram к аккаунту.\n\n"
            "🔗 Для этого:\n"
            "1. Зайди в личный кабинет на сайте\n"
            "2. Сгенерируй код привязки\n"
            "3. Отправь его сюда командой:\n"
            "`/link <код>`\n\n"
            "После привязки тебе будут доступны все функции.\n"
            "ℹ️ Список команд — /help"
        )

@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "🤖 *Финансовый помощник — справка*\n\n"
        "Доступные команды:\n"
        "• /start — приветствие и краткое описание возможностей\n"
        "• /link `<код>` — привязать Telegram к аккаунту (код берётся в личном кабинете на сайте)\n"
        "• /today — расходы за сегодня\n"
        "• /week — расходы за последние 7 дней\n"
        "• /category `<название>` — расходы по указанной категории\n"
        "• /report — краткий отчёт за сегодня и неделю\n"
        "• /help — показать это сообщение\n\n"
        "💡 *Советы:*\n"
        "— Привяжи Telegram через /link, чтобы получать уведомления и советы.\n"
        "— Используй /category для анализа конкретных трат.\n"
        "— Отчёт /report удобно открывать в начале дня.\n\n"
        "🌐 Личный кабинет: [Перейти на сайт](https://example.com)"
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

@router.message(Command("today"))
async def cmd_today(message: Message):
    total = await get_today_expenses(message.from_user.id)
    await message.answer(f"💸 Расходы за сегодня: {total:.2f}")

@router.message(Command("week"))
async def cmd_week(message: Message):
    total = await get_week_expenses(message.from_user.id)
    await message.answer(f"📊 Расходы за неделю: {total:.2f}")

@router.message(Command("category"))
async def cmd_category(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Укажи категорию: /category <название>")
        return
    cat = args[1]
    total = await get_category_expenses(message.from_user.id, cat)
    await message.answer(f"📂 Расходы по категории '{cat}': {total:.2f}")

@router.message(Command("report"))
async def cmd_report(message: Message):
    expenses_today = await get_today_expenses(message.from_user.id)
    expenses_week = await get_week_expenses(message.from_user.id)
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
