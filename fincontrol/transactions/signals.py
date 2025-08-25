from django.db.models.signals import post_save
from django.dispatch import receiver
from transactions.models import Transaction
from services.advice_triggers import trigger_on_new_transaction, trigger_anomaly
import asyncio

@receiver(post_save, sender=Transaction)
def transaction_created(sender, instance, created, **kwargs):
    if created:
        asyncio.create_task(trigger_on_new_transaction(instance))
        asyncio.create_task(trigger_anomaly(instance))
