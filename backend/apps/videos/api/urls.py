from django.urls import path
from .views import (
    UploadIntentCreateApi,
    UploadIntentCompleteApi,
    MediaAssetDetailApi,
    VideoListCreateApi,
    VideoDetailApi,
    VideoAccessUrlApi,
)

urlpatterns = [
    path("upload-intents/", UploadIntentCreateApi.as_view(), name="video-upload-intent"),
    path("upload-intents/<uuid:media_asset_id>/complete/", UploadIntentCompleteApi.as_view(), name="video-upload-complete"),
    path("media-assets/<uuid:media_asset_id>/", MediaAssetDetailApi.as_view(), name="media-asset-detail"),
    path("", VideoListCreateApi.as_view(), name="video-list-create"),
    path("<uuid:pk>/", VideoDetailApi.as_view(), name="video-detail"),
    path("<uuid:video_id>/access-url/", VideoAccessUrlApi.as_view(), name="video-access-url"),
]
