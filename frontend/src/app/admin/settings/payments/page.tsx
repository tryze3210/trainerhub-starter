'use client';

import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { isAdminUser } from '@/lib/authz';
import { privateApi } from '@/lib/api';
import type { PaymentProviderSettings } from '@/types/api';

const emptySettings: PaymentProviderSettings = {
  default_provider: 'mock',
  providers: [],
};

export default function AdminPaymentSettingsPage() {
  const { user } = useAuthSession();
  const isAdmin = isAdminUser(user);
  const [settings, setSettings] = useState<PaymentProviderSettings>(emptySettings);
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setMsg('');
      const payload = await privateApi.getPaymentProviderSettings();
      setSettings(payload);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить payment provider settings');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void load();
  }, [isAdmin]);

  function updateProvider(index: number, patch: Record<string, unknown>) {
    setSettings((current) => ({
      ...current,
      providers: current.providers.map((item, idx) => (idx === index ? { ...item, ...patch } : item)),
    }));
  }

  async function save() {
    try {
      setBusy(true);
      setMsg('');
      const payload = await privateApi.updatePaymentProviderSettings(settings);
      setSettings(payload);
      setMsg('Настройки сохранены');
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось сохранить payment provider settings');
    } finally {
      setBusy(false);
    }
  }

  return (
    <ProtectedPage title="Настройки платежных провайдеров" description="Конфигурация платежных адаптеров для платформы.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет роли администратора.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Настройки администратора</span>
              <h1>Конфигурация платежных провайдеров</h1>
              <p className="lead">Хранилище настроек платежных договоров в PlatformSettings.homepage_config без отдельной миграции под каждый шлюз.</p>
            </div>
            <button className="button" disabled={busy} onClick={() => void save()}>{busy ? 'Сохраняем...' : 'Сохранить'}</button>
          </div>

          {msg ? <div className={`card ${msg === 'Настройки сохранены' ? 'success' : 'error'}`}>{msg}</div> : null}

          <div className="card">
            <div className="form-group">
              <label className="label" htmlFor="default-provider">Провайдер по умолчанию</label>
              <select id="default-provider" className="select" value={settings.default_provider} onChange={(event) => setSettings((current) => ({ ...current, default_provider: event.target.value }))}>
                {settings.providers.map((provider) => (
                  <option key={provider.provider} value={provider.provider}>{provider.display_name || provider.provider}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid-2">
            {settings.providers.map((provider, index) => (
              <article className="card" key={provider.provider}>
                <div className="stack" style={{ gap: 14 }}>
                  <div className="row">
                    <strong>{provider.display_name || provider.provider}</strong>
                    <span className={`badge ${provider.is_enabled ? 'success' : 'warning'}`}>{provider.is_enabled ? 'enabled' : 'disabled'}</span>
                  </div>
                  <div className="form-group">
                    <label className="label">Название на экране</label>
                    <input className="input" value={provider.display_name || ''} onChange={(event) => updateProvider(index, { display_name: event.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="label">Среда</label>
                    <select className="select" value={provider.environment || 'test'} onChange={(event) => updateProvider(index, { environment: event.target.value })}>
                      <option value="dev">Разработка</option>
                      <option value="test">Тест</option>
                      <option value="prod">Продакшен</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="label">Публичный ключ / публичный ID</label>
                    <input className="input" value={provider.public_key || ''} onChange={(event) => updateProvider(index, { public_key: event.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="label">ID магазина</label>
                    <input className="input" value={provider.shop_id || ''} onChange={(event) => updateProvider(index, { shop_id: event.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="label">Секрет вебхука (скрыт)</label>
                    <input className="input" value={provider.webhook_secret_masked || ''} onChange={(event) => updateProvider(index, { webhook_secret_masked: event.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="label">Переопределение return URL</label>
                    <input className="input" value={provider.return_url_override || ''} onChange={(event) => updateProvider(index, { return_url_override: event.target.value })} placeholder="https://app.example.com/checkout/success" />
                  </div>
                  <div className="form-group">
                    <label className="label">Заметки</label>
                    <textarea className="textarea" value={provider.notes || ''} onChange={(event) => updateProvider(index, { notes: event.target.value })} />
                  </div>
                  <label className="checkbox-inline">
                    <input type="checkbox" checked={provider.is_enabled} onChange={(event) => updateProvider(index, { is_enabled: event.target.checked })} />
                    Enabled for checkout creation
                  </label>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
    </ProtectedPage>
  );
}
