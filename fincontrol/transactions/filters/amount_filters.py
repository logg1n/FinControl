from .base_filters import BaseFilter

class AmountGreaterFilter(BaseFilter):
    def apply(self, qs, value):
        if value:
            return qs.filter(amount__gte=value)
        return qs

class AmountLessFilter(BaseFilter):
    def apply(self, qs, value):
        if value:
            return qs.filter(amount__lte=value)
        return qs

class AmountBetweenFilter(BaseFilter):
    def apply(self, qs, value):
        """value = (min_amount, max_amount)"""
        if value and len(value) == 2:
            min_val, max_val = value
            return qs.filter(amount__gte=min_val, amount__lte=max_val)
        return qs
