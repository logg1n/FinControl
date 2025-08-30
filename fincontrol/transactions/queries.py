from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Sum
from asgiref.sync import sync_to_async
from typing import Optional
from transactions.models import Transaction

# ===== Вспомогательная функция фильтрации по периоду =====
def _apply_period_filter(qs, start_date: Optional[date], end_date: Optional[date]):
    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)
    return qs

# ===== Общие суммы =====
@sync_to_async
def get_today_expenses(user_id: int) -> float:
    today = timezone.now().date()
    return Transaction.objects.filter(
        user__telegram_id=user_id,
        date=today,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0

@sync_to_async
def get_week_expenses(user_id: int) -> float:
    start = timezone.now().date() - timedelta(days=7)
    return Transaction.objects.filter(
        user__telegram_id=user_id,
        date__gte=start,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0

@sync_to_async
def get_month_expenses(user_id: int) -> float:
    start = timezone.now().date().replace(day=1)
    return Transaction.objects.filter(
        user__telegram_id=user_id,
        date__gte=start,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0

@sync_to_async
def get_balance(user_id: int) -> float:
    income = Transaction.objects.filter(
        user__telegram_id=user_id,
        type='income'
    ).aggregate(sum=Sum('amount'))['sum'] or 0
    expense = Transaction.objects.filter(
        user__telegram_id=user_id,
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0
    return income - expense

@sync_to_async
def get_first_transaction_date(user_id: int):
    first_tx = Transaction.objects.filter(
        user__telegram_id=user_id
    ).order_by('date').first()
    return first_tx.date if first_tx else None

@sync_to_async
def get_last_transaction_date(user_id: int):
    last_tx = Transaction.objects.filter(
        user__telegram_id=user_id
    ).order_by('-date').first()
    return last_tx.date if last_tx else None

@sync_to_async
def get_period_expenses(user_id: int, start_date: date, end_date: date) -> float:
    return Transaction.objects.filter(
        user__telegram_id=user_id,
        date__range=(start_date, end_date),
        type='expense'
    ).aggregate(sum=Sum('amount'))['sum'] or 0

# ===== Отчёты по категориям =====
@sync_to_async
def get_all_categories_report(user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> str:
    qs = Transaction.objects.filter(
        user__telegram_id=user_id,
        type='expense'
    )
    qs = _apply_period_filter(qs, start_date, end_date)

    qs = qs.values('category').annotate(total=Sum('amount')).order_by('-total')

    if not qs:
        return "⚠️ Нет данных по категориям."

    lines = ["📋 Отчёт по всем категориям:"]
    for row in qs:
        category = row['category'] or "Без категории"
        total = row['total'] or 0
        lines.append(f"— {category}: {total:.2f}")
    return "\n".join(lines)

@sync_to_async
def get_category_expenses(user_id: int, category: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> float:
    qs = Transaction.objects.filter(
        user__telegram_id=user_id,
        category__iexact=category,
        type='expense'
    )
    qs = _apply_period_filter(qs, start_date, end_date)
    return qs.aggregate(sum=Sum('amount'))['sum'] or 0

@sync_to_async
def get_subcategory_expenses(user_id: int, subcategory: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> float:
    qs = Transaction.objects.filter(
        user__telegram_id=user_id,
        subcategory__iexact=subcategory,
        type='expense'
    )
    qs = _apply_period_filter(qs, start_date, end_date)
    return qs.aggregate(sum=Sum('amount'))['sum'] or 0
