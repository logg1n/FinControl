from datetime import date, timedelta
from .base_filters import BaseFilter

class DatePresetFilter(BaseFilter):
    def apply(self, qs, value):
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
        if value and len(value) == 2:
            start, end = value
            return qs.filter(date__range=[start, end])
        return qs
