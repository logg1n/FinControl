from .base_filters import BaseFilter

class AmountGreaterFilter(BaseFilter):
    def apply(self, qs, value):
        if self.is_valid(value):
            return qs.filter(amount__gte=value)
        return qs

class AmountLessFilter(BaseFilter):
    def apply(self, qs, value):
        if self.is_valid(value):
            return qs.filter(amount__lte=value)
        return qs

class AmountBetweenFilter(BaseFilter):
    def apply(self, qs, value):
        """value = (min_amount, max_amount)"""
        if value and len(value) == 2 and self.is_valid(value[0]) and self.is_valid(value[1]):
            return qs.filter(amount__gte=value[0], amount__lte=value[1])
        return qs
