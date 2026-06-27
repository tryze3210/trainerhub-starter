'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import {
  DSBarChart,
  DSEmptyState,
  DSPageHeader,
  DSSection,
  DSSkeleton,
  DSStatsGrid,
  DSStatusDot,
  DSTransitionPanel,
} from '@/design-system';
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

function moderationOpenTotal(moderation?: ModerationOverview | null) {
  return (moderation?.totals.open || 0) + (moderation?.totals.in_review || 0) + (moderation?.totals.escalated || 0);
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
          <DSPageHeader
            eyebrow="Marketplace ops"
            title="Admin cockpit"
            description="Модерация, выплаты и аналитика собраны в один операционный слой."
            actions={
              <>
                <Link href="/admin/marketplace" className="button">Marketplace</Link>
                <Link href="/admin/operations" className="button secondary">Operations</Link>
                <Link href="/admin/audit" className="button ghost">Audit</Link>
              </>
            }
          />

          {msg ? <div className="card error">{msg}</div> : null}
          {!state ? (
            <div className="card">
              <DSSkeleton lines={4} />
            </div>
          ) : null}

          {state ? (
            <DSTransitionPanel active className="stack" style={{ gap: 24 }}>
              <DSStatsGrid
                stats={[
                  {
                    label: 'Revenue 30d',
                    value: money(state.analytics?.revenue),
                    hint: 'Paid marketplace revenue',
                    tone: 'success',
                  },
                  {
                    label: 'Paid orders',
                    value: state.analytics?.paid_orders || 0,
                    hint: 'Last 30 days',
                    tone: 'primary',
                  },
                  {
                    label: 'Payout exposure',
                    value: money(state.payouts?.ops.pending_exposure_amount),
                    hint: 'Pending operator exposure',
                    tone: 'warning',
                  },
                  {
                    label: 'Open moderation',
                    value: moderationOpenTotal(state.moderation),
                    hint: 'Open, review and escalated',
                    tone: moderationOpenTotal(state.moderation) > 0 ? 'danger' : 'success',
                  },
                ]}
              />

              <div className="grid-3">
                <DSSection title="Moderation queues" description="Open work by queue and total risk load.">
                  <div className="card compact stack" style={{ gap: 14 }}>
                    {(state.moderation?.queues || []).length === 0 ? (
                      <DSEmptyState title="Очередей пока нет" description="Новых moderation задач нет." />
                    ) : null}
                    {(state.moderation?.queues || []).map((queue) => (
                      <div className="list-item" key={queue.queue}>
                        <div className="row">
                          <span className="muted">{queue.queue}</span>
                          <DSStatusDot tone={queue.open > 0 ? 'warning' : 'success'} label={queue.open > 0 ? 'Open' : 'Clear'} />
                        </div>
                        <strong>{queue.open} open / {queue.total} total</strong>
                      </div>
                    ))}
                  </div>
                </DSSection>

                <DSSection title="Payout statuses" description="Operational payout volume by status.">
                  <div className="card compact stack" style={{ gap: 16 }}>
                    {(state.payouts?.statuses || []).map((bucket) => (
                      <div className="list-item" key={bucket.status}>
                        <div className="row">
                          <span className="muted">{bucket.status}</span>
                          <DSStatusDot tone={bucket.count > 0 ? 'primary' : 'neutral'} />
                        </div>
                        <strong>{bucket.count} · {money(bucket.amount)}</strong>
                      </div>
                    ))}
                    {(state.payouts?.statuses || []).length > 0 ? (
                      <DSBarChart
                        label="Payout status chart"
                        data={(state.payouts?.statuses || []).map((bucket) => ({
                          label: bucket.status,
                          value: bucket.count,
                          tone: bucket.count > 0 ? 'primary' : 'neutral',
                        }))}
                      />
                    ) : (
                      <DSEmptyState title="Нет payout статусов" description="Операционная сводка пока пустая." />
                    )}
                  </div>
                </DSSection>

                <DSSection title="Review moderation" description="Отзывы, ожидающие решения оператора.">
                  <div className="card compact stack" style={{ gap: 16 }}>
                    <div className="kpi">
                      <span className="muted">Pending reviews</span>
                      <strong>{state.reviews.length}</strong>
                      <DSStatusDot tone={state.reviews.length > 0 ? 'warning' : 'success'} label={state.reviews.length > 0 ? 'Needs review' : 'Clear'} />
                    </div>
                    <Link href="/admin/reviews" className="button secondary">Open review queue</Link>
                  </div>
                </DSSection>
              </div>
            </DSTransitionPanel>
          ) : null}
        </section>
      )}
    </ProtectedPage>
  );
}
