'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { ProtectedPage } from '@/components/protected-page';
import { apiRequest } from '@/lib/api-client';
import { progressApi } from '@/modules/progress/api';
import { studentLearningApi } from '@/modules/student-learning/api';
import type {
  ContentRuntimePayload,
  StudentLearningAreaPayload,
  StudentLearningItem,
  StudentLearningLesson,
} from '@/types/api';

function kindLabel(value: string) {
  if (value === 'course') return 'Курс';
  if (value === 'program') return 'Программа';
  if (value === 'video') return 'Видео';
  return value;
}

function lessonCount(item: StudentLearningItem) {
  return item.lessons?.length || 0;
}

function materialsCount(item: StudentLearningItem) {
  return item.materials?.length || 0;
}

function ProgressBar({ value }: { value: number }) {
  const bounded = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className="progress-track" aria-label={`Progress ${bounded}%`}>
      <div className="progress-bar" style={{ width: `${bounded}%` }} />
    </div>
  );
}

function LessonList({
  lessons,
  onComplete,
  onOpen,
}: {
  lessons: StudentLearningLesson[];
  onComplete: (lesson: StudentLearningLesson) => void;
  onOpen: (lesson: StudentLearningLesson) => void;
}) {
  if (!lessons.length) {
    return <p className="muted">Уроки появятся после публикации программы или курса.</p>;
  }
  return (
    <div className="stack" style={{ gap: 8 }}>
      {lessons.map((lesson) => (
        <div className="row" key={lesson.id}>
          <div className="stack" style={{ gap: 3 }}>
            <strong>{lesson.position}. {lesson.title}</strong>
            <span className="muted">
              {lesson.materials_count || 0} материалов · {lesson.is_completed ? 'completed' : lesson.is_preview ? 'preview' : 'protected'}
            </span>
          </div>
          {lesson.is_completed ? <span className="badge success">Готово</span> : null}
          <button className="button secondary" onClick={() => onOpen(lesson)} type="button">
            Открыть
          </button>
          {!lesson.is_completed ? (
            <button className="button ghost" onClick={() => onComplete(lesson)} type="button">
              Завершить
            </button>
          ) : null}
        </div>
      ))}
    </div>
  );
}

export default function StudentLearningPage() {
  const [payload, setPayload] = useState<StudentLearningAreaPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [openedLesson, setOpenedLesson] = useState<ContentRuntimePayload | null>(null);
  const [lessonMessage, setLessonMessage] = useState('');

  async function load() {
    setLoading(true);
    setMessage('');
    try {
      const next = await studentLearningApi.getLearningArea();
      setPayload(next);
      setSelectedId((current) => current || next.items[0]?.id || null);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить обучение');
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

  async function openLesson(lesson: StudentLearningLesson) {
    setOpenedLesson(null);
    setLessonMessage('');
    try {
      setOpenedLesson(await apiRequest<ContentRuntimePayload>(lesson.runtime_url, { auth: true }));
    } catch (err) {
      setLessonMessage(err instanceof Error ? err.message : 'Урок заблокирован или недоступен');
    }
  }

  async function completeLesson(lesson: StudentLearningLesson) {
    setLessonMessage('');
    try {
      await progressApi.completeLesson({
        lesson_id: lesson.lesson_id,
        program_id: lesson.program_id,
        content_type: lesson.content_type === 'course' ? 'course' : 'program',
      });
      await load();
    } catch (err) {
      setLessonMessage(err instanceof Error ? err.message : 'Не удалось сохранить прогресс урока');
    }
  }

  return (
    <ProtectedPage title="Learning area" description="Кабинет обучения доступен после входа.">
      <section className="stack" style={{ gap: 24 }}>
        <div className="row" style={{ alignItems: 'flex-start' }}>
          <div className="stack" style={{ gap: 8 }}>
            <span className="badge secondary">Student Learning</span>
            <h1>Моё обучение</h1>
            <p className="lead">Курсы, программы, уроки, материалы и активные доступы в одном рабочем экране.</p>
          </div>
          <div className="inline">
            <button className="button secondary" onClick={() => void load()} disabled={loading}>Обновить</button>
            <Link className="button ghost" href="/customer/access">Access center</Link>
          </div>
        </div>

        {message ? <div className="card error">{message}</div> : null}
        {loading ? <div className="card"><p className="muted">Загружаем обучение...</p></div> : null}

        {payload ? (
          <>
            <div className="grid-4">
              <div className="card"><div className="kpi"><span className="muted">Продукты</span><strong>{payload.summary.items_count}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Уроки</span><strong>{payload.summary.lessons_count}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Материалы</span><strong>{payload.summary.materials_count}</strong></div></div>
              <div className="card"><div className="kpi"><span className="muted">Library</span><strong>{payload.summary.library_access ? 'ON' : 'OFF'}</strong></div></div>
            </div>

            {payload.next_lesson ? (
              <div className="card">
                <div className="row" style={{ alignItems: 'center' }}>
                  <div className="stack" style={{ gap: 5 }}>
                    <span className="badge success">Next lesson</span>
                    <h2 className="title-md">{payload.next_lesson.title}</h2>
                    <p className="muted">{payload.next_lesson.materials_count || 0} материалов готовы к уроку</p>
                  </div>
                  <button className="button" onClick={() => payload.next_lesson && void openLesson(payload.next_lesson)} type="button">
                    Продолжить
                  </button>
                </div>
              </div>
            ) : null}

            {lessonMessage ? <div className="card error">{lessonMessage}</div> : null}
            {openedLesson ? (
              <div className="card">
                <div className="row" style={{ alignItems: 'flex-start' }}>
                  <div className="stack" style={{ gap: 6 }}>
                    <span className={openedLesson.allowed ? 'badge success' : 'badge danger'}>
                      {openedLesson.allowed ? 'Доступ открыт' : 'Доступ закрыт'}
                    </span>
                    <h2 className="title-md">{openedLesson.lesson.title}</h2>
                    <p className="muted">
                      {openedLesson.access.code} · video asset: {openedLesson.lesson.video_asset_id || 'hidden'}
                    </p>
                  </div>
                  <button className="button ghost" onClick={() => setOpenedLesson(null)} type="button">Закрыть</button>
                </div>
                {openedLesson.lesson.materials?.length ? (
                  <div className="grid-2" style={{ marginTop: 14 }}>
                    {openedLesson.lesson.materials.map((material, index) => (
                      <div className="card compact" key={`${material.title}-${index}`}>
                        <strong>{material.title}</strong>
                        <p className="muted">{material.kind || 'material'}</p>
                        {material.url ? <a className="button secondary" href={material.url}>Открыть материал</a> : null}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}

            <div className="grid-2">
              <div className="card">
                <h2 className="title-md">Мои курсы и программы</h2>
                <div className="stack" style={{ gap: 12, marginTop: 14 }}>
                  {payload.items.map((item) => (
                    <button
                      className={`card compact text-left ${selected?.id === item.id ? 'is-active' : ''}`}
                      key={item.id}
                      onClick={() => setSelectedId(item.id)}
                      type="button"
                    >
                      <div className="row">
                        <div className="stack" style={{ gap: 5 }}>
                          <div className="inline">
                            <span className="badge success">{item.status}</span>
                            <span className="badge secondary">{kindLabel(item.kind)}</span>
                          </div>
                          <strong>{item.title}</strong>
                          <span className="muted">{lessonCount(item)} уроков · {materialsCount(item)} материалов · {item.trainer_name || 'trainer'}</span>
                        </div>
                        <strong>{item.progress_percent || 0}%</strong>
                      </div>
                      <ProgressBar value={item.progress_percent || 0} />
                    </button>
                  ))}
                  {!payload.items.length ? (
                    <div className="empty-state">
                      <h3>Обучение пока пустое</h3>
                      <p>После оплаты курс или программа появятся здесь автоматически.</p>
                      <Link className="button secondary" href="/catalog">В каталог</Link>
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="card">
                <h2 className="title-md">{selected ? selected.title : 'Уроки'}</h2>
                {selected ? (
                  <div className="stack" style={{ gap: 16, marginTop: 14 }}>
                    <p className="muted">{selected.description || 'Описание появится после публикации.'}</p>
                    <ProgressBar value={selected.progress_percent || 0} />
                    {selected.access_url ? <Link className="button secondary" href={selected.access_url}>Открыть видео</Link> : null}
                    <LessonList
                      lessons={selected.lessons || []}
                      onComplete={(lesson) => void completeLesson(lesson)}
                      onOpen={(lesson) => void openLesson(lesson)}
                    />
                  </div>
                ) : (
                  <p className="muted">Выбери курс или программу слева.</p>
                )}
              </div>
            </div>

            <div className="card">
              <h2 className="title-md">Материалы</h2>
              <div className="grid-2" style={{ marginTop: 14 }}>
                {payload.materials.slice(0, 12).map((material, index) => (
                  <div className="card compact" key={`${material.lesson_id || 'material'}-${index}`}>
                    <div className="row">
                      <div className="stack" style={{ gap: 4 }}>
                        <strong>{material.title}</strong>
                        <span className="muted">{material.lesson_title || 'Урок'} · {material.kind || 'file'}</span>
                      </div>
                      {material.url ? <a className="button secondary" href={material.url}>Открыть</a> : null}
                    </div>
                  </div>
                ))}
                {!payload.materials.length ? <p className="muted">Материалы появятся вместе с уроками.</p> : null}
              </div>
            </div>
          </>
        ) : null}
      </section>
    </ProtectedPage>
  );
}
