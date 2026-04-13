import json
from rest_framework import status, views
from rest_framework.response import Response
from apps.billing.models import CheckoutSession
from apps.payments.gateway import PaymentGateway
from apps.payments.services import PaymentService


class ProviderWebhookView(views.APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        signature = request.headers.get('X-Provider-Signature', '')
        payload = request.body
        gateway = PaymentGateway()
        if not gateway.verify_webhook(payload=payload, signature=signature):
            return Response({'detail': 'Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

        event = json.loads(payload.decode('utf-8'))
        if event.get('type') == 'checkout.paid':
            checkout = CheckoutSession.objects.get(provider_session_id=event['provider_session_id'])
            PaymentService.finalize_checkout_paid(checkout_session=checkout, provider_payment_id=event['provider_payment_id'], request=request)

        return Response({'ok': True})
