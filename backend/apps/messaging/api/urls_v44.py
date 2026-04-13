from django.urls import path
from .views_v44 import InitiateMessageUploadAPIView, FinalizeMessageUploadAPIView, ConversationEscalationAPIView

urlpatterns = [
    path('conversations/<uuid:conversation_id>/uploads/initiate/', InitiateMessageUploadAPIView.as_view()),
    path('uploads/<uuid:upload_session_id>/finalize/', FinalizeMessageUploadAPIView.as_view()),
    path('conversations/<uuid:conversation_id>/escalate/', ConversationEscalationAPIView.as_view()),
]
