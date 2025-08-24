# dashboard/views.py
import pandas as pd
import plotly.express as px
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from transactions.models import Transaction
from transactions.filters import TransactionFilters

@login_required
def analytics_block(request):
    qs = Transaction.objects.filter(user=request.user)
    qs = TransactionFilters(qs).apply(request.GET)
    df = pd.DataFrame(qs.values())

    if df.empty:
        return render(request, "dashboard/analytics_block.html", {"no_data": True})

    df['date'] = pd.to_datetime(df['date'])

    daily = df.groupby(['date', 'type'])['amount'].sum().reset_index()
    fig_line = px.line(daily, x='date', y='amount', color='type', title="Динамика доходов и расходов", markers=True)

    expenses = df[df['type'] == 'expense']
    cat_sum = expenses.groupby('category')['amount'].sum().reset_index()
    fig_pie = px.pie(cat_sum, names='category', values='amount', title="Распределение расходов по категориям", hole=0.4)

    sub_sum = expenses.groupby('subcategory')['amount'].sum().reset_index()
    sub_sum = sub_sum.sort_values('amount', ascending=False).head(5)
    fig_bar = px.bar(sub_sum, x='amount', y='subcategory', orientation='h', title="Топ‑5 подкатегорий по расходам")

    return render(request, "dashboard/analytics_block.html", {
        "fig_line": fig_line.to_html(full_html=False),
        "fig_pie": fig_pie.to_html(full_html=False),
        "fig_bar": fig_bar.to_html(full_html=False),
    })
