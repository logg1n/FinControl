from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async
from transactions.enums.store import load_enums  # замени на реальный путь, где у тебя load_enums

@sync_to_async
def get_categories():
    """
    Возвращает список категорий из enums.json
    """
    enums = load_enums()
    return [(name, name) for name in enums["categories"]]

@sync_to_async
def get_subcategories(category_name: str):
    """
    Возвращает список подкатегорий для указанной категории из enums.json
    """
    enums = load_enums()
    return [(name, name) for name in enums["subcategories"].get(category_name, [])]

def categories_keyboard(categories) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора категории.
    """
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"category_{name}")]
        for _, name in categories
    ]
    buttons.append([InlineKeyboardButton(text="📋 Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def subcategories_keyboard(subcategories, parent_name: str) -> InlineKeyboardMarkup:
    """
    Клавиатура выбора подкатегории.
    """
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"subcategory_{name}")]
        for _, name in subcategories
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="category_menu")])
    buttons.append([InlineKeyboardButton(text="📋 Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
