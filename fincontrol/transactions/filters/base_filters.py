class BaseFilter:
    """Базовый класс для всех фильтров Transaction"""
    def apply(self, qs, value):
        raise NotImplementedError("Метод apply() должен быть реализован в подклассе")
