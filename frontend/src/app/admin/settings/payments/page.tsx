'use client';

import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import type { PaymentProviderSettings } from '@/types/api';

const emptySettings: PaymentProviderSettings = {
  default_provider: 'mock',
  providers: [],
};

export default function AdminPaymentSettingsPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
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
    <ProtectedPage title="Payment provider settings" description="Конфигурация checkout adapters для платформы.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Admin settings</span>
              <h1>Payment provider config</h1>
              <p className="lead">Хранилище provider contract settings в PlatformSettings.homepage_config без отдельной миграции под каждый gateway.</p>
            </div>
            <button className="button" disabled={busy} onClick={() => void save()}>{busy ? 'Сохраняем...' : 'Сохранить'}</button>
          </div>

          {msg ? <div className={`card ${msg === 'Настройки сохранены' ? 'success' : 'error'}`}>{msg}</div> : null}

          <div className="card">
            <div className="form-group">
              <label className="label" htmlFor="default-provider">Default provider</label>
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
                    <label className="label">Display name</label>
                    <input className="input" value={provider.display_name || ''} onChange={(event) => updateProvider(index, { display_name: event.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="label">Environment</label>
                    <select className="select" value={provider.environment || 'test'} onChange={(event) => updateProvider(index, { environment: event.target.value })}>
                      <option value="dev">dev</option>
                      <option value="test">test</option>
                      <option value="prod">prod</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="label">Public key / public id</label>
                    <input className="input" value={provider.public_key || ''} onChange={(event) => updateProvider(index, { public_key: event.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="label">Shop ID</label>
                    <input className="input" value={provider.shop_id || ''} onChange={(event) => updateProvider(index, { shop_id: event.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="label">Webhook secret (masked)</label>
                    <input className="input" value={provider.webhook_secret_masked || ''} onChange={(event) => updateProvider(index, { webhook_secret_masked: event.target.value })} />
                  </div>
                  <div className="form-group">
                    <label className="label">Return URL override</label>
                    <input className="input" value={provider.return_url_override || ''} onChange={(event) => updateProvider(index, { return_url_override: event.target.value })} placeholder="https://app.example.com/checkout/success" />
                  </div>
                  <div className="form-group">
                    <label className="label">Notes</label>
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
