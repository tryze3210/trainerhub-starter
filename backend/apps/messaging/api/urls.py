from django.urls import path
from apps.messaging.api.views import MyInboxView, ConversationMessagesView, SendMessageView, MarkReadView

urlpatterns = [
    path("me/inbox/", MyInboxView.as_view()),
    path("conversations/<uuid:conversation_id>/messages/", ConversationMessagesView.as_view()),
    path("conversations/<uuid:conversation_id>/send/", SendMessageView.as_view()),
    path("conversations/<uuid:conversation_id>/mark-read/", MarkReadView.as_view()),
]
