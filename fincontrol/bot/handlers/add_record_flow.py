from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import datetime

from bot.keyboards.categories_kb import (
    get_categories,
    get_subcategories,
    categories_keyboard,
    subcategories_keyboard,
)
from bot.keyboards.main_kb import main_menu
from django.contrib.auth import get_user_model
from transactions.models import Transaction

User = get_user_model()
router = Router()

# ===== Хелперы =====
def back_btn(callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=callback)]]
    )

def fmt_confirm_text(data: dict) -> str:
    return (
        f"Тип: {data['type']}\n"
        f"Категория: {data.get('category', 'Общая')}\n"
        f"Подкатегория: {data.get('subcategory', '—')}\n"
        f"Сумма: {data['amount']}\n"
        f"Дата: {data['date'].strftime('%d.%m.%Y')}"
    )

# ===== Состояния =====
class AddRecord(StatesGroup):
    type = State()
    category = State()
    subcategory = State()
    amount = State()
    date = State()
    confirm = State()

# ===== Старт =====
@router.callback_query(F.data == "add_record")
async def add_record_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Расход", callback_data="type_expense")],
        [InlineKeyboardButton(text="💰 Доход", callback_data="type_income")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
    ])
    await state.set_state(AddRecord.type)
    await call.message.edit_text("Выбери тип записи:", reply_markup=kb)

# ===== Выбор типа =====
@router.callback_query(AddRecord.type, F.data.startswith("type_"))
async def choose_type(call: CallbackQuery, state: FSMContext):
    record_type = call.data.split("_", 1)[1]
    await state.update_data(type=record_type)

    # Если мы в режиме редактирования поля "type" — вернуться к подтверждению
    data = await state.get_data()
    if data.get("edit_field") == "type":
        await state.update_data(edit_field=None)
        await show_confirm(call.message, state)
        return

    cats = await get_categories()
    kb = categories_keyboard(cats, extra_buttons=[
        ("Пропустить", "skip_category"),
        ("⬅️ Назад", "add_record")
    ])
    await state.set_state(AddRecord.category)
    await call.message.edit_text("📂 Выбери категорию:", reply_markup=kb)

# ===== Выбор категории =====
@router.callback_query(AddRecord.category)
async def choose_category(call: CallbackQuery, state: FSMContext):
    if call.data == "skip_category":
        await state.update_data(category="Общее")
        subs = await get_subcategories("Общее")
        kb = subcategories_keyboard(subs, "Общее", extra_buttons=[
            ("Пропустить", "skip_subcategory"),
            ("⬅️ Назад", "back_to_category")
        ])
        await state.set_state(AddRecord.subcategory)
        await call.message.edit_text("📂 Выбери подкатегорию или пропусти:", reply_markup=kb)
        return

    if call.data.startswith("category_"):
        cat_name = call.data.split("_", 1)[1]
        await state.update_data(category=cat_name)
        subs = await get_subcategories(cat_name)
        if subs:
            kb = subcategories_keyboard(subs, cat_name, extra_buttons=[
                ("Пропустить", "skip_subcategory"),
                ("⬅️ Назад", "back_to_category")
            ])
            await state.set_state(AddRecord.subcategory)
            await call.message.edit_text("📂 Выбери подкатегорию:", reply_markup=kb)
        else:
            await state.update_data(subcategory=None)
            await state.set_state(AddRecord.amount)
            await call.message.edit_text("💵 Введи сумму:", reply_markup=back_btn("back_to_category"))

# ===== Выбор подкатегории =====
@router.callback_query(AddRecord.subcategory)
async def choose_subcategory(call: CallbackQuery, state: FSMContext):
    if call.data == "skip_subcategory":
        await state.update_data(subcategory="Общее")
    elif call.data.startswith("subcategory_"):
        sub_name = call.data.split("_", 1)[1]
        await state.update_data(subcategory=sub_name)
    else:
        await state.update_data(subcategory="Общее")

    # Если редактировали категорию/подкатегорию — сразу вернуться к подтверждению
    data = await state.get_data()
    if data.get("edit_field") in {"category", "subcategory"}:
        await state.update_data(edit_field=None)
        await show_confirm(call.message, state)
        return

    await state.set_state(AddRecord.amount)
    await call.message.edit_text("💵 Введи сумму:", reply_markup=back_btn("back_to_subcategory"))

# ===== Ввод суммы =====
@router.message(AddRecord.amount)
async def input_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверная сумма. Введите положительное число.")
        return

    await state.update_data(amount=amount)

    data = await state.get_data()
    # Если редактировали только сумму — вернуться к подтверждению
    if data.get("edit_field") == "amount":
        await state.update_data(edit_field=None)
        await show_confirm(message, state)
        return

    await state.set_state(AddRecord.date)
    await message.answer(
        "📅 Введи дату (ДД.ММ.ГГГГ) или напиши 'сегодня'.\nМожно пропустить.",
        reply_markup=back_btn("back_to_amount")
    )

# ===== Ввод даты =====
@router.message(AddRecord.date)
async def input_date(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    if text in ("", "пропустить", "сегодня"):
        date = timezone.now().date()
    else:
        try:
            date = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            await message.answer("❌ Неверный формат даты. Попробуй ещё раз.")
            return

    await state.update_data(date=date)

    data = await state.get_data()
    # Если редактировали только дату — вернуться к подтверждению
    if data.get("edit_field") == "date":
        await state.update_data(edit_field=None)
        await show_confirm(message, state)
        return

    await show_confirm(message, state)

# ===== Подтверждение =====
async def show_confirm(message_or_msg, state: FSMContext):
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_record")],
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_record")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
    ])
    await state.set_state(AddRecord.confirm)
    # message_or_msg может быть Message (message) или Message (call.message)
    await message_or_msg.answer(f"Проверь данные:\n\n{fmt_confirm_text(data)}", reply_markup=kb)

# ===== Сохранение =====
@router.callback_query(AddRecord.confirm, F.data == "save_record")
async def save_record(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await save_transaction(call.from_user.id, data)
    await state.clear()
    await call.message.edit_text("✅ Запись сохранена!", reply_markup=main_menu(True))
    await call.answer()

# ===== Меню редактирования на экране подтверждения =====
@router.callback_query(AddRecord.confirm, F.data == "edit_record")
async def edit_record(call: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Тип", callback_data="edit_type")],
        [InlineKeyboardButton(text="Категория", callback_data="edit_category")],
        [InlineKeyboardButton(text="Подкатегория", callback_data="edit_subcategory")],
        [InlineKeyboardButton(text="Сумма", callback_data="edit_amount")],
        [InlineKeyboardButton(text="Дата", callback_data="edit_date")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="confirm_back")]
    ])
    await call.message.edit_text("Выбери поле для изменения:", reply_markup=kb)
    await call.answer()

# ===== Обработчики изменения полей =====
@router.callback_query(F.data == "edit_type")
async def edit_type(call: CallbackQuery, state: FSMContext):
    await state.update_data(edit_field="type")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Расход", callback_data="type_expense")],
        [InlineKeyboardButton(text="💰 Доход", callback_data="type_income")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="confirm_back")]
    ])
    await state.set_state(AddRecord.type)
    await call.message.edit_text("Выбери тип записи:", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "edit_category")
async def edit_category(call: CallbackQuery, state: FSMContext):
    await state.update_data(edit_field="category")
    cats = await get_categories()
    kb = categories_keyboard(cats, extra_buttons=[
        ("Пропустить", "skip_category"),
        ("⬅️ Назад", "confirm_back")
    ])
    await state.set_state(AddRecord.category)
    await call.message.edit_text("📂 Выбери категорию:", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "edit_subcategory")
async def edit_subcategory(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    if not category:
        # Если нет выбранной категории — предложить выбрать категорию
        await state.update_data(edit_field="category")
        cats = await get_categories()
        kb = categories_keyboard(cats, extra_buttons=[
            ("Пропустить", "skip_category"),
            ("⬅️ Назад", "confirm_back")
        ])
        await state.set_state(AddRecord.category)
        await call.message.edit_text("Сначала выбери категорию:", reply_markup=kb)
        await call.answer()
        return

    await state.update_data(edit_field="subcategory")
    subs = await get_subcategories(category)
    kb = subcategories_keyboard(subs, category, extra_buttons=[
        ("Пропустить", "skip_subcategory"),
        ("⬅️ Назад", "confirm_back")
    ])
    await state.set_state(AddRecord.subcategory)
    await call.message.edit_text("📂 Выбери подкатегорию:", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "edit_amount")
async def edit_amount(call: CallbackQuery, state: FSMContext):
    await state.update_data(edit_field="amount")
    await state.set_state(AddRecord.amount)
    await call.message.edit_text("💵 Введи новую сумму:", reply_markup=back_btn("confirm_back"))
    await call.answer()

@router.callback_query(F.data == "edit_date")
async def edit_date(call: CallbackQuery, state: FSMContext):
    await state.update_data(edit_field="date")
    await state.set_state(AddRecord.date)
    await call.message.edit_text("📅 Введи новую дату (ДД.ММ.ГГГГ) или 'сегодня':", reply_markup=back_btn("confirm_back"))
    await call.answer()

# ===== Сохранение в БД =====
@sync_to_async
def save_transaction(telegram_id, data):
    user = User.objects.get(telegram_id=telegram_id)
    Transaction.objects.create(
        user=user,
        type=data["type"],
        category=data.get("category", "Общее"),
        subcategory=data.get("subcategory"),
        amount=data["amount"],
        date=data["date"]
    )

# ===== Обработчики кнопок "Назад" =====
@router.callback_query(F.data == "back_to_category")
async def back_to_category(call: CallbackQuery, state: FSMContext):
    cats = await get_categories()
    kb = categories_keyboard(cats, extra_buttons=[
        ("Пропустить", "skip_category"),
        ("⬅️ Назад", "add_record")
    ])
    await state.set_state(AddRecord.category)
    await call.message.edit_text("📂 Выбери категорию:", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "back_to_subcategory")
async def back_to_subcategory(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cat = data.get("category", "Общее")
    subs = await get_subcategories(cat)
    kb = subcategories_keyboard(subs, cat, extra_buttons=[
        ("Пропустить", "skip_subcategory"),
        ("⬅️ Назад", "back_to_category")
    ])
    await state.set_state(AddRecord.subcategory)
    await call.message.edit_text("📂 Выбери подкатегорию:", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "back_to_amount")
async def back_to_amount(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddRecord.amount)
    await call.message.edit_text("💵 Введи сумму:", reply_markup=back_btn("back_to_subcategory"))
    await call.answer()

@router.callback_query(F.data == "back_to_date")
async def back_to_date(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddRecord.date)
    await call.message.edit_text("📅 Введи дату (ДД.ММ.ГГГГ) или 'сегодня'. Можно пропустить.", reply_markup=back_btn("back_to_amount"))
    await call.answer()

# ===== Возврат к подтверждению =====
@router.callback_query(F.data == "confirm_back")
async def confirm_back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Сохранить", callback_data="save_record")],
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_record")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="main_menu")]
    ])
    await state.set_state(AddRecord.confirm)
    await call.message.edit_text(f"Проверь данные:\n\n{fmt_confirm_text(data)}", reply_markup=kb)
    await call.answer()
