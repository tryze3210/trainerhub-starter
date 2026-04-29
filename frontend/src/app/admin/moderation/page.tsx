'use client';

import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { useAuthSession } from '@/components/auth-provider';
import { privateApi } from '@/lib/api';
import type { ModerationCase, ModerationOverview, TrainerRiskFlag } from '@/types/api';

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}

export default function AdminModerationPage() {
  const { user } = useAuthSession();
  const isAdmin = user?.active_role === 'admin';
  const [overview, setOverview] = useState<ModerationOverview | null>(null);
  const [cases, setCases] = useState<ModerationCase[]>([]);
  const [flags, setFlags] = useState<TrainerRiskFlag[]>([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [queueFilter, setQueueFilter] = useState('');
  const [reason, setReason] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);
  const [msg, setMsg] = useState('');

  async function load() {
    try {
      setMsg('');
      const [overviewPayload, casesPayload, flagsPayload] = await Promise.all([
        privateApi.getAdminModerationOverview(),
        privateApi.listAdminModerationCases({ status: statusFilter || undefined, queue: queueFilter || undefined }),
        privateApi.listAdminRiskFlags(true),
      ]);
      setOverview(overviewPayload);
      setCases(casesPayload);
      setFlags(flagsPayload);
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось загрузить moderation queue');
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    void load();
  }, [isAdmin, statusFilter, queueFilter]);

  const queues = useMemo(() => overview?.queues || [], [overview]);

  async function assign(caseId: string) {
    try {
      setBusyId(caseId);
      await privateApi.assignAdminModerationCase(caseId);
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось назначить case');
    } finally {
      setBusyId(null);
    }
  }

  async function decide(caseId: string, decision: 'approved' | 'rejected' | 'needs_changes' | 'escalated') {
    try {
      setBusyId(caseId);
      await privateApi.decideAdminModerationCase(caseId, { decision, reason });
      if (decision !== 'escalated') setReason('');
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось применить moderation decision');
    } finally {
      setBusyId(null);
    }
  }

  async function resolveFlag(flagId: string) {
    try {
      setBusyId(flagId);
      await privateApi.resolveAdminRiskFlag(flagId);
      await load();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось закрыть risk flag');
    } finally {
      setBusyId(null);
    }
  }

  return (
    <ProtectedPage title="Admin moderation" description="Очередь модерации тренеров, контента и risk flags.">
      {!isAdmin ? (
        <div className="card error">У текущей сессии нет admin-role.</div>
      ) : (
        <section className="stack" style={{ gap: 24 }}>
          <div className="row" style={{ alignItems: 'flex-start' }}>
            <div className="stack" style={{ gap: 10 }}>
              <span className="badge secondary">Trust & Safety</span>
              <h1>Moderation control room</h1>
              <p className="lead">Единая очередь для trainer onboarding, контента, escalations и risk flags.</p>
            </div>
            <button className="button secondary" onClick={() => void load()}>Обновить</button>
          </div>

          {msg ? <div className="card error">{msg}</div> : null}

          <div className="grid-4">
            <div className="card"><div className="kpi"><span className="muted">Open</span><strong>{overview?.totals.open || 0}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">In review</span><strong>{overview?.totals.in_review || 0}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Escalated</span><strong>{overview?.totals.escalated || 0}</strong></div></div>
            <div className="card"><div className="kpi"><span className="muted">Risk flags</span><strong>{overview?.active_risk_flags || 0}</strong></div></div>
          </div>

          <div className="grid-2">
            <div className="card">
              <h2 className="title-md">Queue filters</h2>
              <div className="form" style={{ marginTop: 16 }}>
                <div className="form-row">
                  <div className="form-group">
                    <label className="label" htmlFor="mod-status">Status</label>
                    <select id="mod-status" className="select" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                      <option value="">Все</option>
                      <option value="open">open</option>
                      <option value="in_review">in_review</option>
                      <option value="escalated">escalated</option>
                      <option value="resolved">resolved</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="label" htmlFor="mod-queue">Queue</label>
                    <select id="mod-queue" className="select" value={queueFilter} onChange={(event) => setQueueFilter(event.target.value)}>
                      <option value="">Все</option>
                      {queues.map((queue) => <option key={queue.queue} value={queue.queue}>{queue.queue}</option>)}
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="mod-reason">Decision reason</label>
                  <textarea id="mod-reason" className="textarea" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Коротко: что проверили и почему принято решение" />
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="title-md">Active risk flags</h2>
              <div className="stack" style={{ gap: 10, marginTop: 16 }}>
                {flags.length === 0 ? <p className="muted">Активных risk flags нет.</p> : null}
                {flags.slice(0, 5).map((flag) => (
                  <div className="list-item" key={flag.id}>
                    <span className={`badge ${flag.risk_level === 'critical' || flag.risk_level === 'high' ? 'danger' : 'warning'}`}>{flag.risk_level}</span>
                    <strong>{flag.label}</strong>
                    <small>{flag.code} · trainer {flag.trainer}</small>
                    <button className="button ghost sm" disabled={busyId === flag.id} onClick={() => void resolveFlag(flag.id)}>Resolve</button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {cases.length === 0 ? (
            <div className="empty-state"><h3>Очередь пуста</h3><p>Нет moderation cases под текущие фильтры.</p></div>
          ) : (
            <div className="grid-2">
              {cases.map((item) => (
                <article className="card" key={item.id}>
                  <div className="stack" style={{ gap: 12 }}>
                    <div className="row">
                      <div>
                        <strong>{item.title}</strong>
                        <p className="muted">{item.queue} · {item.target_type} · {item.target_id}</p>
                      </div>
                      <span className={`badge ${item.status === 'escalated' ? 'danger' : item.status === 'resolved' ? 'success' : 'warning'}`}>{item.status}</span>
                    </div>

                    <p>{item.summary || 'Без описания.'}</p>

                    <div className="grid-2">
                      <div className="list-item"><span className="muted">Priority</span><strong>{item.priority}</strong></div>
                      <div className="list-item"><span className="muted">Opened</span><strong>{formatDate(item.opened_at)}</strong></div>
                      <div className="list-item"><span className="muted">Assigned</span><strong>{item.assigned_to || '—'}</strong></div>
                      <div className="list-item"><span className="muted">Decision</span><strong>{item.latest_decision || '—'}</strong></div>
                    </div>

                    <div className="inline" style={{ flexWrap: 'wrap' }}>
                      <button className="button secondary" disabled={busyId === item.id} onClick={() => void assign(item.id)}>Assign to me</button>
                      <button className="button" disabled={busyId === item.id} onClick={() => void decide(item.id, 'approved')}>Approve</button>
                      <button className="button secondary" disabled={busyId === item.id} onClick={() => void decide(item.id, 'needs_changes')}>Needs changes</button>
                      <button className="button ghost" disabled={busyId === item.id} onClick={() => void decide(item.id, 'rejected')}>Reject</button>
                      <button className="button danger" disabled={busyId === item.id} onClick={() => void decide(item.id, 'escalated')}>Escalate</button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      )}
    </ProtectedPage>
  );
}
