from django.urls import path

from apps.accounts.api.views import AccountProfileView, AccountSettingsView, CabinetView, SwitchRoleView

urlpatterns = [
    path('profile/', AccountProfileView.as_view(), name='accounts-profile'),
    path('settings/', AccountSettingsView.as_view(), name='accounts-settings'),
    path('switch-role/', SwitchRoleView.as_view(), name='accounts-switch-role'),
    path('cabinet/', CabinetView.as_view(), name='accounts-cabinet'),
]
