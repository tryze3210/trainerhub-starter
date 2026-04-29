from rest_framework import permissions, response, status, viewsets

from apps.customers.selectors import CustomerMarketplaceHubSelector


class CustomerMarketplaceHubViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    selector = CustomerMarketplaceHubSelector()

    def list(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except (TypeError, ValueError):
            days = 30
        return response.Response(self.selector.build(user=request.user, days=days), status=status.HTTP_200_OK)
