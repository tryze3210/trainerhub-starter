from django.urls import path

from apps.tenancy.api.views import TenantContextView, TenantMembershipListView, TenantSwitchView

urlpatterns = [
    path('context/', TenantContextView.as_view(), name='tenant-context'),
    path('memberships/', TenantMembershipListView.as_view(), name='tenant-memberships'),
    path('switch/', TenantSwitchView.as_view(), name='tenant-switch'),
]
