from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
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
