from django.urls import path

from apps.events.api.views import EmitEventView, InboxMessageListView, OutboxMessageListView

urlpatterns = [
    path('outbox/', OutboxMessageListView.as_view(), name='events-outbox-list'),
    path('inbox/', InboxMessageListView.as_view(), name='events-inbox-list'),
    path('emit/', EmitEventView.as_view(), name='events-emit'),
]
