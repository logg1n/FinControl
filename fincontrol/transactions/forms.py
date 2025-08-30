 
# transactions/forms.py
from django import forms
from .models import Transaction
from .enums.service import get_enum_service
from .constants import CURRENCY_CHOICES

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            "amount",
            "date",
            "type",
            "payment_method",
            "currency",
            "tag",
            "category",
            "subcategory",
        ]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "tag": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- Категории ---
        svc = get_enum_service()
        categories = svc.list_categories()
        self.fields["category"].widget = forms.Select(
            choices=[("", "—")] + [(c, c) for c in categories] + [("__add_new__", "+ Добавить категорию…")],
            attrs={"class": "form-select"}
        )

        # --- Подкатегории ---
        selected_category = (
            self.data.get("category")
            or self.initial.get("category")
            or getattr(self.instance, "category", "")
        )
        subcategories = svc.list_subcategories(selected_category) if selected_category else []
        self.fields["subcategory"].widget = forms.Select(
            choices=[("", "—")] + [(s, s) for s in subcategories] + [("__add_new__", "+ Добавить подкатегорию…")],
            attrs={"class": "form-select"}
        )

        # --- Валюты ---
        self.fields["currency"].widget = forms.Select(
            choices=CURRENCY_CHOICES,
            attrs={"class": "form-select"}
        )
