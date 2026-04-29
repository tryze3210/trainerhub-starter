from __future__ import annotations

from rest_framework import permissions, response, views

from apps.admin_marketplace.selectors import MarketplaceHealthSelector


class AdminMarketplaceHealthView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except (TypeError, ValueError):
            days = 30
        return response.Response(MarketplaceHealthSelector.build(days=days))
