import json
from pathlib import Path
from django.conf import settings

DEFAULT_ENUMS = {
    "categories": ["Еда", "Транспорт", "Развлечения", "Зарплата", "Подарки"],
    "subcategories": {
        "Еда": ["Продукты", "Кафе", "Доставка"],
        "Транспорт": ["Автобус", "Такси", "Метро"],
        "Развлечения": ["Кино", "Игры", "Концерт"],
        "Зарплата": ["Основная", "Премия"],
        "Подарки": ["День рождения", "Новый год"]
    }
}

def get_enums_path() -> Path:
    path = Path(getattr(settings, "ENUMS_FILE", Path(settings.BASE_DIR) / "data" / "enums.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def load_enums() -> dict:
    path = get_enums_path()
    if not path.exists():
        save_enums(DEFAULT_ENUMS)
        return DEFAULT_ENUMS.copy()
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_enums(data: dict) -> None:
    path = get_enums_path()
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
