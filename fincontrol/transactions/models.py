from django.db import models
from django.contrib.auth.models import User
from .constants import CURRENCY_CHOICES



class Transaction(models.Model):
    TYPE_CHOICES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
    ]

    PAYMENT_METHODS = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        ('online', 'Онлайн-платёж'),
        ('other', 'Другое'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма")
    date = models.DateField(verbose_name="Дата операции")
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, verbose_name="Тип операции")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, verbose_name="Способ оплаты/получения")
    currency = models.CharField(max_length=6, choices=CURRENCY_CHOICES, verbose_name="Валюта")
    tag = models.CharField(max_length=50, blank=True, verbose_name="Метка")
    category = models.CharField(max_length=50, verbose_name="Категория")
    subcategory = models.CharField(max_length=50, blank=True, verbose_name="Подкатегория")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} | {self.amount} {self.currency} | {self.get_type_display()}"
