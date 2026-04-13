from rest_framework import mixins, permissions, viewsets
from apps.invoicing.api.serializers import InvoiceSerializer
from apps.invoicing.models import Invoice


class MyInvoiceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user).order_by('-created_at')
