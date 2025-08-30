from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async
from transactions.enums.service import get_enum_service

@sync_to_async
def get_categories():
    """
    Возвращает список категорий в формате (value, label) для клавиатур.
    """
    cats = get_enum_service().list_categories()
    return [(name, name) for name in cats]

@sync_to_async
def get_subcategories(category_name: str):
    """
    Возвращает список подкатегорий в формате (value, label) для клавиатур.
    """
    subs = get_enum_service().list_subcategories(category_name)
    return [(name, name) for name in subs]

def categories_keyboard(categories, extra_buttons=None) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора категории.
    :param categories: список кортежей (value, label)
    :param extra_buttons: список дополнительных кнопок [[InlineKeyboardButton(...)]]
    """
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"category_{name}")]
        for _, name in categories
    ]
    if extra_buttons:
        buttons.extend(extra_buttons)
    buttons.append([InlineKeyboardButton(text="📋 Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def subcategories_keyboard(subcategories, parent_name: str, extra_buttons=None) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора подкатегории.
    :param subcategories: список кортежей (value, label)
    :param parent_name: имя родительской категории
    :param extra_buttons: список дополнительных кнопок [[InlineKeyboardButton(...)]]
    """
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"subcategory_{name}")]
        for _, name in subcategories
    ]
    if extra_buttons:
        buttons.extend(extra_buttons)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="category_menu")])
    buttons.append([InlineKeyboardButton(text="📋 Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
