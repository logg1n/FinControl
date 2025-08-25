import random
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from users.models import User
from transactions.models import Transaction

USERNAME = "demo_user"
NUM_TRANSACTIONS = 40

INCOME_CATEGORIES = ["Зарплата", "Фриланс", "Подарки", "Инвестиции"]
EXPENSE_CATEGORIES = ["Еда", "Транспорт", "Развлечения", "Коммуналка", "Одежда", "Здоровье"]
CURRENCIES = ["RUB", "USD", "EUR"]
PAYMENT_METHODS = ["cash", "card", "bank"]  # подставь свои значения из PAYMENT_METHODS

user = User.objects.get(username=USERNAME)
today = timezone.now().date()
start_date = today - timedelta(days=90)

for _ in range(NUM_TRANSACTIONS):
    tx_type = random.choice(["income", "expense"])
    if tx_type == "income":
        category = random.choice(INCOME_CATEGORIES)
        amount = Decimal(random.randint(1000, 10000))
    else:
        category = random.choice(EXPENSE_CATEGORIES)
        amount = Decimal(random.randint(100, 3000))

    Transaction.objects.create(
        user=user,
        date=start_date + timedelta(days=random.randint(0, 90)),
        amount=amount,
        currency=random.choice(CURRENCIES),
        type=tx_type,
        payment_method=random.choice(PAYMENT_METHODS),
        tag=f"Тестовая {category.lower()}",
        category=category,
        subcategory=""  # можно заполнить чем-то при желании
    )

print(f"✅ Добавлено {NUM_TRANSACTIONS} транзакций для пользователя '{USERNAME}'")
