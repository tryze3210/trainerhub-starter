from django.urls import path

from apps.public_catalog.api.views import FeaturedCatalogView, PublicCatalogItemDetailView, PublicCatalogView

urlpatterns = [
    path('items/', PublicCatalogView.as_view(), name='public-catalog-items'),
    path('featured/', FeaturedCatalogView.as_view(), name='public-catalog-featured'),
    path('<str:entity_type>/<slug:slug>/', PublicCatalogItemDetailView.as_view(), name='public-catalog-item-detail'),
]
