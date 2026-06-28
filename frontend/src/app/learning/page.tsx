'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/protected-page';
import { apiRequest } from '@/lib/api-client';
import { progressApi } from '@/modules/progress/api';
import { studentLearningApi } from '@/modules/student-learning/api';
import {
  CustomerCabinetShell,
  CustomerEmptyState,
  CustomerErrorState,
  CustomerLoadingState,
  CustomerMetricCard,
  CustomerStatusBadge,
  type CustomerMetric,
} from '@/modules/customer-cabinet/components';
import { accessTypeLabel, formatCustomerDate, statusTone } from '@/modules/customer-cabinet/components/customer-format';
import type { ContentRuntimePayload, StudentLearningAreaPayload, StudentLearningItem, StudentLearningLesson } from '@/types/api';

function lessonStatus(lesson: StudentLearningLesson) {
  if (lesson.is_completed) return 'Завершён';
  if (lesson.is_preview) return 'Доступен для просмотра';
  return 'Доступ по покупке';
}

function ProgressBar({ value }: { value: number }) {
  const bounded = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className="customer-progress-bar" aria-label={`Прогресс ${bounded}%`}>
      <div className="customer-progress-fill" style={{ width: `${bounded}%` }} />
    </div>
  );
}

function itemHref(item: StudentLearningItem) {
  if (item.access_url) return item.access_url;
  if (item.kind === 'program' && item.slug) return `/catalog/programs/${item.slug}`;
  if (item.kind === 'video' && item.slug) return `/catalog/videos/${item.slug}`;
  return '/learning';
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
      setMessage(err instanceof Error ? err.message : 'Не удалось загрузить данные');
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
      setLessonMessage(err instanceof Error ? err.message : 'Урок пока недоступен');
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
      setLessonMessage(err instanceof Error ? err.message : 'Не удалось сохранить прогресс');
    }
  }

  const metrics: CustomerMetric[] = [
    { label: 'Продукты', value: payload?.summary.items_count ?? 0, hint: 'Курсы и программы', tone: 'neutral' },
    { label: 'Уроки', value: payload?.summary.lessons_count ?? 0, hint: 'В обучении', tone: 'success' },
    { label: 'Материалы', value: payload?.summary.materials_count ?? 0, hint: 'Файлы и ссылки', tone: 'neutral' },
    { label: 'Доступ к библиотеке', value: payload?.summary.library_access ? 'Открыт' : 'Нет данных', hint: 'По покупкам', tone: payload?.summary.library_access ? 'success' : 'warning' },
  ];

  return (
    <ProtectedPage title="Моё обучение" description="Кабинет обучения доступен после входа.">
      <CustomerCabinetShell
        title="Моё обучение"
        description="Курсы, программы, уроки, материалы и активные доступы собраны в одном рабочем экране."
        actions={<button className="premium-secondary-button" type="button" onClick={() => void load()} disabled={loading}>Обновить</button>}
      >
        <div className="customer-learning-page">
          <div className="customer-metric-grid">
            {metrics.map((metric) => <CustomerMetricCard key={metric.label} metric={metric} />)}
          </div>

          {message ? <CustomerErrorState message={message} onRetry={() => void load()} /> : null}
          {loading ? <CustomerLoadingState /> : null}

          {payload?.next_lesson ? (
            <section className="customer-learning-continue-card">
              <div>
                <CustomerStatusBadge tone="success">Следующий урок</CustomerStatusBadge>
                <h2>{payload.next_lesson.title}</h2>
                <p>{payload.next_lesson.materials_count || 0} материалов готовы к уроку.</p>
              </div>
              <button className="premium-primary-button" type="button" onClick={() => payload.next_lesson && void openLesson(payload.next_lesson)}>Продолжить</button>
            </section>
          ) : null}

          {lessonMessage ? <CustomerErrorState message={lessonMessage} /> : null}

          <div className="customer-learning-grid">
            <section className="customer-learning-list">
              <div className="customer-section-header"><h2>Программы и курсы</h2></div>
              {payload?.items.map((item) => (
                <button
                  className={selected?.id === item.id ? 'customer-learning-item customer-learning-item-active' : 'customer-learning-item'}
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedId(item.id)}
                >
                  <span>{accessTypeLabel(item.kind)}</span>
                  <strong>{item.title}</strong>
                  <small>{item.trainer_name || 'TrainerHub'} · {item.lessons?.length || 0} уроков</small>
                  <ProgressBar value={item.progress_percent || 0} />
                </button>
              ))}
              {!payload?.items.length && !loading ? <CustomerEmptyState title="Обучение пока пустое" description="После покупки курс или программа появятся здесь." /> : null}
            </section>

            <section className="customer-lesson-panel">
              <div className="customer-section-header">
                <div>
                  <h2>{selected?.title || 'Уроки'}</h2>
                  <p>{selected?.description || 'Выберите программу, чтобы увидеть уроки и материалы.'}</p>
                </div>
                {selected ? <Link href={itemHref(selected)} className="premium-secondary-button">Открыть продукт</Link> : null}
              </div>

              {selected ? <ProgressBar value={selected.progress_percent || 0} /> : null}

              <div className="customer-commerce-list">
                {selected?.lessons?.map((lesson) => (
                  <article className="customer-lesson-row" key={lesson.id}>
                    <div>
                      <CustomerStatusBadge tone={lesson.is_completed ? 'success' : lesson.is_preview ? 'warning' : 'neutral'}>{lessonStatus(lesson)}</CustomerStatusBadge>
                      <strong>{lesson.position}. {lesson.title}</strong>
                      <span>{lesson.materials_count || 0} материалов · {lesson.duration_minutes || 0} мин.</span>
                    </div>
                    <div className="customer-page-actions">
                      <button className="premium-secondary-button" type="button" onClick={() => void openLesson(lesson)}>Открыть урок</button>
                      {!lesson.is_completed ? <button className="premium-secondary-button" type="button" onClick={() => void completeLesson(lesson)}>Завершить урок</button> : null}
                    </div>
                  </article>
                ))}
              </div>

              {openedLesson ? (
                <section className="customer-section-card">
                  <div className="customer-section-header">
                    <div>
                      <CustomerStatusBadge tone={openedLesson.allowed ? 'success' : 'danger'}>{openedLesson.allowed ? 'Доступ открыт' : 'Доступ закрыт'}</CustomerStatusBadge>
                      <h2>{openedLesson.lesson.title}</h2>
                      <p>{openedLesson.lesson.description || 'Материалы урока доступны ниже.'}</p>
                    </div>
                    <button className="premium-secondary-button" type="button" onClick={() => setOpenedLesson(null)}>Вернуться к списку</button>
                  </div>
                  <div className="customer-materials-grid">
                    {(openedLesson.lesson.materials || []).map((material, index) => (
                      <article className="customer-material-card" key={`${material.title}-${index}`}>
                        <strong>{material.title}</strong>
                        <span>{accessTypeLabel(material.kind || 'material')}</span>
                        {material.url ? <a className="premium-secondary-button" href={material.url}>Открыть материал</a> : null}
                      </article>
                    ))}
                    {!openedLesson.lesson.materials?.length ? <CustomerEmptyState title="Материалов пока нет" description="Материалы появятся после публикации урока." actionHref="/learning" actionLabel="Вернуться к урокам" /> : null}
                  </div>
                </section>
              ) : null}
            </section>
          </div>

          <section className="customer-section-card">
            <div className="customer-section-header"><h2>Материалы</h2></div>
            <div className="customer-materials-grid">
              {payload?.materials.slice(0, 12).map((material, index) => (
                <article className="customer-material-card" key={`${material.lesson_id || 'material'}-${index}`}>
                  <strong>{material.title}</strong>
                  <span>{material.lesson_title || 'Урок'} · {accessTypeLabel(material.kind || 'material')}</span>
                  {material.url ? <a className="premium-secondary-button" href={material.url}>Открыть материал</a> : null}
                </article>
              ))}
              {!payload?.materials.length && !loading ? <CustomerEmptyState title="Материалов пока нет" description="Файлы и ссылки появятся вместе с уроками." /> : null}
            </div>
          </section>
        </div>
      </CustomerCabinetShell>
    </ProtectedPage>
  );
}
