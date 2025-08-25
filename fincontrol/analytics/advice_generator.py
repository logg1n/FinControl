import os
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from transactions.models import Transaction
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_spending_summary(user, days=30):
    today = timezone.now().date()
    start_date = today - timedelta(days=days)

    expenses = (
        Transaction.objects
        .filter(user=user, type="expense", date__gte=start_date)
        .values("category")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    if not expenses:
        return "Нет расходов за выбранный период."

    total_spent = sum(e["total"] for e in expenses)
    avg_spent = total_spent / len(expenses)

    summary_lines = [
        f"Общие расходы: {total_spent:.2f}",
        f"Средние расходы по категориям: {avg_spent:.2f}"
    ]
    for e in expenses:
        summary_lines.append(f"{e['category']}: {e['total']:.2f}")

    return "\n".join(summary_lines)

def get_ai_advice(user, days=30):
    summary = generate_spending_summary(user, days=days)

    prompt = (
        "Ты — финансовый помощник. "
        "На основе этих данных о тратах за последние 30 дней "
        "сформулируй 3–5 конкретных и полезных совета по оптимизации бюджета.\n\n"
        f"{summary}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()
