class PaymentGatewayAdapter:
    def create_checkout(self, *, order, payment):
        return {
            'external_payment_id': f'mock-{payment.id}',
            'checkout_url': f'https://payments.example/checkout/{payment.id}',
            'payload': {'mock': True, 'order_id': str(order.id)},
        }
