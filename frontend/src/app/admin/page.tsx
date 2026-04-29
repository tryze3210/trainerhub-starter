'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import type { AdminPayoutOverview, AnalyticsKpiOverview, ModerationOverview, Review } from '@/types/api';

type AdminCockpitState = {
  analytics: AnalyticsKpiOverview | null;
  payouts: AdminPayoutOverview | null;
  moderation: ModerationOverview | null;
  reviews: Review[];
};

function money(value?: string | number, currency = 'RUB') {
  if (value === undefined || value === null || value === '') return `0 ${currency}`;
  return `${value} ${currency}`;
}

export default function AdminCockpitPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [state, setState] = useState<AdminCockpitState | null>(null);
  const [msg, setMsg] = useState('');

  async function load() {
    try {
      setMsg('');
      const [analytics, payouts, moderation, reviewsPayload] = await Promise.all([
        privateApi.getAdminAnalyticsOverview(30).catch(() => null),
        privateApi.getAdminPayoutOverview().catch(() => null),
        privateApi.getAdminModerationOverview().catch(() => null),
        privateApi.listPendingReviews().catch(() => ({ results: [] })),
      ]);

      setState({
        analytics,
        payouts,
        moderation,
        reviews: reviewsPayload.results || [],
      });
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить admin cockpit');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void load();
  }, [isAdmin]);

  return (
    <ProtectedPage title="Admin cockpit" description="Единая операционная панель marketplace core.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="card dark">
            <div className="stack" style={{ gap: 12 }}>
              <span className="badge secondary">Marketplace ops</span>
              <h1 className="title-lg">Admin cockpit</h1>
              <p className="lead">Модерация, выплаты и аналитика собраны в один операционный слой.</p>
              <div className="inline" style={{ flexWrap: 'wrap' }}>
                <Link href="/admin/marketplace" className="button">Marketplace command</Link>
                <Link href="/admin/moderation" className="button secondary">Moderation</Link>
                <Link href="/admin/payouts" className="button secondary">Payout ops</Link>
                <Link href="/admin/analytics" className="button secondary">Analytics</Link>
                <Link href="/admin/operations" className="button secondary">Operations</Link>
                <Link href="/admin/reviews" className="button ghost">Reviews</Link>
              </div>
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}
          {!state ? <div className="card">Загрузка admin cockpit...</div> : null}

          {state ? (
            <>
              <div className="grid-4">
                <div className="card"><div className="kpi"><span className="muted">Revenue 30d</span><strong>{money(state.analytics?.revenue)}</strong></div></div>
                <div className="card"><div className="kpi"><span className="muted">Paid orders</span><strong>{state.analytics?.paid_orders || 0}</strong></div></div>
                <div className="card"><div className="kpi"><span className="muted">Payout exposure</span><strong>{money(state.payouts?.ops.pending_exposure_amount)}</strong></div></div>
                <div className="card"><div className="kpi"><span className="muted">Open moderation</span><strong>{(state.moderation?.totals.open || 0) + (state.moderation?.totals.in_review || 0) + (state.moderation?.totals.escalated || 0)}</strong></div></div>
              </div>

              <div className="grid-3">
                <div className="card">
                  <h2 className="title-md">Moderation queues</h2>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    {(state.moderation?.queues || []).length === 0 ? <p className="muted">Очередей пока нет.</p> : null}
                    {(state.moderation?.queues || []).map((queue) => (
                      <div className="list-item" key={queue.queue}>
                        <span className="muted">{queue.queue}</span>
                        <strong>{queue.open} open / {queue.total} total</strong>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card">
                  <h2 className="title-md">Payout statuses</h2>
                  <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                    {(state.payouts?.statuses || []).map((bucket) => (
                      <div className="list-item" key={bucket.status}>
                        <span className="muted">{bucket.status}</span>
                        <strong>{bucket.count} · {money(bucket.amount)}</strong>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="card">
                  <h2 className="title-md">Review moderation</h2>
                  <div className="kpi" style={{ marginTop: 16 }}>
                    <span className="muted">Pending reviews</span>
                    <strong>{state.reviews.length}</strong>
                  </div>
                  <Link href="/admin/reviews" className="button secondary" style={{ marginTop: 16 }}>Open review queue</Link>
                </div>
              </div>
            </>
          ) : null}
        </section>
      )}
    </ProtectedPage>
  );
}
