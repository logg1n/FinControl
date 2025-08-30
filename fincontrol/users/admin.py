from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "telegram_username", "telegram_id", "is_active")
    search_fields = ("username", "email", "telegram_username", "telegram_id")
    fieldsets = UserAdmin.fieldsets + (
        ("Telegram", {"fields": ("telegram_username", "telegram_id")}),
    )
