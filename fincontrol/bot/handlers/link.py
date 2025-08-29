from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from django.contrib.auth import get_user_model
from django.db import transaction
from asgiref.sync import sync_to_async
import uuid

User = get_user_model()
router = Router()

def _is_valid_uuid(code: str) -> bool:
    try:
        uuid.UUID(code)
        return True
    except Exception:
        return False

@sync_to_async
def link_user_by_code(code: str, telegram_id: int):
    """
    Возвращает (status, username):
      - ("invalid", None)               — код не найден
      - ("already_linked_same", name)   — уже привязан к этому же Telegram
      - ("already_linked_other", name)  — уже привязан к другому Telegram
      - ("linked", name)                — успешно привязали
    """
    with transaction.atomic():
        user = User.objects.select_for_update().get(telegram_link_code=code)

        if user.telegram_id:
            if user.telegram_id == telegram_id:
                return "already_linked_same", user.username
            else:
                return "already_linked_other", user.username

        user.telegram_id = telegram_id
        user.telegram_link_code = ""  # одноразовый
        user.save(update_fields=["telegram_id", "telegram_link_code"])
        return "linked", user.username

@router.message(Command("link"))
async def cmd_link(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❗ Укажи код привязки: /link <код>\n\n"
            "ℹ️ Сгенерируй код в своём личном кабинете на сайте."
        )
        return

    code = args[1].strip()

    # Быстрая валидация формата UUID (опционально, но полезно)
    if not _is_valid_uuid(code):
        await message.answer("❌ Неверный формат кода. Сгенерируй новый код в личном кабинете.")
        return

    try:
        status, username = await link_user_by_code(code, message.from_user.id)

        if status == "already_linked_same":
            await message.answer("ℹ️ Этот аккаунт уже привязан к твоему Telegram.")
        elif status == "already_linked_other":
            await message.answer(
                "⚠️ Этот код принадлежит аккаунту, уже привязанному к другому Telegram.\n"
                "Если хочешь сменить привязку, отвяжи Telegram на сайте и сгенерируй новый код."
            )
        elif status == "linked":
            await message.answer(
                "✅ Готово! Telegram привязан к твоему аккаунту.\n\n"
                "Теперь доступно:\n"
                "• Уведомления о транзакциях\n"
                "• Еженедельные персональные советы\n"
                "• Быстрые команды бота\n\n"
                "💡 Попробуй /help, чтобы узнать больше."
            )
    except User.DoesNotExist:
        await message.answer(
            "❌ Код не найден или уже использован. Сгенерируй новый код в личном кабинете."
        )
