'use client';

import { useEffect, useMemo, useState } from 'react';

import { ProtectedPage } from '@/components/protected-page';
import { assignmentsApi } from '@/modules/assignments/api';
import { TrainerDashboardShell } from '@/modules/trainer-dashboard/components/trainer-dashboard-shell';
import type { AssignmentReviewPayload, AssignmentSubmission, AssignmentsPayload, AssignmentSubmissionsPayload } from '@/types/api';

const defaultForm = {
  title: '',
  description: '',
  content_type: 'course',
  content_id: '',
  lesson_id: '',
};

export default function TrainerAssignmentsPage() {
  const [assignments, setAssignments] = useState<AssignmentsPayload | null>(null);
  const [submissions, setSubmissions] = useState<AssignmentSubmissionsPayload | null>(null);
  const [form, setForm] = useState(defaultForm);
  const [reviewDrafts, setReviewDrafts] = useState<Record<string, AssignmentReviewPayload>>({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load() {
    setLoading(true);
    setMessage('');
    try {
      const [assignmentPayload, submissionPayload] = await Promise.all([
        assignmentsApi.getTrainerAssignments(),
        assignmentsApi.getTrainerSubmissions(),
      ]);
      setAssignments(assignmentPayload);
      setSubmissions(submissionPayload);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить задания');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const pendingSubmissions = useMemo(
    () => (submissions?.items || []).filter((item) => item.status === 'submitted' || item.status === 'needs_revision'),
    [submissions]
  );

  async function createAssignment() {
    setMessage('');
    try {
      await assignmentsApi.createAssignment({
        ...form,
        content_type: form.content_type as 'course' | 'program',
        status: 'published',
      });
      setForm(defaultForm);
      await load();
      setMessage('Задание опубликовано.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось создать задание');
    }
  }

  async function reviewSubmission(submission: AssignmentSubmission) {
    const draft = reviewDrafts[submission.id] || {};
    setMessage('');
    try {
      await assignmentsApi.reviewSubmission(submission.id, {
        status: draft.status || 'reviewed',
        review_comment: draft.review_comment || '',
        score: draft.score || null,
      });
      await load();
      setMessage('Проверка сохранена.');
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось сохранить ревью');
    }
  }

  function patchReview(id: string, patch: AssignmentReviewPayload) {
    setReviewDrafts((current) => ({
      ...current,
      [id]: {
        ...current[id],
        ...patch,
      },
    }));
  }

  return (
    <ProtectedPage title="Задания" description="Раздел заданий доступен только тренеру.">
      <TrainerDashboardShell
        title="Задания"
        description="Задания, ответы учеников, проверка тренером и статусы выполнения."
      >
        {message ? <div className="card">{message}</div> : null}
        {loading ? <div className="card"><p className="muted">Загружаем задания...</p></div> : null}

        <div className="trainer-assignment-page">
        <div className="grid-4">
          <div className="trainer-assignment-card"><div className="kpi"><span className="muted">Заданий</span><strong>{assignments?.summary.total || 0}</strong></div></div>
          <div className="trainer-assignment-card"><div className="kpi"><span className="muted">Опубликовано</span><strong>{assignments?.summary.published || 0}</strong></div></div>
          <div className="trainer-assignment-card"><div className="kpi"><span className="muted">Ответов</span><strong>{submissions?.summary.total || 0}</strong></div></div>
          <div className="trainer-assignment-card"><div className="kpi"><span className="muted">На проверку</span><strong>{pendingSubmissions.length}</strong></div></div>
        </div>

        <div className="trainer-assignment-grid">
          <div className="trainer-assignment-card">
            <h2 className="title-md">Создать задание</h2>
            <div className="stack" style={{ gap: 12, marginTop: 14 }}>
              <input className="input" value={form.title} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} placeholder="Название задания" />
              <textarea className="textarea" rows={4} value={form.description} onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))} placeholder="Описание и критерии проверки" />
              <div className="grid-2">
                <select className="input" value={form.content_type} onChange={(event) => setForm((prev) => ({ ...prev, content_type: event.target.value }))}>
                  <option value="course">Курс</option>
                  <option value="program">Программа</option>
                </select>
                <input className="input" value={form.content_id} onChange={(event) => setForm((prev) => ({ ...prev, content_id: event.target.value }))} placeholder="ID продукта" />
              </div>
              <input className="input" value={form.lesson_id} onChange={(event) => setForm((prev) => ({ ...prev, lesson_id: event.target.value }))} placeholder="ID урока, если задание привязано к уроку" />
              <button className="premium-primary-button" onClick={() => void createAssignment()} type="button">Опубликовать</button>
            </div>
          </div>

          <div className="trainer-assignment-card">
            <h2 className="title-md">Опубликованные задания</h2>
            <div className="stack" style={{ gap: 10, marginTop: 14 }}>
              {(assignments?.items || []).map((assignment) => (
                <div className="list-item" key={assignment.id}>
                  <div className="stack" style={{ gap: 3 }}>
                    <strong>{assignment.title}</strong>
                    <span className="muted">{assignment.content_type} · {assignment.content_id}</span>
                  </div>
                  <span className="badge secondary">{assignment.submissions_count || 0} ответов</span>
                </div>
              ))}
              {!assignments?.items.length ? <p className="muted">Заданий пока нет.</p> : null}
            </div>
          </div>
        </div>

        <div className="trainer-assignment-card">
          <h2 className="title-md">Ответы учеников</h2>
          <div className="stack" style={{ gap: 12, marginTop: 14 }}>
            {(submissions?.items || []).map((submission) => {
              const draft = reviewDrafts[submission.id] || {};
              return (
                <div className="trainer-submission-card" key={submission.id}>
                  <div className="row" style={{ alignItems: 'flex-start' }}>
                    <div className="stack" style={{ gap: 5 }}>
                      <div className="inline">
                        <span className="badge secondary">{submission.status}</span>
                        <span className="badge secondary">{submission.student_email || submission.student_id}</span>
                      </div>
                      <strong>{submission.assignment?.title || 'Задание'}</strong>
                      <p>{submission.answer_text || 'Ответ без текста.'}</p>
                    </div>
                    <span className="muted">{submission.submitted_at ? new Date(submission.submitted_at).toLocaleString() : ''}</span>
                  </div>
                  <div className="grid-2" style={{ marginTop: 12 }}>
                    <select className="input" value={draft.status || submission.status || 'reviewed'} onChange={(event) => patchReview(submission.id, { status: event.target.value as AssignmentReviewPayload['status'] })}>
                      <option value="reviewed">Проверено</option>
                      <option value="needs_revision">Нужна доработка</option>
                      <option value="approved">Принято</option>
                    </select>
                    <input className="input" value={draft.score ?? submission.score ?? ''} onChange={(event) => patchReview(submission.id, { score: event.target.value })} placeholder="оценка" />
                  </div>
                  <textarea
                    className="textarea"
                    rows={3}
                    style={{ marginTop: 10 }}
                    value={draft.review_comment ?? submission.review_comment ?? ''}
                    onChange={(event) => patchReview(submission.id, { review_comment: event.target.value })}
                    placeholder="Комментарий ученику"
                  />
                  <button className="premium-secondary-button" style={{ marginTop: 10 }} onClick={() => void reviewSubmission(submission)} type="button">
                    Сохранить проверку
                  </button>
                </div>
              );
            })}
            {!submissions?.items.length ? <p className="muted">Ответов пока нет.</p> : null}
          </div>
        </div>
        </div>
      </TrainerDashboardShell>
    </ProtectedPage>
  );
}
