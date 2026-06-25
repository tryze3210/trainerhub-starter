'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';

import { uploadApi } from '@/modules/upload/api';
import type { CourseDraft, CourseLessonDraft, LessonMaterial } from '@/types/api';

type CourseFormState = {
  title: string;
  slug: string;
  description: string;
  price_amount: string;
  currency: string;
};

type LessonFormState = {
  title: string;
  description: string;
  position: number;
  video_asset_id: string;
  materials_text: string;
  is_preview: boolean;
};

const emptyCourseForm: CourseFormState = {
  title: '',
  slug: '',
  description: '',
  price_amount: '0.00',
  currency: 'RUB',
};

const emptyLessonForm: LessonFormState = {
  title: '',
  description: '',
  position: 1,
  video_asset_id: '',
  materials_text: '',
  is_preview: false,
};

function statusBadge(status?: string) {
  if (status === 'published') return 'badge badge-success';
  if (status === 'archived') return 'badge badge-muted';
  return 'badge';
}

function parseMaterials(value: string): LessonMaterial[] {
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [title, url, kind] = line.split('|').map((item) => item.trim());
      return {
        title,
        url: url || undefined,
        kind: kind || (url ? 'link' : 'file'),
      };
    });
}

function formatMaterials(materials?: LessonMaterial[]) {
  return (materials || [])
    .map((item) => [item.title, item.url || '', item.kind || ''].filter(Boolean).join(' | '))
    .join('\n');
}

export function CourseProgramBuilderPanel() {
  const [courses, setCourses] = useState<CourseDraft[]>([]);
  const [lessons, setLessons] = useState<CourseLessonDraft[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null);
  const [editingLessonId, setEditingLessonId] = useState<string | null>(null);
  const [courseForm, setCourseForm] = useState<CourseFormState>(emptyCourseForm);
  const [lessonForm, setLessonForm] = useState<LessonFormState>(emptyLessonForm);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const selectedCourse = useMemo(
    () => courses.find((course) => course.id === selectedCourseId) || null,
    [courses, selectedCourseId]
  );

  async function reloadCourses(nextSelectedId?: string | null) {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await uploadApi.listMyCourses();
      setCourses(payload);
      const nextId = nextSelectedId ?? selectedCourseId ?? payload[0]?.id ?? null;
      setSelectedCourseId(nextId);
      if (nextId) {
        setLessons(await uploadApi.listCourseLessons(nextId));
      } else {
        setLessons([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить курсы');
    } finally {
      setIsLoading(false);
    }
  }

  async function reloadLessons(courseId: string) {
    setLessons(await uploadApi.listCourseLessons(courseId));
  }

  useEffect(() => {
    void reloadCourses();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedCourse) {
      setCourseForm(emptyCourseForm);
      return;
    }
    setCourseForm({
      title: selectedCourse.title,
      slug: selectedCourse.slug,
      description: selectedCourse.description || '',
      price_amount: selectedCourse.price_amount || '0.00',
      currency: selectedCourse.currency || 'RUB',
    });
  }, [selectedCourse]);

  async function selectCourse(courseId: string) {
    setSelectedCourseId(courseId);
    setEditingLessonId(null);
    setLessonForm(emptyLessonForm);
    setError(null);
    setMessage(null);
    try {
      setLessons(await uploadApi.listCourseLessons(courseId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить уроки');
    }
  }

  function newCourse() {
    setSelectedCourseId(null);
    setEditingLessonId(null);
    setCourseForm(emptyCourseForm);
    setLessonForm(emptyLessonForm);
    setLessons([]);
    setError(null);
    setMessage(null);
  }

  function editLesson(lesson: CourseLessonDraft) {
    setEditingLessonId(lesson.id);
    setLessonForm({
      title: lesson.title,
      description: lesson.description || '',
      position: lesson.position,
      video_asset_id: lesson.video_asset_id || '',
      materials_text: formatMaterials(lesson.materials),
      is_preview: Boolean(lesson.is_preview),
    });
  }

  async function submitCourse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      const payload = {
        ...courseForm,
        metadata: {
          builder_version: 'v97',
          product_kind: 'course',
        },
      };
      const course = selectedCourseId
        ? await uploadApi.updateCourseDraft(selectedCourseId, payload)
        : await uploadApi.createCourseDraft(payload);
      setMessage(selectedCourseId ? 'Курс обновлён' : 'Курс создан');
      await reloadCourses(course.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Курс не сохранён');
    } finally {
      setIsSaving(false);
    }
  }

  async function submitLesson(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedCourseId) return;
    setIsSaving(true);
    setError(null);
    setMessage(null);
    const payload = {
      title: lessonForm.title,
      description: lessonForm.description,
      position: Number(lessonForm.position) || lessons.length + 1,
      video_asset_id: lessonForm.video_asset_id || null,
      materials: parseMaterials(lessonForm.materials_text),
      is_preview: lessonForm.is_preview,
    };
    try {
      if (editingLessonId) {
        await uploadApi.updateCourseLesson(selectedCourseId, editingLessonId, payload);
        setMessage('Урок обновлён');
      } else {
        await uploadApi.createCourseLesson(selectedCourseId, payload);
        setMessage('Урок добавлен');
      }
      setEditingLessonId(null);
      setLessonForm({ ...emptyLessonForm, position: lessons.length + 2 });
      await reloadLessons(selectedCourseId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Урок не сохранён');
    } finally {
      setIsSaving(false);
    }
  }

  async function deleteLesson(lessonId: string) {
    if (!selectedCourseId) return;
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      await uploadApi.deleteCourseLesson(selectedCourseId, lessonId);
      setMessage('Урок удалён');
      if (editingLessonId === lessonId) {
        setEditingLessonId(null);
        setLessonForm(emptyLessonForm);
      }
      await reloadLessons(selectedCourseId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Урок не удалён');
    } finally {
      setIsSaving(false);
    }
  }

  async function publishCourse() {
    if (!selectedCourseId) return;
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      await uploadApi.publishCourseDraft(selectedCourseId);
      setMessage('Курс опубликован в CMS history');
      await reloadCourses(selectedCourseId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Курс не опубликован');
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <div>
          <h2>Course / Program Builder</h2>
          <p>Course drafts with ordered lessons, video asset links and lesson materials.</p>
        </div>
        <button className="btn btn-secondary" onClick={newCourse} type="button">
          New course
        </button>
      </div>

      {error ? <div className="alert alert-error">{error}</div> : null}
      {message ? <div className="alert alert-success">{message}</div> : null}

      <div className="grid grid-2 gap-4">
        <div className="stack gap-3">
          {isLoading ? <p>Загрузка...</p> : null}
          {!isLoading && courses.length === 0 ? <p>Курсов пока нет.</p> : null}
          {courses.map((course) => (
            <button
              className={`card text-left ${selectedCourseId === course.id ? 'is-active' : ''}`}
              key={course.id}
              onClick={() => void selectCourse(course.id)}
              type="button"
            >
              <div className="row row-between">
                <strong>{course.title}</strong>
                <span className={statusBadge(course.status)}>{course.status || 'draft'}</span>
              </div>
              <p>{course.price_amount} {course.currency} · lessons: {course.lessons?.length ?? 0}</p>
            </button>
          ))}
        </div>

        <div className="stack gap-4">
          <form className="form stack gap-3" onSubmit={submitCourse}>
            <div className="grid grid-2 gap-3">
              <label>
                Course title
                <input value={courseForm.title} onChange={(event) => setCourseForm((current) => ({ ...current, title: event.target.value }))} required />
              </label>
              <label>
                Slug
                <input value={courseForm.slug} onChange={(event) => setCourseForm((current) => ({ ...current, slug: event.target.value }))} required />
              </label>
            </div>
            <label>
              Description
              <textarea value={courseForm.description} onChange={(event) => setCourseForm((current) => ({ ...current, description: event.target.value }))} rows={3} />
            </label>
            <div className="grid grid-2 gap-3">
              <label>
                Price
                <input value={courseForm.price_amount} onChange={(event) => setCourseForm((current) => ({ ...current, price_amount: event.target.value }))} inputMode="decimal" />
              </label>
              <label>
                Currency
                <select value={courseForm.currency} onChange={(event) => setCourseForm((current) => ({ ...current, currency: event.target.value }))}>
                  <option value="RUB">RUB</option>
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                </select>
              </label>
            </div>
            <div className="row gap-2">
              <button className="btn" disabled={isSaving} type="submit">
                {selectedCourse ? 'Save course' : 'Create course'}
              </button>
              {selectedCourse ? (
                <button className="btn btn-secondary" disabled={isSaving} onClick={() => void publishCourse()} type="button">
                  Publish course
                </button>
              ) : null}
            </div>
          </form>

          {selectedCourse ? (
            <form className="form stack gap-3" onSubmit={submitLesson}>
              <h3>{editingLessonId ? 'Edit lesson' : 'Add lesson'}</h3>
              <div className="grid grid-2 gap-3">
                <label>
                  Lesson title
                  <input value={lessonForm.title} onChange={(event) => setLessonForm((current) => ({ ...current, title: event.target.value }))} required />
                </label>
                <label>
                  Position
                  <input value={lessonForm.position} onChange={(event) => setLessonForm((current) => ({ ...current, position: Number(event.target.value) }))} min={1} type="number" />
                </label>
              </div>
              <label>
                Video asset id
                <input value={lessonForm.video_asset_id} onChange={(event) => setLessonForm((current) => ({ ...current, video_asset_id: event.target.value }))} placeholder="UUID" />
              </label>
              <label>
                Materials
                <textarea value={lessonForm.materials_text} onChange={(event) => setLessonForm((current) => ({ ...current, materials_text: event.target.value }))} placeholder="Title | https://url | pdf" rows={4} />
              </label>
              <label className="row gap-2">
                <input checked={lessonForm.is_preview} onChange={(event) => setLessonForm((current) => ({ ...current, is_preview: event.target.checked }))} type="checkbox" />
                Preview lesson
              </label>
              <div className="row gap-2">
                <button className="btn" disabled={isSaving} type="submit">
                  {editingLessonId ? 'Save lesson' : 'Add lesson'}
                </button>
                {editingLessonId ? (
                  <button className="btn btn-secondary" onClick={() => { setEditingLessonId(null); setLessonForm(emptyLessonForm); }} type="button">
                    Cancel
                  </button>
                ) : null}
              </div>
            </form>
          ) : null}
        </div>
      </div>

      {selectedCourse ? (
        <div className="mt-4 stack gap-3">
          <h3>Lessons</h3>
          {lessons.length === 0 ? <p>Уроки ещё не добавлены.</p> : null}
          {lessons.map((lesson) => (
            <div className="card" key={lesson.id}>
              <div className="row row-between">
                <strong>{lesson.position}. {lesson.title}</strong>
                <span className="badge">{lesson.materials?.length || 0} materials</span>
              </div>
              <p>{lesson.description || 'No description'} · video: {lesson.video_asset_id || 'not linked'}</p>
              <div className="row gap-2">
                <button className="btn btn-secondary" onClick={() => editLesson(lesson)} type="button">
                  Edit
                </button>
                <button className="btn btn-danger" disabled={isSaving} onClick={() => void deleteLesson(lesson.id)} type="button">
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
