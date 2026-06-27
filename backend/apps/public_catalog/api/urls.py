from django.urls import path

from apps.public_catalog.api.views import (
    FeaturedCatalogView,
    PublicCatalogItemDetailView,
    PublicCatalogView,
    PublicContentLandingView,
    PublicMarketplaceHomeView,
    PublicTrainerLandingView,
)

urlpatterns = [
    path('', PublicMarketplaceHomeView.as_view(), name='public-marketplace-home'),
    path('items/', PublicCatalogView.as_view(), name='public-catalog-items'),
    path('featured/', FeaturedCatalogView.as_view(), name='public-catalog-featured'),
    path('landing/<str:entity_type>/<slug:slug>/', PublicContentLandingView.as_view(), name='public-marketplace-content-landing'),
    path('trainers/<slug:slug>/landing/', PublicTrainerLandingView.as_view(), name='public-marketplace-trainer-landing'),
    path('<str:entity_type>/<slug:slug>/', PublicCatalogItemDetailView.as_view(), name='public-catalog-item-detail'),
]
