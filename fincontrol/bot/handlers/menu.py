from aiogram.exceptions import TelegramBadRequest
from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from datetime import datetime, timedelta
from django.utils import timezone

from bot.keyboards.main_kb import main_menu
from bot.keyboards.categories_kb import (
    get_categories,
    get_subcategories,
    categories_keyboard,
    subcategories_keyboard
)
from transactions.queries import (
    get_today_expenses,
    get_week_expenses,
    get_month_expenses,
    get_balance,
    get_first_transaction_date,
    get_last_transaction_date,
    get_period_expenses,
    get_all_categories_report,
    get_category_expenses,
    get_subcategory_expenses
)

router = Router()

# ===== Вспомогательные =====
def menu_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Меню", callback_data="main_menu")]
    ])

def period_dates(period: str):
    """Возвращает (start_date, end_date) по ключу периода."""
    today = timezone.now().date()
    if period == "day":
        return today, today
    elif period == "week":
        return today - timedelta(days=7), today
    elif period == "month":
        return today.replace(day=1), today
    return None, None

# ===== Главное меню =====
@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery):

    try:
        await call.message.edit_text("📋 Главное меню:", reply_markup=main_menu(True))
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise

# ===== Подменю «Отчёты» =====
def reports_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 За день", callback_data="report_day")],
        [InlineKeyboardButton(text="📆 За неделю", callback_data="report_week")],
        [InlineKeyboardButton(text="🗓 За месяц", callback_data="report_month")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="report_balance")],
        [InlineKeyboardButton(text="📍 Произвольный период", callback_data="report_custom")],
        [InlineKeyboardButton(text="📂 Отчёт по категориям", callback_data="categories_report")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])

@router.callback_query(F.data == "reports_menu")
async def cb_reports_menu(call: CallbackQuery):
    try:
        await call.message.edit_text("📊 Выбери тип отчёта:", reply_markup=reports_menu())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise

@router.callback_query(F.data == "report_day")
async def cb_report_day(call: CallbackQuery):
    total = await get_today_expenses(call.from_user.id)
    try:
        await call.message.edit_text(f"📅 Сегодня: {total:.2f}", reply_markup=reports_menu())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise

@router.callback_query(F.data == "report_week")
async def cb_report_week(call: CallbackQuery):
    total = await get_week_expenses(call.from_user.id)
    try:
        await call.message.edit_text(f"📆 Неделя: {total:.2f}", reply_markup=reports_menu())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise

@router.callback_query(F.data == "report_month")
async def cb_report_month(call: CallbackQuery):
    total = await get_month_expenses(call.from_user.id)
    try:
        await call.message.edit_text(f"🗓 Месяц: {total:.2f}", reply_markup=reports_menu())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise

@router.callback_query(F.data == "report_balance")
async def cb_report_balance(call: CallbackQuery):
    total = await get_balance(call.from_user.id)
    try:
        await call.message.edit_text(f"💰 Баланс: {total:.2f}", reply_markup=reports_menu())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise

@router.callback_query(F.data == "report_custom")
async def cb_report_custom(call: CallbackQuery):
    first_date = await get_first_transaction_date(call.from_user.id)
    last_date = await get_last_transaction_date(call.from_user.id)
    if not first_date or not last_date:
        try:
            await call.message.edit_text("⚠️ Нет данных для отчёта.", reply_markup=reports_menu())
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await call.answer()
            else:
                raise
        return
    try:
        await call.message.edit_text(
            f"📍 Введите даты в формате ДД.ММ.ГГГГ–ДД.ММ.ГГГГ\n"
            f"Доступный диапазон: {first_date.strftime('%d.%m.%Y')} — {last_date.strftime('%d.%m.%Y')}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="reports_menu")]
            ])
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise

@router.message(F.text.regexp(r"^\d{2}\.\d{2}\.\d{4}\s*-\s*\d{2}\.\d{2}\.\d{4}$"))
async def custom_period_input(message: Message):
    try:
        start_str, end_str = message.text.replace(" ", "").split("-")
        start_date = datetime.strptime(start_str, "%d.%m.%Y").date()
        end_date = datetime.strptime(end_str, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("❌ Неверный формат. Попробуйте снова.")
        return

    first_date = await get_first_transaction_date(message.from_user.id)
    last_date = await get_last_transaction_date(message.from_user.id)

    if not first_date or not last_date:
        await message.answer("⚠️ Нет данных для отчёта.", reply_markup=reports_menu())
        return

    if start_date < first_date:
        start_date = first_date
    if end_date > last_date:
        end_date = last_date
    if start_date > end_date:
        await message.answer("⚠️ Начальная дата позже конечной. Попробуйте снова.")
        return

    total = await get_period_expenses(message.from_user.id, start_date, end_date)
    await message.answer(
        f"📍 За период {start_date.strftime('%d.%m.%Y')} — {end_date.strftime('%d.%m.%Y')}: {total:.2f}",
        reply_markup=reports_menu()
    )

# ===== Отчёт по категориям =====
def categories_report_kb(categories) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="📋 Все категории", callback_data="report_all_categories_all")]]
    for _, name in categories:
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"report_category_{name}_all")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="reports_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "categories_report")
async def cb_categories_report(call: CallbackQuery):
    cats = await get_categories()
    try:
        await call.message.edit_text("📂 Выбери категорию или смотри все:", reply_markup=categories_report_kb(cats))
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise

# ----- Все категории с фильтрами -----
def all_categories_period_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 День", callback_data="report_all_categories_day"),
         InlineKeyboardButton(text="📆 Неделя", callback_data="report_all_categories_week")],
        [InlineKeyboardButton(text="🗓 Месяц", callback_data="report_all_categories_month"),
         InlineKeyboardButton(text="♾ Всё время", callback_data="report_all_categories_all")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="categories_report")]
    ])

@router.callback_query(F.data.startswith("report_all_categories_"))
async def cb_report_all_categories(call: CallbackQuery):
    period = call.data.split("_")[-1]
    start, end = period_dates(period)
    text = await get_all_categories_report(call.from_user.id, start, end)
    try:
        await call.message.edit_text(text, reply_markup=all_categories_period_kb())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise

# ----- Отчёт по конкретной категории -----
def category_report_kb(category_name: str, subcategories, period: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📅 День", callback_data=f"report_category_{category_name}_day"),
         InlineKeyboardButton(text="📆 Неделя", callback_data=f"report_category_{category_name}_week")],
        [InlineKeyboardButton(text="🗓 Месяц", callback_data=f"report_category_{category_name}_month"),
         InlineKeyboardButton(text="♾ Всё время", callback_data=f"report_category_{category_name}_all")]
    ]
    for _, sub in subcategories:
        buttons.append([InlineKeyboardButton(text=sub, callback_data=f"report_subcategory_{sub}_{period}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="categories_report")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data.startswith("report_category_"))
async def cb_report_category(call: CallbackQuery):
    parts = call.data.split("_")
    category_name = parts[2]
    period = parts[3] if len(parts) > 3 else "all"
    start, end = period_dates(period)

    total = await get_category_expenses(call.from_user.id, category_name, start, end)
    subs = await get_subcategories(category_name)
    text = (
        f"📊 Категория: {category_name}\n"
        f"💵 Всего ({'День' if period=='day' else 'Неделя' if period=='week' else 'Месяц' if period=='month' else 'Всё время'}): "
        f"{total:.2f}\n\nВыбери подкатегорию:"
    )
    try:
        await call.message.edit_text(text, reply_markup=category_report_kb(category_name, subs, period))
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise

# ----- Отчёт по подкатегории -----
def subcategory_report_kb(subcategory_name: str, period: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 День", callback_data=f"report_subcategory_{subcategory_name}_day"),
         InlineKeyboardButton(text="📆 Неделя", callback_data=f"report_subcategory_{subcategory_name}_week")],
        [InlineKeyboardButton(text="🗓 Месяц", callback_data=f"report_subcategory_{subcategory_name}_month"),
         InlineKeyboardButton(text="♾ Всё время", callback_data=f"report_subcategory_{subcategory_name}_all")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="categories_report")]
    ])

@router.callback_query(F.data.startswith("report_subcategory_"))
async def cb_report_subcategory(call: CallbackQuery):
    parts = call.data.split("_")
    subcategory_name = parts[2]
    period = parts[3] if len(parts) > 3 else "all"
    start, end = period_dates(period)

    total = await get_subcategory_expenses(call.from_user.id, subcategory_name, start, end)
    text = (
        f"📊 Подкатегория: {subcategory_name}\n"
        f"💵 Всего ({'День' if period=='day' else 'Неделя' if period=='week' else 'Месяц' if period=='month' else 'Всё время'}): "
        f"{total:.2f}"
    )
    try:
        await call.message.edit_text(text, reply_markup=subcategory_report_kb(subcategory_name, period))
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await call.answer()
        else:
            raise