'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { privateApi } from '@/lib/api';
import type { PayoutRequest } from '@/types/api';

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export default function PayoutDetailPage() {
  const params = useParams<{ id: string }>();
  const [payout, setPayout] = useState<PayoutRequest | null>(null);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (!params?.id) return;
    void (async () => {
      try {
        setMsg('');
        const payload = await privateApi.getPayout(params.id);
        setPayout(payload);
      } catch (err) {
        setMsg(err instanceof Error ? err.message : 'Не удалось загрузить payout detail');
      }
    })();
  }, [params?.id]);

  return (
    <ProtectedPage title="Payout detail" description="Страница payout доступна только после входа.">
      {msg ? <div className="card error">{msg}</div> : null}
      {!payout ? (
        <div className="card">Загрузка payout...</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="card dark">
            <span className="badge">Payout detail</span>
            <h1 className="title-lg">Payout #{payout.id}</h1>
            <p className="lead">Статус: {payout.status || '—'} · Сумма: {payout.amount || '—'} {payout.currency || 'RUB'}</p>
          </div>

          <div className="grid-2">
            <div className="card">
              <h3>Основное</h3>
              <div className="stack" style={{ gap: 8, marginTop: 14 }}>
                <div><strong>Requested:</strong> {formatDate(payout.requested_at || payout.created_at)}</div>
                <div><strong>Approved:</strong> {formatDate(payout.approved_at)}</div>
                <div><strong>Processed:</strong> {formatDate(payout.processed_at)}</div>
                <div><strong>Destination:</strong> {payout.destination_masked || '—'}</div>
              </div>
            </div>
            <div className="card">
              <h3>Ledger entries</h3>
              <div className="stack" style={{ gap: 10, marginTop: 14 }}>
                {(payout.ledger_entries || []).length === 0 ? (
                  <p className="muted">Связанных ledger entries пока нет.</p>
                ) : (
                  payout.ledger_entries?.map((entry) => (
                    <div className="card compact" key={entry.id}>
                      <strong>{entry.entry_type || 'entry'}</strong>
                      <p className="muted">{entry.amount || '—'} {entry.currency || 'RUB'} · payment {entry.payment_id || '—'}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="inline">
            <Link href="/payouts" className="button secondary">Назад к payout ledger</Link>
            <Link href="/payments" className="button ghost">Платежи</Link>
          </div>
        </section>
      )}
    </ProtectedPage>
  );
}
