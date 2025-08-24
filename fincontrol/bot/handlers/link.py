from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from users.models import Profile  # путь к твоей модели профиля
from django.db import transaction

router = Router()

@router.message(Command("link"))
async def cmd_link(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❗ Укажи код привязки: /link <код>")
        return

    code = args[1].strip()

    try:
        with transaction.atomic():
            profile = Profile.objects.select_for_update().get(telegram_link_code=code)
            profile.telegram_id = message.from_user.id
            profile.telegram_link_code = ""  # очищаем код, чтобы нельзя было использовать повторно
            profile.save()
        await message.answer("✅ Telegram успешно привязан к твоему профилю!")
    except Profile.DoesNotExist:
        await message.answer("❌ Код не найден или уже использован. Сгенерируй новый в веб‑кабинете.")
