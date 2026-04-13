from rest_framework import serializers
from apps.invoicing.models import Invoice


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['id', 'order_id', 'payment_id', 'document_type', 'document_number', 'currency', 'gross_amount', 'payload', 'created_at']
