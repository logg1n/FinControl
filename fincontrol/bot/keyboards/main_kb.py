from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu(is_linked: bool) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="❌ Отменить привязку" if is_linked else "📌 Привязать аккаунт",
                callback_data="unlink" if is_linked else "link"
            )
        ],
        [
            InlineKeyboardButton(text="📊 Отчёт", callback_data="reports_menu")
        ],
        [
            InlineKeyboardButton(text="➕ Добавить запись", callback_data="add_record")
        ]
    ])
