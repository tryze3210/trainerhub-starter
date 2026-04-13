export async function fetchMyInbox(client: any) {
  return client.get('/api/v1/messaging/me/inbox/');
}

export async function fetchConversationMessages(client: any, conversationId: string) {
  return client.get(`/api/v1/messaging/conversations/${conversationId}/messages/`);
}

export async function sendMessage(client: any, conversationId: string, body: string) {
  return client.post(`/api/v1/messaging/conversations/${conversationId}/send/`, { body });
}

export async function markConversationRead(client: any, conversationId: string) {
  return client.post(`/api/v1/messaging/conversations/${conversationId}/mark-read/`);
}
