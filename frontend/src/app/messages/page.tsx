'use client';

import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { messagingApi } from '@/modules/messaging/api';
import {
  CustomerCabinetShell,
  CustomerEmptyState,
  CustomerErrorState,
  CustomerLoadingState,
  CustomerMetricCard,
  CustomerStatusBadge,
  type CustomerMetric,
} from '@/modules/customer-cabinet/components';
import { formatCustomerDate } from '@/modules/customer-cabinet/components/customer-format';
import type { Conversation, Message, MessagingInbox } from '@/types/api';

function senderName(message: Message) {
  if (message.sender_email) return message.sender_email;
  return 'TrainerHub';
}

function conversationTitle(conversation: Conversation) {
  return conversation.subject || conversation.last_message?.body?.slice(0, 48) || 'Диалог';
}

export default function MessagesPage() {
  const [inbox, setInbox] = useState<MessagingInbox | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeConversationId, setActiveConversationId] = useState('');
  const [recipientId, setRecipientId] = useState('');
  const [subject, setSubject] = useState('');
  const [startBody, setStartBody] = useState('');
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load() {
    setLoading(true);
    setMessage('');
    try {
      const payload = await messagingApi.getInbox();
      setInbox(payload);
      setActiveConversationId((current) => current || payload.results[0]?.id || '');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  }

  async function loadMessages(conversationId: string) {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    try {
      const rows = await messagingApi.getMessages(conversationId);
      setMessages(rows);
      await messagingApi.markRead(conversationId);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить диалог');
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    void loadMessages(activeConversationId);
  }, [activeConversationId]);

  const activeConversation = useMemo(
    () => inbox?.results.find((item) => item.id === activeConversationId) || inbox?.results[0] || null,
    [inbox, activeConversationId]
  );

  async function startConversation() {
    setMessage('');
    try {
      const conversation = await messagingApi.startConversation({
        recipient_id: recipientId,
        subject,
        body: startBody,
      });
      setRecipientId('');
      setSubject('');
      setStartBody('');
      await load();
      setActiveConversationId(conversation.id);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось создать диалог');
    }
  }

  async function send() {
    if (!activeConversationId || !body.trim()) return;
    setMessage('');
    try {
      await messagingApi.sendMessage(activeConversationId, body);
      setBody('');
      await loadMessages(activeConversationId);
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось отправить сообщение');
    }
  }

  const metrics: CustomerMetric[] = [
    { label: 'Диалогов', value: inbox?.results.length || 0, hint: 'Всего', tone: 'neutral' },
    { label: 'Непрочитанных', value: inbox?.unread_total || 0, hint: 'Требуют внимания', tone: inbox?.unread_total ? 'warning' : 'success' },
  ];

  return (
    <ProtectedPage title="Сообщения" description="Диалоги доступны после входа.">
      <CustomerCabinetShell
        title="Сообщения"
        description="Диалоги с тренерами, ответы по программам и системные уведомления."
        actions={<button className="premium-secondary-button" type="button" onClick={() => void load()} disabled={loading}>Обновить</button>}
      >
        <div className="customer-metric-grid">
          {metrics.map((metric) => <CustomerMetricCard key={metric.label} metric={metric} />)}
        </div>
        {message ? <CustomerErrorState message={message} onRetry={() => void load()} /> : null}
        {loading ? <CustomerLoadingState /> : null}

        <section className="customer-section-card">
          <div className="customer-section-header"><h2>Новый диалог</h2></div>
          <div className="customer-message-composer">
            <input className="input" value={recipientId} onChange={(event) => setRecipientId(event.target.value)} placeholder="Получатель" />
            <input className="input" value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Тема" />
            <textarea className="textarea" value={startBody} onChange={(event) => setStartBody(event.target.value)} placeholder="Первое сообщение" />
            <button className="premium-secondary-button" type="button" onClick={() => void startConversation()}>Написать сообщение</button>
          </div>
        </section>

        <div className="customer-message-layout">
          <section className="customer-conversation-list">
            {(inbox?.results || []).map((conversation) => (
              <button
                className={activeConversationId === conversation.id ? 'customer-conversation-card customer-conversation-card-active' : 'customer-conversation-card'}
                key={conversation.id}
                type="button"
                onClick={() => setActiveConversationId(conversation.id)}
              >
                <CustomerStatusBadge tone={conversation.unread_count ? 'warning' : 'neutral'}>
                  {conversation.unread_count ? `${conversation.unread_count} новых` : 'Прочитано'}
                </CustomerStatusBadge>
                <strong>{conversationTitle(conversation)}</strong>
                <span>{conversation.last_message?.body || 'Пока нет сообщений'}</span>
                <small>{formatCustomerDate(conversation.last_message_at || conversation.updated_at || conversation.created_at)}</small>
              </button>
            ))}
            {!loading && !inbox?.results.length ? <CustomerEmptyState title="Диалогов пока нет" description="Новые сообщения появятся здесь." actionHref="/catalog" actionLabel="Открыть каталог" /> : null}
          </section>

          <section className="customer-message-thread">
            <div className="customer-section-header">
              <h2>{activeConversation ? conversationTitle(activeConversation) : 'Диалог'}</h2>
            </div>
            {messages.map((item) => (
              <article className="customer-message-bubble" key={item.id}>
                <div>
                  <strong>{senderName(item)}</strong>
                  <span>{formatCustomerDate(item.created_at)}</span>
                </div>
                <p>{item.body}</p>
              </article>
            ))}
            {activeConversation && !messages.length ? <CustomerEmptyState title="В диалоге пока нет сообщений" description="Напишите первое сообщение ниже." actionHref="/messages" actionLabel="Остаться здесь" /> : null}
            {activeConversation ? (
              <div className="customer-message-composer">
                <textarea className="textarea" rows={4} value={body} onChange={(event) => setBody(event.target.value)} placeholder="Написать сообщение" />
                <button className="premium-primary-button" type="button" onClick={() => void send()}>Отправить</button>
              </div>
            ) : (
              <CustomerEmptyState title="Выберите диалог" description="Откройте существующий диалог или создайте новый." actionHref="/messages" actionLabel="Остаться здесь" />
            )}
          </section>
        </div>
      </CustomerCabinetShell>
    </ProtectedPage>
  );
}
