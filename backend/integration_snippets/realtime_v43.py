"""
Integration seam for Django Channels / websocket gateway.

Expected flow:
- Message persisted in messaging domain
- Publish conversation event to websocket layer
- Push unread counter updates to participants
- Optional fallback via notifications slice
"""


def publish_message_created(message):
    return {
        "event": "message.created",
        "conversation_id": str(message.conversation_id),
        "message_id": str(message.id),
    }
