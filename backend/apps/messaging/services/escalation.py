class SupportEscalationService:
    def escalate_conversation(self, *, conversation_id, source_message_id=None, reason_code="manual", summary=""):
        return {
            "conversation_id": str(conversation_id),
            "source_message_id": str(source_message_id) if source_message_id else None,
            "reason_code": reason_code,
            "summary": summary,
            "status": "open",
        }
