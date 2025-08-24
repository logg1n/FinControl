from .base_filters import BaseFilter

class PaymentMethodFilter(BaseFilter):
    def apply(self, qs, value):
        if self.is_valid(value):
            return qs.filter(payment_method=value)
        return qs
