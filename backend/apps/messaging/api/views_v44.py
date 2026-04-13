from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.messaging.services.media_pipeline import MessageMediaPipeline
from apps.messaging.services.escalation import SupportEscalationService

class InitiateMessageUploadAPIView(APIView):
    def post(self, request, conversation_id):
        service = MessageMediaPipeline()
        payload = service.initiate_upload(
            conversation_id=conversation_id,
            actor_id=request.user.id,
            kind=request.data.get("kind", "file"),
            filename=request.data.get("filename", "upload.bin"),
            content_type=request.data.get("content_type", "application/octet-stream"),
            file_size=int(request.data.get("file_size", 0)),
        )
        return Response(payload.__dict__, status=status.HTTP_201_CREATED)

class FinalizeMessageUploadAPIView(APIView):
    def post(self, request, upload_session_id):
        payload = MessageMediaPipeline().finalize_upload(
            upload_session_id=upload_session_id,
            checksum=request.data.get("checksum"),
        )
        return Response(payload)

class ConversationEscalationAPIView(APIView):
    def post(self, request, conversation_id):
        payload = SupportEscalationService().escalate_conversation(
            conversation_id=conversation_id,
            source_message_id=request.data.get("source_message_id"),
            reason_code=request.data.get("reason_code", "manual"),
            summary=request.data.get("summary", ""),
        )
        return Response(payload, status=status.HTTP_201_CREATED)
