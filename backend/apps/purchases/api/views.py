from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from apps.products.models import Product
from apps.purchases.models import Purchase
from apps.payments.services.create_stub_payment import CreateStubCheckoutService
from .serializers import PurchaseSerializer, CheckoutSerializer


class PurchaseCheckoutApi(generics.GenericAPIView):
    serializer_class = CheckoutSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not hasattr(request.user, "customer_profile"):
            return Response({"detail": "Customer profile not found."}, status=status.HTTP_400_BAD_REQUEST)
        product = get_object_or_404(Product, pk=serializer.validated_data["product_id"], status="published", is_deleted=False)
        purchase, payment = CreateStubCheckoutService().execute(customer_profile=request.user.customer_profile, product=product)
        return Response(
            {
                "purchase": PurchaseSerializer(purchase).data,
                "payment": {
                    "id": str(payment.id),
                    "status": payment.status,
                    "provider": payment.provider,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "confirm_url": f"/api/v1/payments/{payment.id}/stub-confirm/",
                },
            },
            status=status.HTTP_201_CREATED,
        )


class PurchaseListApi(generics.ListAPIView):
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Purchase.objects.filter(customer=self.request.user.customer_profile).select_related("product", "trainer")
