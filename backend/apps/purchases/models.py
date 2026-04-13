from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel
from apps.customers.models import CustomerProfile
from apps.trainers.models import TrainerProfile
from apps.products.models import Product

class Purchase(UUIDModel, TimeStampedModel):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.PROTECT, related_name="purchases")
    trainer = models.ForeignKey(TrainerProfile, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    status = models.CharField(max_length=32, default="pending")
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2)
    platform_commission_amount = models.DecimalField(max_digits=12, decimal_places=2)
    trainer_net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default="RUB")
