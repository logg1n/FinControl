import pandas as pd

import plotly.express as px
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import Sum

from .models import Transaction
from .forms import TransactionForm
from .filters import TransactionFilters
from .enums.service import get_enum_service
from .constants import CURRENCY_CHOICES


@login_required
def transaction_list(request):
    """
    Список транзакций с применением фильтров.
    """
    qs = Transaction.objects.filter(user=request.user)
    filtered_qs = TransactionFilters(qs).apply(request.GET)
    return render(request, "transactions/list.html", {
        "transactions": filtered_qs
    })


@login_required
def transaction_add(request):
    """
    Добавление транзакции.
    Категории и подкатегории подгружаются из builder-enum (JSON).
    Валюты — из CURRENCY_CHOICES.
    """
    svc = get_enum_service()

    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            # Приводим валюту к верхнему регистру
            if transaction.currency:
                transaction.currency = transaction.currency.upper()
            transaction.save()
            return redirect("transaction_list")
    else:
        form = TransactionForm()

    return render(request, "transactions/add.html", {
        "form": form,
        "categories": svc.list_categories(),
        "currencies": CURRENCY_CHOICES
    })


@login_required
def transaction_edit(request, pk):
    """
    Редактирование транзакции.
    """
    transaction = Transaction.objects.get(pk=pk, user=request.user)
    svc = get_enum_service()

    if request.method == "POST":
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            if transaction.currency:
                transaction.currency = transaction.currency.upper()
            transaction.save()
            return redirect("transaction_list")
    else:
        form = TransactionForm(instance=transaction)

    return render(request, "transactions/add.html", {
        "form": form,
        "categories": svc.list_categories(),
        "currencies": CURRENCY_CHOICES
    })


@login_required
def transaction_delete(request, pk):
    """
    Удаление транзакции.
    """
    transaction = Transaction.objects.get(pk=pk, user=request.user)
    if request.method == "POST":
        transaction.delete()
        return redirect("transaction_list")
    return render(request, "transactions/confirm_delete.html", {
        "transaction": transaction
    })

@login_required
def transactions_table_block(request):
    """
    Возвращает HTML-фрагмент <tbody> таблицы транзакций для AJAX-подгрузки.
    """
    qs = Transaction.objects.filter(user=request.user)
    qs = TransactionFilters(qs).apply(request.GET)

    html = render_to_string("transactions/_transactions_table_body.html", {
        "transactions": qs
    })
    return HttpResponse(html)



@login_required
def dashboard_view(request):
    # Фильтрация
    qs = Transaction.objects.filter(user=request.user)
    qs = TransactionFilters(qs).apply(request.GET)

    # KPI
    total_income = qs.filter(type='income').aggregate(sum=Sum('amount'))['sum'] or 0
    total_expense = qs.filter(type='expense').aggregate(sum=Sum('amount'))['sum'] or 0
    balance = total_income - total_expense

    # DataFrame для графиков
    df = pd.DataFrame(qs.values())
    fig_line_html = fig_pie_html = fig_bar_html = None
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])

        # Линия
        daily = df.groupby(['date', 'type'])['amount'].sum().reset_index()
        fig_line_html = px.line(daily, x='date', y='amount', color='type',
                                title="Динамика доходов и расходов", markers=True).to_html(full_html=False)

        # Круговая
        expenses = df[df['type'] == 'expense']
        if not expenses.empty:
            cat_sum = expenses.groupby('category')['amount'].sum().reset_index()
            fig_pie_html = px.pie(cat_sum, names='category', values='amount',
                                  title="Распределение расходов по категориям", hole=0.4).to_html(full_html=False)

            # Топ‑5 подкатегорий
            sub_sum = expenses.groupby('subcategory')['amount'].sum().reset_index()
            sub_sum = sub_sum.sort_values('amount', ascending=False).head(5)
            fig_bar_html = px.bar(sub_sum, x='amount', y='subcategory', orientation='h',
                                  title="Топ‑5 подкатегорий по расходам").to_html(full_html=False)

    return render(request, "transactions/dashboard.html", {
        "transactions": qs,
        "categories": get_enum_service().list_categories(),
        "currencies": CURRENCY_CHOICES,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "fig_line": fig_line_html,
        "fig_pie": fig_pie_html,
        "fig_bar": fig_bar_html
    })

