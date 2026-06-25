'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { ProtectedPage } from '@/components/protected-page';
import { assignmentsApi } from '@/modules/assignments/api';
import type { Assignment, AssignmentsPayload } from '@/types/api';

function statusLabel(status?: string) {
  if (status === 'approved') return 'Принято';
  if (status === 'needs_revision') return 'Нужна доработка';
  if (status === 'reviewed') return 'Проверено';
  if (status === 'submitted') return 'Отправлено';
  return 'Ожидает ответа';
}

function contentLabel(type: string) {
  return type === 'course' ? 'Курс' : 'Программа';
}

export default function StudentAssignmentsPage() {
  const [payload, setPayload] = useState<AssignmentsPayload | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [answerText, setAnswerText] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  async function load() {
    setLoading(true);
    setMessage('');
    try {
      const next = await assignmentsApi.getStudentAssignments();
      setPayload(next);
      setSelectedId((current) => current || next.items[0]?.id || '');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить задания');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const selected = useMemo(
    () => payload?.items.find((item) => item.id === selectedId) || payload?.items[0] || null,
    [payload, selectedId]
  );

  useEffect(() => {
    setAnswerText(selected?.submission?.answer_text || '');
  }, [selected?.id, selected?.submission?.answer_text]);

  async function submit(assignment: Assignment) {
    setSaving(true);
    setMessage('');
    try {
      await assignmentsApi.submitAssignment(assignment.id, {
        answer_text: answerText,
        attachments: [],
      });
      await load();
      setMessage('Ответ отправлен.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось отправить ответ');
    } finally {
      setSaving(false);
    }
  }

  return (
    <ProtectedPage title="Assignments" description="Домашние задания доступны после входа.">
      <section className="stack" style={{ gap: 24 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 8 }}>
            <span className="badge secondary">Homework</span>
            <h1>Домашние задания</h1>
            <p className="lead">Задания по активным курсам и программам, ответы и комментарии тренера.</p>
          </div>
          <div className="inline">
            <button className="button secondary" onClick={() => void load()} disabled={loading} type="button">Обновить</button>
            <Link className="button ghost" href="/learning">Обучение</Link>
          </div>
        </div>

        {message ? <div className="card">{message}</div> : null}
        {loading ? <div className="card"><p className="muted">Загружаем задания...</p></div> : null}

        {payload ? (
          <>
            <div className="grid-4">
              <div className="card"><div className="kpi"><span className="muted">Всего</span><strong>{payload.summary.total}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Ожидают</span><strong>{payload.summary.pending || 0}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Отправлено</span><strong>{payload.summary.submitted || 0}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Принято</span><strong>{payload.summary.approved || 0}</strong></div></div>
            </div>

            <div className="grid-2">
              <div className="card">
                <h2 className="title-md">Список заданий</h2>
                <div className="stack" style={{ gap: 10, marginTop: 14 }}>
                  {payload.items.map((assignment) => (
                    <button
                      className={`card compact text-left ${selected?.id === assignment.id ? 'is-active' : ''}`}
                      key={assignment.id}
                      onClick={() => setSelectedId(assignment.id)}
                      type="button"
                    >
                      <div className="row">
                        <div className="stack" style={{ gap: 4 }}>
                          <div className="inline">
                            <span className="badge secondary">{contentLabel(assignment.content_type)}</span>
                            <span className={assignment.submission ? 'badge success' : 'badge warning'}>
                              {statusLabel(assignment.submission?.status)}
                            </span>
                          </div>
                          <strong>{assignment.title}</strong>
                          <span className="muted">{assignment.trainer_email || 'trainer'} · {assignment.content_id}</span>
                        </div>
                      </div>
                    </button>
                  ))}
                  {!payload.items.length ? (
                    <div className="empty-state">
                      <h3>Заданий пока нет</h3>
                      <p>Они появятся здесь, когда тренер опубликует homework для доступного тебе курса.</p>
                      <Link className="button secondary" href="/learning">К обучению</Link>
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">{selected ? selected.title : 'Ответ'}</h2>
                {selected ? (
                  <div className="stack" style={{ gap: 14, marginTop: 14 }}>
                    <p>{selected.description || 'Тренер не добавил отдельное описание задания.'}</p>
                    <div className="inline">
                      <span className="badge secondary">{selected.content_type}</span>
                      <span className="badge secondary">lesson {selected.lesson_id || 'any'}</span>
                      {selected.due_at ? <span className="badge warning">due {new Date(selected.due_at).toLocaleString()}</span> : null}
                    </div>
                    <label className="stack" style={{ gap: 6 }}>
                      <span className="muted">Мой ответ</span>
                      <textarea
                        className="textarea"
                        rows={8}
                        value={answerText}
                        onChange={(event) => setAnswerText(event.target.value)}
                        placeholder="Напиши ответ, ссылку на работу или комментарий тренеру"
                      />
                    </label>
                    <button className="button" onClick={() => void submit(selected)} disabled={saving} type="button">
                      {selected.submission ? 'Обновить ответ' : 'Отправить ответ'}
                    </button>
                    {selected.submission ? (
                      <div className="card compact">
                        <div className="row">
                          <strong>{statusLabel(selected.submission.status)}</strong>
                          <span className="muted">{selected.submission.submitted_at ? new Date(selected.submission.submitted_at).toLocaleString() : ''}</span>
                        </div>
                        {selected.submission.review_comment ? <p>{selected.submission.review_comment}</p> : <p className="muted">Комментарий тренера пока пуст.</p>}
                        {selected.submission.score ? <span className="badge success">Score {selected.submission.score}</span> : null}
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <p className="muted">Выбери задание слева.</p>
                )}
              </div>
            </div>
          </>
        ) : null}
      </section>
    </ProtectedPage>
  );
}
