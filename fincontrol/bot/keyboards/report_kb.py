# fincontrol/bot/keyboards/report_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def report_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подробнее", callback_data="details")],
        [InlineKeyboardButton(text="Сравнить с прошлой неделей", callback_data="compare_week")],
        [InlineKeyboardButton(text="Добавить трату", callback_data="add_expense")]
    ])
