from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('config.api')),
    path('api/v1/auth/', include('apps.authn.api.urls')),
    path('api/v1/content/', include('apps.content.api.urls')),
    path('api/v1/trainers/', include('apps.trainers.api.urls')),
    path('api/v1/onboarding/', include('apps.onboarding.api.urls')),
    path('api/v1/public-catalog/', include('apps.public_catalog.api.urls')),
    path('api/v1/videos/', include('apps.videos.api.urls')),
    path('api/v1/trainer-cms/', include('apps.trainer_cms.api.urls')),
    path('api/v1/media-assets/', include('apps.media_assets.api.urls')),
    path('api/v1/categories/', include('apps.categories.api.urls')),
    path('api/v1/tags/', include('apps.categories.api.tag_urls')),
    path('api/v1/favorites/', include('apps.favorites.api.urls')),
    path('api/v1/customer/', include('apps.customers.api.urls')),
    path('api/v1/notifications/', include('apps.notifications.api.urls')),
    path('api/v1/reviews/', include('apps.reviews.api.urls')),
    path('api/v1/moderation/', include('apps.moderation.api.urls')),
    path('api/v1/payouts/', include('apps.payouts.api.urls')),
    path('api/v1/analytics/', include('apps.analytics.api.urls')),
    path('api/v1/admin/', include('apps.admin_marketplace.api.urls')),
    path('api/v1/audit/', include('apps.audit.api.urls')),
    path('api/v1/platform-settings/', include('apps.platform_settings.api.urls')),
]
