from .base_filters import BaseFilter

class CurrencyFilter(BaseFilter):
    def apply(self, qs, value):
        if self.is_valid(value):
            return qs.filter(currency=value)
        return qs
