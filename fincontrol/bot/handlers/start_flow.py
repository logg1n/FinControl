from aiogram import F, types, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db import transaction
from bot.keyboards.main_kb import main_menu

User = get_user_model()
router = Router()

def start_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Старт")]],
        resize_keyboard=True
    )

def menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Меню")]],
        resize_keyboard=True
    )

@sync_to_async
def is_user_linked(telegram_id: int) -> bool:
    return User.objects.filter(telegram_id=telegram_id).exists()

@sync_to_async
def link_user_by_username(username: str, telegram_id: int) -> bool:
    username = username.strip().lower()
    with transaction.atomic():
        try:
            user = User.objects.select_for_update().get(telegram_username__iexact=username)
        except User.DoesNotExist:
            return False
        if user.telegram_id:
            return False
        user.telegram_id = telegram_id
        user.save(update_fields=["telegram_id"])
        return True

@sync_to_async
def unlink_user(telegram_id: int) -> bool:
    try:
        user = User.objects.get(telegram_id=telegram_id)
    except User.DoesNotExist:
        return False
    user.telegram_id = None
    user.save(update_fields=["telegram_id"])
    return True

async def do_link(message: types.Message):
    username = message.from_user.username
    if not username:
        await message.answer("⚠️ У вас в Telegram не установлен @username.", reply_markup=start_kb())
        return
    if await is_user_linked(message.from_user.id):
        await message.answer("📋 Вы уже привязаны.", reply_markup=menu_kb())
        return
    linked = await link_user_by_username(username, message.from_user.id)
    if linked:
        await message.answer(f"✅ Telegram @{username} успешно привязан!", reply_markup=menu_kb())
    else:
        await message.answer("⚠️ Не удалось привязать Telegram.", reply_markup=start_kb())

@router.message(Command("start"))
async def cmd_start(message: Message):
    await do_link(message)

@router.message(F.text.casefold() == "старт")
async def btn_start(message: Message):
    await do_link(message)

@router.message(F.text.casefold() == "меню")
async def open_menu(message: Message):
    if await is_user_linked(message.from_user.id):
        await message.answer("📋 Главное меню:", reply_markup=main_menu(True))
    else:
        await message.answer("⚠️ Telegram не привязан.", reply_markup=start_kb())

@router.callback_query(F.data == "unlink")
async def cb_unlink(call: types.CallbackQuery):
    success = await unlink_user(call.from_user.id)
    if success:
        await call.message.edit_text("🔓 Привязка аккаунта отменена.")
        await call.message.answer("👋 Вернёмся к началу.", reply_markup=start_kb())
    else:
        await call.message.edit_text("⚠️ Не удалось найти привязанный аккаунт.", reply_markup=main_menu(False))
    await call.answer()
