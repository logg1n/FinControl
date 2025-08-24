from datetime import date, timedelta
from .base_filters import BaseFilter

class DatePresetFilter(BaseFilter):
    def apply(self, qs, value):
        if not self.is_valid(value):
            return qs
        today = date.today()
        if value == "day":
            return qs.filter(date__gte=today - timedelta(days=1))
        elif value == "week":
            return qs.filter(date__gte=today - timedelta(weeks=1))
        elif value == "month":
            return qs.filter(date__gte=today - timedelta(days=30))
        elif value == "year":
            return qs.filter(date__gte=today - timedelta(days=365))
        return qs

class DateRangeFilter(BaseFilter):
    def apply(self, qs, value):
        """value = (start_date, end_date)"""
        if value and len(value) == 2 and self.is_valid(value[0]) and self.is_valid(value[1]):
            return qs.filter(date__range=[value[0], value[1]])
        return qs
