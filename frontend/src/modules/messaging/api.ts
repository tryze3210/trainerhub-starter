import { apiRequest } from '@/lib/api-client';
import type { Conversation, Message, MessagingInbox } from '@/types/api';

export const messagingApi = {
  getInbox: () =>
    apiRequest<MessagingInbox>('/messaging/me/inbox/', {
      auth: true,
    }),

  startConversation: (payload: { recipient_id: string; subject?: string; body?: string }) =>
    apiRequest<Conversation>('/messaging/conversations/start/', {
      auth: true,
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getMessages: (conversationId: string) =>
    apiRequest<Message[]>(`/messaging/conversations/${conversationId}/messages/`, {
      auth: true,
    }),

  sendMessage: (conversationId: string, body: string) =>
    apiRequest<Message>(`/messaging/conversations/${conversationId}/send/`, {
      auth: true,
      method: 'POST',
      body: JSON.stringify({ body }),
    }),

  markRead: (conversationId: string) =>
    apiRequest<{ status: string }>(`/messaging/conversations/${conversationId}/mark-read/`, {
      auth: true,
      method: 'POST',
    }),
};
