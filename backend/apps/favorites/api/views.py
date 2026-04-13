from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from apps.favorites.api.serializers import FavoriteSerializer
from apps.favorites.models import Favorite

class FavoriteViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Favorite.objects.filter(user=self.request.user).order_by('-created_at')
        target_type = self.request.query_params.get('target_type')
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
