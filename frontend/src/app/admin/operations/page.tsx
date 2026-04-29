'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';

type JsonMap = Record<string, unknown>;

function asRecord(value: unknown): JsonMap {
  return value && typeof value === 'object' && !Array.isArray(value) ? (value as JsonMap) : {};
}

function scalar(value: unknown): string {
  if (value === null || value === undefined || value === '') return '0';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

function CounterGrid({ title, data }: { title: string; data: unknown }) {
  const record = asRecord(data);
  const rows = Object.entries(record);
  return (
    <div className="card">
      <h2 className="title-md">{title}</h2>
      <div className="stack" style={{ gap: 10, marginTop: 16 }}>
        {rows.length === 0 ? <p className="muted">Нет данных.</p> : null}
        {rows.map(([key, value]) => (
          <div className="list-item" key={key}>
            <span className="muted">{key}</span>
            <strong>{scalar(value)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AdminOperationsPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [inspection, setInspection] = useState<JsonMap | null>(null);
  const [report, setReport] = useState<JsonMap | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const trainerApplications = useMemo(() => asRecord(inspection?.trainer_applications), [inspection]);
  const moderation = useMemo(() => asRecord(inspection?.moderation), [inspection]);

  async function load() {
    if (!isAdmin) return;
    try {
      setMsg('');
      setInspection(await privateApi.getAdminMarketplaceMaintenance());
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить maintenance status');
    }
  }

  async function runRepair(dryRun: boolean) {
    if (!isAdmin) return;
    try {
      setLoading(true);
      setMsg('');
      const result = await privateApi.runAdminMarketplaceMaintenance(dryRun);
      setReport(result);
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Maintenance operation failed');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [isAdmin]);

  return (
    <ProtectedPage title="Admin operations" description="Repair/backfill для onboarding, moderation и trainer access.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="card dark">
            <div className="stack" style={{ gap: 12 }}>
              <span className="badge secondary">Marketplace maintenance</span>
              <h1 className="title-lg">Admin operations</h1>
              <p className="lead">
                Контроль целостности цепочки: trainer application → moderation case → approved trainer role → public profile → CMS access.
              </p>
              <div className="inline" style={{ flexWrap: 'wrap' }}>
                <button className="button secondary" type="button" onClick={() => void load()} disabled={loading}>Refresh</button>
                <button className="button ghost" type="button" onClick={() => void runRepair(true)} disabled={loading}>Dry-run repair</button>
                <button className="button" type="button" onClick={() => void runRepair(false)} disabled={loading}>Apply repair</button>
                <Link href="/admin" className="button ghost">Back to cockpit</Link>
              </div>
            </div>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}
          {!inspection ? <div className="card">Загрузка operations status...</div> : null}

          {inspection ? (
            <div className="grid-2">
              <CounterGrid title="Trainer applications" data={trainerApplications} />
              <CounterGrid title="Moderation" data={moderation} />
            </div>
          ) : null}

          {report ? (
            <div className="card">
              <h2 className="title-md">Last repair report</h2>
              <pre style={{ overflowX: 'auto', whiteSpace: 'pre-wrap', marginTop: 16 }}>{JSON.stringify(report, null, 2)}</pre>
            </div>
          ) : null}
        </section>
      )}
    </ProtectedPage>
  );
}
