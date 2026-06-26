from django.urls import path
from apps.messaging.api.views import (
    ConversationMessagesView,
    CreateSystemMessageView,
    MarkReadView,
    MyInboxView,
    SendMessageView,
    StartConversationView,
)

urlpatterns = [
    path("me/inbox/", MyInboxView.as_view(), name="messaging-inbox"),
    path("conversations/start/", StartConversationView.as_view(), name="messaging-start-conversation"),
    path("conversations/<uuid:conversation_id>/messages/", ConversationMessagesView.as_view(), name="messaging-conversation-messages"),
    path("conversations/<uuid:conversation_id>/send/", SendMessageView.as_view(), name="messaging-send-message"),
    path("conversations/<uuid:conversation_id>/system/", CreateSystemMessageView.as_view(), name="messaging-system-message"),
    path("conversations/<uuid:conversation_id>/mark-read/", MarkReadView.as_view(), name="messaging-mark-read"),
]
