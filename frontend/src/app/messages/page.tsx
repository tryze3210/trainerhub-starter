'use client';

import { useEffect, useMemo, useState } from 'react';

import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { messagingApi } from '@/modules/messaging/api';
import type { Conversation, Message, MessagingInbox } from '@/types/api';

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export default function MessagesPage() {
  const { user } = useAuthSession();
  const [inbox, setInbox] = useState<MessagingInbox | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedId, setSelectedId] = useState('');
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
      setSelectedId((current) => current || payload.results[0]?.id || '');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить сообщения');
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
    void loadMessages(selectedId);
  }, [selectedId]);

  const selected = useMemo(
    () => inbox?.results.find((item) => item.id === selectedId) || inbox?.results[0] || null,
    [inbox, selectedId]
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
      setSelectedId(conversation.id);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось создать диалог');
    }
  }

  async function send() {
    if (!selectedId) return;
    setMessage('');
    try {
      await messagingApi.sendMessage(selectedId, body);
      setBody('');
      await loadMessages(selectedId);
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось отправить сообщение');
    }
  }

  return (
    <ProtectedPage title="Messages" description="Диалоги доступны после входа.">
      <section className="stack" style={{ gap: 24 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 8 }}>
            <span className="badge secondary">Messaging</span>
            <h1>Сообщения</h1>
            <p className="lead">Диалоги trainer ↔ student, системные сообщения и notification hooks в одном inbox.</p>
          </div>
          <button className="button secondary" onClick={() => void load()} disabled={loading} type="button">Обновить</button>
        </div>

        {message ? <div className="card">{message}</div> : null}

        <div className="grid-4">
          <div className="card"><div className="kpi"><span className="muted">Диалогов</span><strong>{inbox?.results.length || 0}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Unread</span><strong>{inbox?.unread_total || 0}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Role</span><strong>{user?.active_role || 'user'}</strong></div></div>
          <div className="card"><div className="kpi"><span className="muted">Selected</span><strong>{selected ? selected.unread_count : 0}</strong></div></div>
        </div>

        <div className="card">
          <h2 className="title-md">Новый диалог</h2>
          <div className="grid-3" style={{ marginTop: 14 }}>
            <input className="input" value={recipientId} onChange={(event) => setRecipientId(event.target.value)} placeholder="recipient user id" />
            <input className="input" value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="subject" />
            <input className="input" value={startBody} onChange={(event) => setStartBody(event.target.value)} placeholder="first message" />
          </div>
          <button className="button secondary" style={{ marginTop: 12 }} onClick={() => void startConversation()} type="button">Начать диалог</button>
        </div>

        <div className="grid-2">
          <div className="card">
            <h2 className="title-md">Inbox</h2>
            <div className="stack" style={{ gap: 10, marginTop: 14 }}>
              {loading ? <p className="muted">Загружаем inbox...</p> : null}
              {(inbox?.results || []).map((conversation) => (
                <button
                  className={`card compact text-left ${selectedId === conversation.id ? 'is-active' : ''}`}
                  key={conversation.id}
                  onClick={() => setSelectedId(conversation.id)}
                  type="button"
                >
                  <div className="row">
                    <div className="stack" style={{ gap: 4 }}>
                      <div className="inline">
                        <span className="badge secondary">{conversation.kind}</span>
                        {conversation.unread_count ? <span className="badge warning">{conversation.unread_count} unread</span> : null}
                      </div>
                      <strong>{conversation.subject || 'Диалог'}</strong>
                      <span className="muted">{conversation.last_message?.body || 'Пока нет сообщений'}</span>
                    </div>
                    <span className="muted">{formatDate(conversation.last_message_at)}</span>
                  </div>
                </button>
              ))}
              {!loading && !inbox?.results.length ? <p className="muted">Диалогов пока нет.</p> : null}
            </div>
          </div>

          <div className="card">
            <h2 className="title-md">{selected?.subject || 'Диалог'}</h2>
            <div className="stack" style={{ gap: 10, marginTop: 14 }}>
              {messages.map((item) => (
                <article className="card compact" key={item.id}>
                  <div className="row">
                    <div className="inline">
                      <span className={item.message_type === 'system' ? 'badge secondary' : 'badge success'}>{item.message_type}</span>
                      <strong>{item.sender_email || 'System'}</strong>
                    </div>
                    <span className="muted">{formatDate(item.created_at)}</span>
                  </div>
                  <p style={{ marginTop: 8 }}>{item.body}</p>
                </article>
              ))}
              {selected && !messages.length ? <p className="muted">В этом диалоге пока нет сообщений.</p> : null}
              {selected ? (
                <div className="stack" style={{ gap: 8 }}>
                  <textarea className="textarea" rows={4} value={body} onChange={(event) => setBody(event.target.value)} placeholder="Написать сообщение" />
                  <button className="button" onClick={() => void send()} type="button">Отправить</button>
                </div>
              ) : (
                <p className="muted">Выбери диалог слева или создай новый.</p>
              )}
            </div>
          </div>
        </div>
      </section>
    </ProtectedPage>
  );
}
