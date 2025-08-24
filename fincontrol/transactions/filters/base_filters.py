class BaseFilter:
    """Базовый класс для всех фильтров Transaction"""
    def apply(self, qs, value):
        raise NotImplementedError("Метод apply() должен быть реализован в подклассе")

    @staticmethod
    def is_valid(value):
        """Проверка, что значение не None и не пустая строка"""
        return value not in (None, "")
