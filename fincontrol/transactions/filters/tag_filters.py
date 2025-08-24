from .base_filters import BaseFilter

class TagFilter(BaseFilter):
    def apply(self, qs, value):
        if value:
            return qs.filter(tag__icontains=value)
        return qs
