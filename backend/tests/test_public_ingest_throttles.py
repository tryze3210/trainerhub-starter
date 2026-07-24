import pytest
from rest_framework.test import APIRequestFactory
from rest_framework.throttling import ScopedRateThrottle

from apps.affiliates.api.views import PublicAffiliateTrackingViewSet
from apps.analytics.api.views import AnalyticsEventCollectView
from apps.referrals.api.views import TrackReferralView


pytestmark = pytest.mark.django_db


def test_public_ingest_endpoints_use_scoped_throttles(settings):
    rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]

    assert AnalyticsEventCollectView.throttle_classes == [ScopedRateThrottle]
    assert AnalyticsEventCollectView.throttle_scope == "analytics_collect"
    assert "analytics_collect" in rates

    assert PublicAffiliateTrackingViewSet.throttle_classes == [ScopedRateThrottle]
    assert PublicAffiliateTrackingViewSet.throttle_scope == "affiliate_click"
    assert "affiliate_click" in rates

    assert TrackReferralView.throttle_classes == [ScopedRateThrottle]
    assert TrackReferralView.throttle_scope == "referral_track"
    assert "referral_track" in rates


def test_public_affiliate_click_rejects_invalid_payload_without_server_error():
    request = APIRequestFactory().post("/api/v1/affiliates/public/click/", {}, format="json")
    view = PublicAffiliateTrackingViewSet.as_view({"post": "click"})

    response = view(request)

    assert response.status_code == 400
    assert "partner_code" in response.data
    assert "client_key" in response.data
