from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from asgiref.sync import sync_to_async
from django.utils import timezone
from asgiref.sync import sync_to_async
from django.utils import timezone

from users.models import User
from transactions.models import Transaction
from transactions.queries import get_balance

from bot.keyboards.categories_kb import (
    get_categories,
    get_subcategories,
    categories_keyboard,
    subcategories_keyboard
)


router = Router()

# ===== Состояния FSM =====
class AddRecord(StatesGroup):
    choosing_type = State()
    choosing_category = State()
    choosing_subcategory = State()
    entering_amount = State()
    confirming = State()

# ===== Кнопки выбора типа =====
def type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💵 Доход", callback_data="type_income")],
        [InlineKeyboardButton(text="💸 Расход", callback_data="type_expense")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_record")]
    ])

# ===== Создание транзакции (синхронный ORM в отдельном потоке) =====

@sync_to_async
def create_transaction(telegram_id, record_type, category, subcategory, amount, payment_method="cash", currency="BYN", tag=""):
    # Находим пользователя по telegram_id
    user = User.objects.get(telegram_id=telegram_id)

    return Transaction.objects.create(
        user=user,
        type=record_type,
        category=category,
        subcategory=subcategory if subcategory != "—" else None,
        amount=amount,
        date=timezone.now().date(),
        payment_method=payment_method,
        currency=currency,
        tag=tag
    )


# ===== Старт добавления записи =====
@router.callback_query(F.data == "add_record")
async def cb_add_record(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddRecord.choosing_type)
    new_text = "➕ Выберите тип записи:"
    if call.message.text != new_text:
        await call.message.edit_text(new_text, reply_markup=type_keyboard())
    else:
        await call.answer()

# ===== Выбор типа =====
@router.callback_query(F.data.startswith("type_"), AddRecord.choosing_type)
async def choose_type(call: CallbackQuery, state: FSMContext):
    record_type = call.data.split("_")[1]  # income / expense
    await state.update_data(record_type=record_type)

    cats = await get_categories()
    kb = categories_keyboard(
        cats,
        extra_buttons=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_record")]]
    )

    await state.set_state(AddRecord.choosing_category)
    await call.message.edit_text(f"📂 Выберите категорию для {'дохода' if record_type=='income' else 'расхода'}:", reply_markup=kb)
    await call.answer()

# ===== Выбор категории =====
@router.callback_query(F.data.startswith("category_"), AddRecord.choosing_category)
async def choose_category(call: CallbackQuery, state: FSMContext):
    category_name = call.data.split("_", 1)[1]
    await state.update_data(category=category_name)

    subs = await get_subcategories(category_name)
    if subs:
        kb = subcategories_keyboard(
            subs,
            parent_name=category_name,
            extra_buttons=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_record")]]
        )
        await state.set_state(AddRecord.choosing_subcategory)
        await call.message.edit_text(f"📂 Выберите подкатегорию для {category_name}:", reply_markup=kb)
    else:
        await state.set_state(AddRecord.entering_amount)
        await call.message.edit_text(f"💰 Введите сумму для {category_name}:")
    await call.answer()

# ===== Выбор подкатегории =====
@router.callback_query(F.data.startswith("subcategory_"), AddRecord.choosing_subcategory)
async def choose_subcategory(call: CallbackQuery, state: FSMContext):
    subcategory_name = call.data.split("_", 1)[1]
    await state.update_data(subcategory=subcategory_name)

    await state.set_state(AddRecord.entering_amount)
    await call.message.edit_text(f"💰 Введите сумму для {subcategory_name}:")
    await call.answer()

# ===== Ввод суммы =====
@router.message(AddRecord.entering_amount)
async def enter_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите корректное число.")
        return

    await state.update_data(amount=amount)
    data = await state.get_data()

    category = data.get("category")
    subcategory = data.get("subcategory", "—")
    record_type = data.get("record_type")

    text = (
        f"📋 Подтверждение записи:\n"
        f"Тип: {'Доход' if record_type=='income' else 'Расход'}\n"
        f"Категория: {category}\n"
        f"Подкатегория: {subcategory}\n"
        f"Сумма: {amount:.2f}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_add_record")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_record")]
    ])

    await state.set_state(AddRecord.confirming)
    await message.answer(text, reply_markup=kb)

# ===== Подтверждение =====

@router.callback_query(F.data == "confirm_add_record", AddRecord.confirming)
async def confirm_record(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await create_transaction(
        call.from_user.id,
        data["record_type"],
        data["category"],
        data.get("subcategory", "—"),
        data["amount"]
    )

    # Получаем актуальный баланс
    balance = await get_balance(call.from_user.id)

    await state.clear()
    await call.message.edit_text(
        f"✅ Запись успешно добавлена!\n💰 Текущий баланс: {balance:.2f}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📋 Меню", callback_data="main_menu")]]
        )
    )
    await call.answer()


# ===== Отмена =====
@router.callback_query(F.data == "cancel_add_record")
async def cancel_add_record(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Добавление записи отменено.", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="📋 Меню", callback_data="main_menu")]]
    ))
    await call.answer()
