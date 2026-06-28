'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import {
  CustomerCabinetShell,
  CustomerEmptyState,
  CustomerErrorState,
  CustomerLoadingState,
  CustomerMetricCard,
  CustomerStatusBadge,
  type CustomerMetric,
} from '@/modules/customer-cabinet/components';
import {
  entitlementStatus,
  entitlementTitle,
  entitlementType,
  formatCustomerDate,
  shortCustomerNumber,
  statusTone,
  accessStatusLabel,
} from '@/modules/customer-cabinet/components/customer-format';
import type { Entitlement } from '@/types/api';

function isActive(item: Entitlement) {
  const status = entitlementStatus(item).toLowerCase();
  return item.is_active || status === 'active' || status === 'granted';
}

function isExpiring(item: Entitlement) {
  const expiresAt = item.ends_at || item.expires_at;
  if (!expiresAt) return false;
  const expires = new Date(expiresAt).getTime();
  if (Number.isNaN(expires)) return false;
  const diff = expires - Date.now();
  return diff > 0 && diff <= 1000 * 60 * 60 * 24 * 14;
}

export default function EntitlementsPage() {
  const [items, setItems] = useState<Entitlement[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const { isAuthenticated, isLoading: sessionLoading } = useAuthSession();

  async function load() {
    try {
      setLoading(true);
      setMessage('');
      setItems(await privateApi.listEntitlements());
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (sessionLoading) return;
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    void load();
  }, [isAuthenticated, sessionLoading]);

  const active = useMemo(() => items.filter(isActive), [items]);
  const expiring = useMemo(() => items.filter(isExpiring), [items]);
  const inactive = useMemo(() => items.filter((item) => !isActive(item)), [items]);
  const metrics: CustomerMetric[] = [
    { label: 'Всего', value: items.length, hint: 'Все доступы', tone: 'neutral' },
    { label: 'Активные', value: active.length, hint: 'Можно учиться', tone: 'success' },
    { label: 'Скоро истекают', value: expiring.length, hint: 'До 14 дней', tone: expiring.length ? 'warning' : 'neutral' },
    { label: 'Неактивные', value: inactive.length, hint: 'Истекли или отозваны', tone: inactive.length ? 'danger' : 'neutral' },
  ];

  return (
    <ProtectedPage title="Мои доступы" description="Доступы к материалам доступны только после входа.">
      <CustomerCabinetShell
        title="Мои доступы"
        description="Все активные и завершённые доступы к программам, видео, наборам и подпискам."
        actions={<button className="premium-secondary-button" type="button" onClick={() => void load()} disabled={loading}>Обновить</button>}
      >
        <div className="customer-metric-grid">
          {metrics.map((metric) => <CustomerMetricCard key={metric.label} metric={metric} />)}
        </div>

        {message ? <CustomerErrorState message={message} onRetry={() => void load()} /> : null}
        {loading ? <CustomerLoadingState /> : null}

        {!loading && !items.length ? (
          <CustomerEmptyState title="Доступов пока нет" description="После успешной покупки доступ появится здесь." />
        ) : null}

        <div className="customer-access-grid">
          {active.map((item) => (
            <article className="customer-access-card" key={item.id}>
              <CustomerStatusBadge tone={statusTone(entitlementStatus(item), item.is_active)}>
                {accessStatusLabel(entitlementStatus(item), item.is_active)}
              </CustomerStatusBadge>
              <h3>{entitlementTitle(item)}</h3>
              <p>{entitlementType(item)} · {item.trainer_name || 'TrainerHub'}</p>
              <div className="customer-commerce-list">
                <div><span>Активирован</span><strong>{formatCustomerDate(item.starts_at || item.granted_at || item.created_at)}</strong></div>
                <div><span>Срок действия</span><strong>{formatCustomerDate(item.ends_at || item.expires_at)}</strong></div>
                <div><span>Номер доступа</span><strong>{shortCustomerNumber(item.id, 'ACC')}</strong></div>
              </div>
              <Link href="/learning" className="premium-primary-button">Перейти к обучению</Link>
            </article>
          ))}
        </div>

        {inactive.length ? (
          <section className="customer-section-card">
            <div className="customer-section-header">
              <h2>Истекшие и неактивные</h2>
            </div>
            <div className="customer-commerce-list">
              {inactive.map((item) => (
                <article className="customer-commerce-card" key={item.id}>
                  <CustomerStatusBadge tone={statusTone(entitlementStatus(item), item.is_active)}>
                    {accessStatusLabel(entitlementStatus(item), item.is_active)}
                  </CustomerStatusBadge>
                  <strong>{entitlementTitle(item)}</strong>
                  <span>{entitlementType(item)} · {formatCustomerDate(item.ends_at || item.expires_at || item.revoked_at)}</span>
                </article>
              ))}
            </div>
          </section>
        ) : null}
      </CustomerCabinetShell>
    </ProtectedPage>
  );
}
