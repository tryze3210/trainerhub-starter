'use client';

import { Suspense } from 'react';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { privateApi } from '@/lib/api';
import type { Payment } from '@/types/api';

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

function PaymentDetailPageContent() {
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [payment, setPayment] = useState<Payment | null>(null);
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);

  const providerRedirect = searchParams.get('provider_redirect') === '1';

  async function load() {
    if (!params?.id) return;
    try {
      setMsg('');
      const data = await privateApi.getPayment(params.id);
      setPayment(data);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить платёж');
    }
  }

  useEffect(() => {
    void load();
  }, [params?.id]);

  async function confirmMock() {
    if (!params?.id) return;
    try {
      setBusy(true);
      await privateApi.confirmMockPayment(params.id);
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось подтвердить платёж');
    } finally {
      setBusy(false);
    }
  }

  async function cancelMock() {
    if (!params?.id) return;
    try {
      setBusy(true);
      await privateApi.cancelMockPayment(params.id);
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось отменить платёж');
    } finally {
      setBusy(false);
    }
  }

  const contract = useMemo(() => (payment?.provider_payload || {}) as Record<string, string>, [payment?.provider_payload]);

  return (
    <ProtectedPage title="Детали платежа" description="Страница платежа доступна только после входа.">
      {msg ? <div className="card error">{msg}</div> : null}
      {!payment ? (
        <div className="card">Загрузка платежа...</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="card dark">
            <span className="badge">Payment detail</span>
            <h1 className="title-lg">Платёж #{payment.id}</h1>
            <p className="lead">Статус: {payment.status || '—'} · Провайдер: {payment.provider || '—'} · Сумма: {payment.amount || '—'} {payment.currency || 'RUB'}</p>
          </div>
          {providerRedirect ? (
            <div className="card warning">
              Этот платёж создан через provider-specific checkout contract. Используй ссылки ниже для return/webhook flow или mock action для локального сценария.
            </div>
          ) : null}
          <div className="grid-2">
            <div className="card">
              <h3>Основное</h3>
              <div className="stack" style={{ gap: 8, marginTop: 14 }}>
                <div><strong>Order ID:</strong> {payment.order_id || '—'}</div>
                <div><strong>External payment:</strong> {payment.external_payment_id || '—'}</div>
                <div><strong>Подтверждён:</strong> {formatDate(payment.confirmed_at)}</div>
                <div><strong>Создан:</strong> {formatDate(payment.created_at)}</div>
              </div>
            </div>
            <div className="card">
              <h3>Checkout contract</h3>
              <div className="stack" style={{ gap: 10, marginTop: 14 }}>
                <div className="list-item"><span className="muted">Adapter</span><strong>{contract.adapter || '—'}</strong></div>
                <div className="list-item"><span className="muted">Frontend return</span><strong style={{ wordBreak: 'break-all' }}>{contract.frontend_return_url || '—'}</strong></div>
                <div className="list-item"><span className="muted">Provider success</span><strong style={{ wordBreak: 'break-all' }}>{contract.provider_return_url_success || '—'}</strong></div>
                <div className="list-item"><span className="muted">Provider cancel</span><strong style={{ wordBreak: 'break-all' }}>{contract.provider_return_url_cancel || '—'}</strong></div>
                <div className="list-item"><span className="muted">Webhook</span><strong style={{ wordBreak: 'break-all' }}>{contract.webhook_url || '—'}</strong></div>
              </div>
            </div>
          </div>
          <div className="card">
            <h3>Provider payload</h3>
            <pre className="code-block">{JSON.stringify(payment.provider_payload || {}, null, 2)}</pre>
          </div>
          {payment.status === 'pending' ? (
            <div className="inline">
              <button className="button" disabled={busy} onClick={() => void confirmMock()}>{busy ? 'Обновляем...' : 'Подтвердить mock-платёж'}</button>
              <button className="button secondary" disabled={busy} onClick={() => void cancelMock()}>{busy ? 'Обновляем...' : 'Отменить mock-платёж'}</button>
            </div>
          ) : null}
          <div className="inline">
            <Link href="/payments" className="button secondary">Назад к платежам</Link>
            {payment.order_id ? <button className="button ghost" onClick={() => router.push(`/orders/${payment.order_id}`)}>Открыть заказ</button> : null}
            <Link href="/payouts" className="button ghost">Payouts</Link>
          </div>
        </section>
      )}
    </ProtectedPage>
  );
}

export default function PaymentDetailPage() {
  return (
    <Suspense fallback={<div>Загрузка...</div>}>
      <PaymentDetailPageContent />
    </Suspense>
  );
}

