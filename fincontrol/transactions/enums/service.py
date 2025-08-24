from .store import load_enums, save_enums

class EnumService:
    def __init__(self):
        self._data = load_enums()

    def _persist(self):
        save_enums(self._data)

    def list_categories(self):
        return list(self._data.get("categories", []))

    def add_category(self, name: str):
        name = name.strip()
        if not name or name in self._data["categories"]:
            return False
        self._data["categories"].append(name)
        self._data["subcategories"].setdefault(name, [])
        self._persist()
        return True

    def list_subcategories(self, category: str):
        return list(self._data["subcategories"].get(category, []))

    def add_subcategory(self, category: str, name: str):
        name = name.strip()
        if not name or category not in self._data["categories"]:
            return False
        subs = self._data["subcategories"].setdefault(category, [])
        if name in subs:
            return False
        subs.append(name)
        self._persist()
        return True

def get_enum_service() -> EnumService:
    return EnumService()
