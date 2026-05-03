from django.urls import path

from apps.events.api.views import (
    DispatchOutboxView,
    DomainEventDetailView,
    DomainEventListView,
    EmitEventView,
    EventHandlerListView,
    InboxMessageListView,
    OutboxHealthView,
    OutboxMessageDetailView,
    OutboxMessageListView,
    OutboxMessageMarkDeadView,
    OutboxMessageRetryView,
    RequeueStuckOutboxView,
)

urlpatterns = [
    path('handlers/', EventHandlerListView.as_view(), name='events-handlers-list'),
    path('', DomainEventListView.as_view(), name='events-list'),
    path('<uuid:event_id>/', DomainEventDetailView.as_view(), name='events-detail'),
    path('outbox/', OutboxMessageListView.as_view(), name='events-outbox-list'),
    path('outbox/health/', OutboxHealthView.as_view(), name='events-outbox-health'),
    path('outbox/<uuid:message_id>/', OutboxMessageDetailView.as_view(), name='events-outbox-detail'),
    path('outbox/<uuid:message_id>/retry/', OutboxMessageRetryView.as_view(), name='events-outbox-retry'),
    path('outbox/<uuid:message_id>/dead/', OutboxMessageMarkDeadView.as_view(), name='events-outbox-dead'),
    path('outbox/requeue-stuck/', RequeueStuckOutboxView.as_view(), name='events-outbox-requeue-stuck'),
    path('outbox/dispatch/', DispatchOutboxView.as_view(), name='events-outbox-dispatch'),
    path('inbox/', InboxMessageListView.as_view(), name='events-inbox-list'),
    path('emit/', EmitEventView.as_view(), name='events-emit'),
]
