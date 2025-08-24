from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.template.loader import render_to_string
from django.http import HttpResponse
import pandas as pd
import plotly.express as px

from transactions.models import Transaction
from transactions.filters import TransactionFilters


@login_required
def dashboard_block(request):
    """
    Возвращает HTML-фрагмент с KPI и графиками для AJAX-подгрузки.
    """
    qs = Transaction.objects.filter(user=request.user)
    qs = TransactionFilters(qs).apply(request.GET)

    # KPI
    total_income = qs.filter(type='income').aggregate(sum=Sum('amount'))['sum'] or 0
    total_expense = qs.filter(type='expense').aggregate(sum=Sum('amount'))['sum'] or 0
    balance = total_income - total_expense

    # DataFrame для графиков
    df = pd.DataFrame(qs.values("date", "type", "amount", "category", "subcategory"))
    fig_line_html = fig_pie_html = fig_bar_html = None

    if not df.empty:
        df = df.dropna(subset=['date', 'amount'])
        df['date'] = pd.to_datetime(df['date'])

        # Линия
        daily = df.groupby(['date', 'type'])['amount'].sum().reset_index()
        if not daily.empty:
            fig_line_html = px.line(
                daily, x='date', y='amount', color='type',
                title="Динамика доходов и расходов", markers=True
            ).to_html(full_html=False)

        # Круговая и топ‑5
        expenses = df[df['type'] == 'expense']
        if not expenses.empty:
            cat_sum = expenses.groupby('category')['amount'].sum().reset_index()
            if not cat_sum.empty:
                fig_pie_html = px.pie(
                    cat_sum, names='category', values='amount',
                    title="Распределение расходов по категориям", hole=0.4
                ).to_html(full_html=False)

            sub_sum = expenses.groupby('subcategory')['amount'].sum().reset_index()
            sub_sum = sub_sum.sort_values('amount', ascending=False).head(5)
            if not sub_sum.empty:
                fig_bar_html = px.bar(
                    sub_sum, x='amount', y='subcategory', orientation='h',
                    title="Топ‑5 подкатегорий по расходам"
                ).to_html(full_html=False)

    html = render_to_string("dashboard/_dashboard_block.html", {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "fig_line": fig_line_html,
        "fig_pie": fig_pie_html,
        "fig_bar": fig_bar_html
    })
    return HttpResponse(html)
