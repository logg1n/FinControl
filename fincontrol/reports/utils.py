from transactions.models import Transaction

ALLOWED_SORT = {
    "date", "-date", "amount", "-amount",
    "category", "-category", "subcategory", "-subcategory",
    "currency", "-currency", "type", "-type",
    "payment_method", "-payment_method", "tag", "-tag",
}

def get_filtered_transactions(request):
    qs = Transaction.objects.filter(user=request.user)

    if category := request.GET.get("category"):
        qs = qs.filter(category=category)
    if subcategory := request.GET.get("subcategory"):
        qs = qs.filter(subcategory=subcategory)
    if tx_type := request.GET.get("type"):
        qs = qs.filter(type=tx_type)
    if payment_method := request.GET.get("payment_method"):
        qs = qs.filter(payment_method=payment_method)
    if currency := request.GET.get("currency"):
        qs = qs.filter(currency=currency)
    if tag_query := request.GET.get("tag"):
        qs = qs.filter(tag__icontains=tag_query)
    if date_from := request.GET.get("date_from"):
        qs = qs.filter(date__gte=date_from)
    if date_to := request.GET.get("date_to"):
        qs = qs.filter(date__lte=date_to)

    sort = request.GET.get("sort")
    if sort in ALLOWED_SORT:
        qs = qs.order_by(sort)
    else:
        qs = qs.order_by("-date")

    return qs
