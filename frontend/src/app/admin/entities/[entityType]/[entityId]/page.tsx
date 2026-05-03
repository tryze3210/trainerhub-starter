'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { adminEntityDetailsApi, adminEntityHref } from '@/modules/admin-entity-details/api';
import type { AdminEntityActionResult, AdminEntityDetail } from '@/modules/admin-entity-details/api';

function scalar(value: unknown, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback;
  if (typeof value === 'number') return value.toLocaleString('ru-RU');
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function label(value: string) {
  return value.replaceAll('_', ' ');
}

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('ru-RU');
}

function prettyJson(value: unknown) {
  if (!value || typeof value !== 'object') return '';
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function likelyDateKey(key: string) {
  return key.endsWith('_at') || key === 'created_at' || key === 'updated_at' || key === 'received_at' || key === 'processed_at';
}

function stringValue(value: unknown) {
  if (value === null || value === undefined || value === '') return '';
  return String(value);
}

function isRiskHoldLedger(detail: AdminEntityDetail) {
  const raw = detail.raw || {};
  return (
    detail.entity_type === 'payout_ledger' &&
    String(raw.entry_type || '') === 'risk_hold' &&
    String(raw.source_type || '') === 'payment_dispute_hold'
  );
}

function paymentIdForRiskHold(detail: AdminEntityDetail) {
  const raw = detail.raw || {};
  return stringValue(raw.payment_id || raw.source_id || detail.primary?.payment_id || detail.primary?.source_id);
}

function KeyValueRows({ data }: { data?: Record<string, unknown> }) {
  const entries = Object.entries(data || {}).filter(([, value]) => value !== undefined && value !== null && value !== '');
  if (!entries.length) return <p className="muted">Нет данных.</p>;

  return (
    <div className="stack" style={{ gap: 10 }}>
      {entries.map(([key, value]) => (
        <div className="list-item" key={key}>
          <span className="muted">{label(key)}</span>
          <strong>{likelyDateKey(key) ? formatDate(String(value)) : scalar(value)}</strong>
        </div>
      ))}
    </div>
  );
}

function JsonBlock({ title, value }: { title: string; value: unknown }) {
  const json = prettyJson(value);
  return (
    <div className="card">
      <h2 className="title-md">{title}</h2>
      {json ? (
        <pre style={{ overflowX: 'auto', whiteSpace: 'pre-wrap', marginTop: 16 }}>{json}</pre>
      ) : (
        <p className="muted" style={{ marginTop: 16 }}>Нет JSON payload.</p>
      )}
    </div>
  );
}

function entityBackLink(entityType: string) {
  if (entityType === 'audit_event') return '/admin/audit';
  if (entityType === 'payout_ledger' || entityType === 'payout_request') return '/admin/payouts';
  if (entityType === 'moderation_case') return '/admin/moderation';
  return '/admin/operations';
}

function EntityActions({
  detail,
  disabled,
  onAction,
}: {
  detail: AdminEntityDetail;
  disabled: boolean;
  onAction: (label: string, action: () => Promise<AdminEntityActionResult>) => Promise<void>;
}) {
  const isOutbox = detail.entity_type === 'outbox_message';
  const isWebhook = detail.entity_type === 'payment_webhook';
  const isRiskHold = isRiskHoldLedger(detail);
  const paymentId = paymentIdForRiskHold(detail);

  if (!isOutbox && !isWebhook && !isRiskHold) {
    return (
      <div className="card">
        <h2 className="title-md">Actions</h2>
        <p className="muted" style={{ marginTop: 12 }}>
          Для этого типа сущности операторские действия не предусмотрены. Используй связанные сущности или audit feed.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="title-md">Actions</h2>
      <div className="stack" style={{ gap: 12, marginTop: 16 }}>
        {isOutbox ? (
          <>
            <div className="list-item">
              <span>
                <strong>Retry outbox message</strong>
                <br />
                <span className="muted">Вернуть сообщение в pending и сбросить attempts.</span>
              </span>
              <button
                className="button"
                type="button"
                disabled={disabled}
                onClick={() => onAction('Outbox retry completed', () => adminEntityDetailsApi.retryOutboxMessage(detail.entity_id))}
              >
                Retry
              </button>
            </div>
            <div className="list-item">
              <span>
                <strong>Mark outbox dead</strong>
                <br />
                <span className="muted">Пометить сообщение как dead с причиной оператора.</span>
              </span>
              <button
                className="button secondary"
                type="button"
                disabled={disabled}
                onClick={() => {
                  const reason = window.prompt('Причина перевода outbox message в dead:', 'manual_dead_from_entity_detail');
                  if (!reason) return;
                  void onAction('Outbox marked dead', () => adminEntityDetailsApi.markOutboxDead(detail.entity_id, reason));
                }}
              >
                Dead
              </button>
            </div>
          </>
        ) : null}

        {isWebhook ? (
          <div className="list-item">
            <span>
              <strong>Reprocess payment webhook</strong>
              <br />
              <span className="muted">Повторно прогнать сохраненный webhook через payment lifecycle без проверки подписи.</span>
            </span>
            <button
              className="button"
              type="button"
              disabled={disabled}
              onClick={() => {
                const force = String(detail.status || detail.raw?.status || '') === 'processed'
                  ? window.confirm('Webhook уже processed. Форсировать повторную обработку?')
                  : false;
                void onAction('Payment webhook reprocessed', () => adminEntityDetailsApi.reprocessPaymentWebhook(detail.entity_id, force));
              }}
            >
              Reprocess
            </button>
          </div>
        ) : null}

        {isRiskHold ? (
          <div className="list-item">
            <span>
              <strong>Release risk hold</strong>
              <br />
              <span className="muted">Вернуть заблокированную сумму тренеру по payment_id: {paymentId || '—'}.</span>
            </span>
            <button
              className="button"
              type="button"
              disabled={disabled || !paymentId}
              onClick={() => {
                const reason = window.prompt('Причина ручного release risk hold:', 'manual_release_from_entity_detail');
                if (!reason || !paymentId) return;
                void onAction('Risk hold released', () => adminEntityDetailsApi.releaseRiskHold(paymentId, reason));
              }}
            >
              Release hold
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function AdminEntityDetailPage() {
  const params = useParams<{ entityType?: string; entityId?: string }>();
  const entityType = String(params?.entityType || '');
  const entityId = String(params?.entityId || '');
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [detail, setDetail] = useState<AdminEntityDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [actionMsg, setActionMsg] = useState('');

  const load = useCallback(async () => {
    if (!isAdmin || !entityType || !entityId) return;
    try {
      setLoading(true);
      setMsg('');
      setDetail(await adminEntityDetailsApi.getDetail(entityType, entityId));
    } catch (error) {
      setMsg(error instanceof Error ? error.message : 'Не удалось загрузить entity detail');
    } finally {
      setLoading(false);
    }
  }, [entityId, entityType, isAdmin]);

  const runAction = useCallback(async (successLabel: string, action: () => Promise<AdminEntityActionResult>) => {
    try {
      setActionLoading(true);
      setActionMsg('');
      const result = await action();
      setActionMsg(`${successLabel}: ${scalar(result.status || result.detail || result.id || 'ok')}`);
      await load();
    } catch (error) {
      setActionMsg(error instanceof Error ? error.message : 'Операторское действие не выполнено');
    } finally {
      setActionLoading(false);
    }
  }, [load]);

  useEffect(() => {
    void load();
  }, [load]);

  const rawSummary = useMemo(() => {
    const raw = detail?.raw || {};
    return {
      id: raw.id || detail?.entity_id,
      created_at: raw.created_at,
      updated_at: raw.updated_at,
      status: raw.status || detail?.status,
    };
  }, [detail]);

  return (
    <ProtectedPage title="Admin entity detail" description="Детальная карточка операционной сущности: payment, webhook, outbox, audit, payout ledger или moderation case.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="card dark">
            <div className="row" style={{ alignItems: 'flex-start', gap: 18 }}>
              <div className="stack" style={{ gap: 10 }}>
                <span className="badge secondary">Entity detail</span>
                <h1 className="title-lg">{detail?.title || `${entityType}:${entityId}`}</h1>
                <p className="lead">
                  {detail ? `${detail.entity_type}:${detail.entity_id}` : `${entityType}:${entityId}`}
                </p>
                <div className="inline" style={{ flexWrap: 'wrap' }}>
                  <Link href={entityBackLink(detail?.entity_type || entityType)} className="button secondary">Back</Link>
                  <Link href="/admin/operations" className="button ghost">Operations</Link>
                  <Link href="/admin/audit" className="button ghost">Audit</Link>
                  <button className="button" type="button" disabled={loading || actionLoading} onClick={() => void load()}>
                    {loading ? 'Refreshing...' : 'Refresh'}
                  </button>
                </div>
              </div>
              <div className="card" style={{ minWidth: 220 }}>
                <div className="kpi">
                  <span className="muted">Status</span>
                  <strong>{detail?.status || '—'}</strong>
                  <small className="muted">{detail?.entity_type || entityType}</small>
                </div>
              </div>
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}
          {actionMsg ? <div className="card">{actionMsg}</div> : null}
          {!detail && !msg ? <div className="card">Загрузка entity detail...</div> : null}

          {detail ? (
            <>
              <EntityActions detail={detail} disabled={loading || actionLoading} onAction={runAction} />

              <div className="grid-2">
                <div className="card">
                  <h2 className="title-md">Primary fields</h2>
                  <div style={{ marginTop: 16 }}>
                    <KeyValueRows data={detail.primary} />
                  </div>
                </div>

                <div className="card">
                  <h2 className="title-md">System fields</h2>
                  <div style={{ marginTop: 16 }}>
                    <KeyValueRows data={rawSummary} />
                  </div>
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">Relationships</h2>
                <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                  {detail.relationships.length === 0 ? <p className="muted">Связанных сущностей нет.</p> : null}
                  {detail.relationships.map((relationship) => {
                    const href = relationship.href || adminEntityHref(relationship.entity_type, relationship.entity_id);
                    return (
                      <div className="list-item" key={`${relationship.entity_type}-${relationship.entity_id}-${relationship.label}`}>
                        <span>
                          <strong>{relationship.label}</strong>
                          <br />
                          <span className="muted">{relationship.entity_type}:{relationship.entity_id}</span>
                        </span>
                        <Link href={href} className="button secondary">Open</Link>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="grid-2">
                <JsonBlock title="Payload / context" value={detail.payload} />
                <JsonBlock title="Raw object" value={detail.raw} />
              </div>
            </>
          ) : null}
        </section>
      )}
    </ProtectedPage>
  );
}
