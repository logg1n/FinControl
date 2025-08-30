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
    email = models.EmailField("Email",unique=True,blank=True,null=True)

    telegram_username = models.CharField(
        "Telegram username",
        max_length=32,
        blank=True,
        null=True,
        unique=True
    )
    telegram_id = models.BigIntegerField(
        "Telegram ID",
        blank=True,
        null=True,
        unique=True
    )

    def generate_link_code(self) -> str:
        # Генерируем короткий код (8 символов)
        code = uuid.uuid4().hex[:8]
        self.telegram_link_code = code
        self.save(update_fields=["telegram_link_code"])
        return code

    def __str__(self):
        return self.username
