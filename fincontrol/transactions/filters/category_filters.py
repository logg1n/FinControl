from .base_filters import BaseFilter

class CategoryFilter(BaseFilter):
    def apply(self, qs, value):
        if self.is_valid(value):
            return qs.filter(category__iexact=value)
        return qs

class SubCategoryFilter(BaseFilter):
    def apply(self, qs, value):
        if self.is_valid(value):
            return qs.filter(subcategory__iexact=value)
        return qs
