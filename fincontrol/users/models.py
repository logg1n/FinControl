from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    GENDER_CHOICES = [
        ('male', 'Мужской'),
        ('female', 'Женский'),
        ('other', 'Другое'),
    ]

    full_name = models.CharField("Полное имя", max_length=150, blank=True)
    gender = models.CharField("Пол", max_length=10, choices=GENDER_CHOICES, blank=True)
    age = models.PositiveIntegerField("Возраст", null=True, blank=True)
    position = models.CharField("Должность", max_length=150, blank=True)

    telegram_id = models.BigIntegerField("Telegram ID", null=True, blank=True, unique=True)
    telegram_link_code = models.CharField("Код привязки Telegram", max_length=36, blank=True, unique=True)

    def generate_link_code(self):
        self.telegram_link_code = str(uuid.uuid4())
        self.save()

    def __str__(self):
        return self.username
