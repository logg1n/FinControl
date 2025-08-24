from .amount_filters import AmountGreaterFilter, AmountLessFilter, AmountBetweenFilter
from .date_filters import DatePresetFilter, DateRangeFilter
from .category_filters import CategoryFilter, SubCategoryFilter
from .currency_filters import CurrencyFilter
from .payment_filters import PaymentMethodFilter
from .tag_filters import TagFilter

class TransactionFilters:
    """Объединённый интерфейс для всех фильтров Transaction"""
    def __init__(self, qs):
        self.qs = qs

    def apply(self, params):
        self.qs = AmountGreaterFilter().apply(self.qs, params.get("amount_min"))
        self.qs = AmountLessFilter().apply(self.qs, params.get("amount_max"))
        self.qs = AmountBetweenFilter().apply(self.qs, (
            params.get("amount_from"),
            params.get("amount_to")
        ))
        self.qs = DatePresetFilter().apply(self.qs, params.get("date_preset"))
        self.qs = DateRangeFilter().apply(self.qs, (
            params.get("date_from"),
            params.get("date_to")
        ))
        self.qs = CategoryFilter().apply(self.qs, params.get("category"))
        self.qs = SubCategoryFilter().apply(self.qs, params.get("subcategory"))
        self.qs = CurrencyFilter().apply(self.qs, params.get("currency"))
        self.qs = PaymentMethodFilter().apply(self.qs, params.get("payment_method"))
        self.qs = TagFilter().apply(self.qs, params.get("tag"))
        return self.qs
