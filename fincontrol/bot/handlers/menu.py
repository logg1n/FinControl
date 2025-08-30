from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from datetime import datetime

from bot.keyboards.main_kb import main_menu

router = Router()

# ===== Вспомогательные клавиатуры =====
def menu_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Меню", callback_data="main_menu")]
    ])

# ===== Главное меню =====
@router.callback_query(F.data == "main_menu")
async def cb_main_menu(call: CallbackQuery):
    await call.message.edit_text("📋 Главное меню:", reply_markup=main_menu(True))
    await call.answer()

# ===== Подменю «Отчёты» =====
def reports_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 За день", callback_data="report_day")],
        [InlineKeyboardButton(text="📆 За неделю", callback_data="report_week")],
        [InlineKeyboardButton(text="🗓 За месяц", callback_data="report_month")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="report_balance")],
        [InlineKeyboardButton(text="📍 Произвольный период", callback_data="report_custom")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])

@router.callback_query(F.data == "reports_menu")
async def cb_reports_menu(call: CallbackQuery):
    await call.message.edit_text("📊 Выбери тип отчёта:", reply_markup=reports_menu())
    await call.answer()

@router.callback_query(F.data == "report_day")
async def cb_report_day(call: CallbackQuery):
    total = await get_today_expenses(call.from_user.id)
    await call.message.edit_text(f"📅 Сегодня: {total:.2f}", reply_markup=reports_menu())
    await call.answer()

@router.callback_query(F.data == "report_week")
async def cb_report_week(call: CallbackQuery):
    total = await get_week_expenses(call.from_user.id)
    await call.message.edit_text(f"📆 Неделя: {total:.2f}", reply_markup=reports_menu())
    await call.answer()

@router.callback_query(F.data == "report_month")
async def cb_report_month(call: CallbackQuery):
    total = await get_month_expenses(call.from_user.id)
    await call.message.edit_text(f"🗓 Месяц: {total:.2f}", reply_markup=reports_menu())
    await call.answer()

@router.callback_query(F.data == "report_balance")
async def cb_report_balance(call: CallbackQuery):
    total = await get_balance(call.from_user.id)
    await call.message.edit_text(f"💰 Баланс: {total:.2f}", reply_markup=reports_menu())
    await call.answer()

@router.callback_query(F.data == "report_custom")
async def cb_report_custom(call: CallbackQuery):
    first_date = await get_first_transaction_date(call.from_user.id)
    last_date = await get_last_transaction_date(call.from_user.id)
    if not first_date or not last_date:
        await call.message.edit_text("⚠️ Нет данных для отчёта.", reply_markup=reports_menu())
        await call.answer()
        return
    await call.message.edit_text(
        f"📍 Введите даты в формате ДД.ММ.ГГГГ–ДД.ММ.ГГГГ\n"
        f"Доступный диапазон: {first_date.strftime('%d.%m.%Y')} — {last_date.strftime('%d.%m.%Y')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="reports_menu")]
        ])
    )
    await call.answer()

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

# ===== Подменю «Категории» =====
def categories_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 По категории", callback_data="category_menu")],
        [InlineKeyboardButton(text="📂 По подкатегории", callback_data="subcategory_menu")],
        [InlineKeyboardButton(text="📋 Все категории", callback_data="all_categories_report")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ])

@router.callback_query(F.data == "categories_menu")
async def cb_categories_menu(call: CallbackQuery):
    await call.message.edit_text("📂 Выбери тип отчёта по категориям:", reply_markup=categories_menu_kb())
    await call.answer()

# ----- По категории -----
@router.callback_query(F.data == "category_menu")
async def cb_category_menu(call: CallbackQuery):
    cats = await get_categories()
    if cats:
        await call.message.edit_text("📂 Выбери категорию:", reply_markup=categories_keyboard(cats))
    else:
        await call.message.edit_text("⚠️ Категории пока не добавлены.", reply_markup=categories_menu_kb())
    await call.answer()

@router.callback_query(F.data.startswith("category_"))
async def cb_category(call: CallbackQuery):
    cat_name = call.data.split("_", 1)[1]
    subs = await get_subcategories(cat_name)
    if subs:
        await call.message.edit_text("📂 Выбери подкатегорию:", reply_markup=subcategories_keyboard(subs, cat_name))
    else:
        total = await get_category_expenses(call.from_user.id, cat_name)
        await call.message.edit_text(f"📊 Расходы по категории '{cat_name}': {total:.2f}", reply_markup=categories_menu_kb())
    await call.answer()

# ----- По подкатегории -----
def categories_keyboard_for_subcats(categories) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"subcat_pick_{name}")]
        for _, name in categories
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="categories_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(F.data == "subcategory_menu")
async def cb_subcategory_menu(call: CallbackQuery):
    cats = await get_categories()
    if not cats:
        await call.message.edit_text("⚠️ Категории пока не добавлены.", reply_markup=categories_menu_kb())
        await call.answer()
        return
    await call.message.edit_text("📂 Сначала выбери категорию:", reply_markup=categories_keyboard_for_subcats(cats))
    await call.answer()

@router.callback_query(F.data.startswith("subcat_pick_"))
async def cb_subcat_pick(call: CallbackQuery):
    cat_name = call.data.split("_", 2)[2]
    subs = await get_subcategories(cat_name)
    if not subs:
        await call.message.edit_text(f"⚠️ У категории '{cat_name}' нет подкатегорий.", reply_markup=categories_menu_kb())
    else:
        await call.message.edit_text("📂 Выбери подкатегорию:", reply_markup=subcategories_keyboard(subs, cat_name))
    await call.answer()

@router.callback_query(F.data.startswith("subcategory_"))
async def cb_subcategory(call: CallbackQuery):
    sub_name = call.data.split("_", 1)[1]
    total = await get_subcategory_expenses(call.from_user.id, sub_name)
    await call.message.edit_text(f"📊 Расходы по подкатегории '{sub_name}': {total:.2f}", reply_markup=categories_menu_kb())
    await call.answer()

# ----- Все категории -----
@router.callback_query(F.data == "all_categories_report")
async def cb_all_categories_report(call: CallbackQuery):
    report_text = await get_all_categories_report(call.from_user.id)
    await call.message.edit_text(report_text, reply_markup=categories_menu_kb())
    await call.answer()

# ===== Добавить запись (заглушка) =====
@router.callback_query(F.data == "add_record")
async def cb_add_record(call: CallbackQuery):
    await call.message.edit_text("➕ Добавление записи (в разработке)", reply_markup=menu_button())
    await call.answer()
