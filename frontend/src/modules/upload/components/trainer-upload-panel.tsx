'use client';

import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { onboardingApi } from '@/modules/trainer-onboarding/api';
import { uploadApi } from '@/modules/upload/api';
import { uploadFileDirect } from '@/modules/upload/upload-file';
import type {
  BundleDraft,
  BundleItemDraft,
  ProgramDraft,
  ProgramLessonDraft,
  VideoDraft,
} from '@/types/api';

type TrainerContentTab = 'videos' | 'programs' | 'bundles';

type TrainerContentMetric = {
  label: string;
  value: string | number;
  hint?: string;
};

type TrainerContentStatusTone =
  | 'neutral'
  | 'success'
  | 'warning'
  | 'danger';

type TrainerProductPreview = {
  title: string;
  description: string;
  price: string;
  typeLabel: string;
  accessLabel: string;
  href?: string;
};

type DraftFormState = {
  title: string;
  slug: string;
  description: string;
  price_amount: string;
  currency: string;
};

type LessonFormState = {
  title: string;
  description: string;
  position: string;
  video_asset_id: string;
  is_preview: boolean;
};

type BundleItemFormState = {
  item_type: 'video' | 'program';
  target_id: string;
  position: string;
};

type StudioEntity = VideoDraft | ProgramDraft | BundleDraft;

const contentTabs: Array<{ id: TrainerContentTab; label: string }> = [
  { id: 'videos', label: 'Видео' },
  { id: 'programs', label: 'Программы' },
  { id: 'bundles', label: 'Наборы' },
];

const initialForm: DraftFormState = {
  title: '',
  slug: '',
  description: '',
  price_amount: '0',
  currency: 'RUB',
};

const initialLessonForm: LessonFormState = {
  title: '',
  description: '',
  position: '1',
  video_asset_id: '',
  is_preview: false,
};

const initialBundleItemForm: BundleItemFormState = {
  item_type: 'video',
  target_id: '',
  position: '1',
};

function makeSlug(value: string) {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9а-яё\s-]/gi, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

function statusLabel(status?: string) {
  switch (status) {
    case 'published':
      return 'Опубликовано';
    case 'review':
    case 'submitted':
    case 'under_review':
      return 'На проверке';
    case 'archived':
      return 'В архиве';
    default:
      return 'Черновик';
  }
}

function statusTone(status?: string): TrainerContentStatusTone {
  switch (status) {
    case 'published':
      return 'success';
    case 'review':
    case 'submitted':
    case 'under_review':
      return 'warning';
    case 'archived':
      return 'neutral';
    case 'rejected':
      return 'danger';
    default:
      return 'neutral';
  }
}

function resolveEntityLabel(tab: TrainerContentTab) {
  if (tab === 'videos') return 'видео';
  if (tab === 'programs') return 'программа';
  return 'набор';
}

function toFormState(draft?: Pick<StudioEntity, 'title' | 'slug' | 'description' | 'price_amount' | 'currency'> | null): DraftFormState {
  if (!draft) return initialForm;
  return {
    title: draft.title || '',
    slug: draft.slug || '',
    description: draft.description || '',
    price_amount: draft.price_amount || '0',
    currency: draft.currency || 'RUB',
  };
}

function toLessonFormState(lesson?: ProgramLessonDraft | null): LessonFormState {
  if (!lesson) return initialLessonForm;
  return {
    title: lesson.title || '',
    description: lesson.description || '',
    position: String(lesson.position || 1),
    video_asset_id: lesson.video_asset_id || '',
    is_preview: Boolean(lesson.is_preview),
  };
}

function toBundleItemFormState(item?: BundleItemDraft | null): BundleItemFormState {
  if (!item) return initialBundleItemForm;
  return {
    item_type: item.item_type === 'program' ? 'program' : 'video',
    target_id: item.target_id || item.video_id || item.program_id || '',
    position: String(item.position || 1),
  };
}

function formatPrice(value?: string, currency?: string) {
  const number = Number(value || 0);
  if (!Number.isFinite(number) || number <= 0) return 'Бесплатно';
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: currency || 'RUB',
    maximumFractionDigits: 2,
  }).format(number);
}

function entityCountLabel(tab: TrainerContentTab, count: number) {
  if (tab === 'programs') return `${count} уроков`;
  if (tab === 'bundles') return `${count} материалов`;
  return count > 0 ? 'Видеофайл подключён' : 'Видеофайл не подключён';
}

function previewFor(entity: StudioEntity | null, tab: TrainerContentTab): TrainerProductPreview {
  const typeLabel = tab === 'videos' ? 'Видео' : tab === 'programs' ? 'Программа' : 'Набор';
  return {
    title: entity?.title || typeLabel,
    description: entity?.description || 'Описание появится после сохранения материала.',
    price: formatPrice(entity?.price_amount, entity?.currency),
    typeLabel,
    accessLabel: 'Платный доступ',
    href: entity?.slug ? `/catalog/${tab}/${entity.slug}` : undefined,
  };
}

function StatusBadge({ status }: { status?: string }) {
  return <span className={`trainer-content-status trainer-content-status-${statusTone(status)}`}>{statusLabel(status)}</span>;
}

function FieldHint({ children }: { children: React.ReactNode }) {
  return <small className="trainer-content-field-hint">{children}</small>;
}

export function TrainerUploadPanel() {
  const [tab, setTab] = useState<TrainerContentTab>('videos');
  const [videos, setVideos] = useState<VideoDraft[]>([]);
  const [programs, setPrograms] = useState<ProgramDraft[]>([]);
  const [bundles, setBundles] = useState<BundleDraft[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [selectedProgramId, setSelectedProgramId] = useState<string | null>(null);
  const [selectedBundleId, setSelectedBundleId] = useState<string | null>(null);
  const [selectedLessonId, setSelectedLessonId] = useState<string | null>(null);
  const [selectedBundleItemId, setSelectedBundleItemId] = useState<string | null>(null);
  const [videoForm, setVideoForm] = useState<DraftFormState>(initialForm);
  const [programForm, setProgramForm] = useState<DraftFormState>(initialForm);
  const [bundleForm, setBundleForm] = useState<DraftFormState>(initialForm);
  const [lessonForm, setLessonForm] = useState<LessonFormState>(initialLessonForm);
  const [bundleItemForm, setBundleItemForm] = useState<BundleItemFormState>(initialBundleItemForm);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [actionId, setActionId] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const selectedVideo = useMemo(() => videos.find((video) => video.id === selectedVideoId) || null, [selectedVideoId, videos]);
  const selectedProgram = useMemo(() => programs.find((program) => program.id === selectedProgramId) || null, [selectedProgramId, programs]);
  const selectedBundle = useMemo(() => bundles.find((bundle) => bundle.id === selectedBundleId) || null, [selectedBundleId, bundles]);
  const selectedLesson = useMemo(() => selectedProgram?.lessons?.find((lesson) => lesson.id === selectedLessonId) || null, [selectedLessonId, selectedProgram]);
  const selectedBundleItem = useMemo(() => selectedBundle?.items?.find((item) => item.id === selectedBundleItemId) || null, [selectedBundleItemId, selectedBundle]);
  const assetVideoOptions = useMemo(() => videos.filter((video) => video.video_asset_id), [videos]);
  const bundleTargetOptions = useMemo(() => bundleItemForm.item_type === 'program' ? programs : videos, [bundleItemForm.item_type, programs, videos]);
  const sortedProgramLessons = useMemo(() => [...(selectedProgram?.lessons || [])].sort((left, right) => (left.position || 0) - (right.position || 0)), [selectedProgram]);
  const sortedBundleItems = useMemo(() => [...(selectedBundle?.items || [])].sort((left, right) => (left.position || 0) - (right.position || 0)), [selectedBundle]);
  const selectedLessonIndex = sortedProgramLessons.findIndex((lesson) => lesson.id === selectedLessonId);
  const selectedBundleItemIndex = sortedBundleItems.findIndex((item) => item.id === selectedBundleItemId);
  const preview = previewFor(tab === 'videos' ? selectedVideo : tab === 'programs' ? selectedProgram : selectedBundle, tab);

  const metrics: TrainerContentMetric[] = [
    { label: 'Видео', value: videos.length, hint: 'материалы библиотеки' },
    { label: 'Программы', value: programs.length, hint: 'структуры обучения' },
    { label: 'Наборы', value: bundles.length, hint: 'коммерческие комплекты' },
    { label: 'На проверке', value: [...videos, ...programs, ...bundles].filter((item) => ['review', 'submitted', 'under_review'].includes(item.status || '')).length },
  ];

  async function load() {
    try {
      setLoading(true);
      setError('');
      const [videoItems, programItems, bundleItems] = await Promise.all([
        uploadApi.listMyVideos(),
        uploadApi.listMyPrograms(),
        uploadApi.listMyBundles(),
      ]);
      setVideos(videoItems);
      setPrograms(programItems);
      setBundles(bundleItems);
      setSelectedVideoId((currentId) => (currentId && videoItems.some((item) => item.id === currentId) ? currentId : videoItems[0]?.id || null));
      setSelectedProgramId((currentId) => (currentId && programItems.some((item) => item.id === currentId) ? currentId : programItems[0]?.id || null));
      setSelectedBundleId((currentId) => (currentId && bundleItems.some((item) => item.id === currentId) ? currentId : bundleItems[0]?.id || null));
    } catch {
      setError('Не удалось загрузить материалы. Попробуйте обновить страницу или повторить действие позже.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    setVideoForm(toFormState(selectedVideo));
  }, [selectedVideo]);

  useEffect(() => {
    setProgramForm(toFormState(selectedProgram));
    setSelectedLessonId((currentId) => currentId && selectedProgram?.lessons?.some((lesson) => lesson.id === currentId) ? currentId : selectedProgram?.lessons?.[0]?.id || null);
  }, [selectedProgram]);

  useEffect(() => {
    setBundleForm(toFormState(selectedBundle));
    setSelectedBundleItemId((currentId) => currentId && selectedBundle?.items?.some((item) => item.id === currentId) ? currentId : selectedBundle?.items?.[0]?.id || null);
  }, [selectedBundle]);

  useEffect(() => {
    setLessonForm(toLessonFormState(selectedLesson));
  }, [selectedLesson]);

  useEffect(() => {
    const next = toBundleItemFormState(selectedBundleItem);
    if (selectedBundleItem) {
      setBundleItemForm(next);
      return;
    }
    setBundleItemForm((current) => ({
      ...current,
      target_id: current.target_id || (current.item_type === 'program' ? programs[0]?.id : videos[0]?.id) || '',
    }));
  }, [selectedBundleItem, programs, videos]);

  function resetMessages() {
    setError('');
    setMessage('');
  }

  function startNew(tabName: TrainerContentTab) {
    resetMessages();
    if (tabName === 'videos') {
      setSelectedVideoId(null);
      setVideoForm(initialForm);
      setFile(null);
    } else if (tabName === 'programs') {
      setSelectedProgramId(null);
      setSelectedLessonId(null);
      setProgramForm(initialForm);
      setLessonForm(initialLessonForm);
    } else {
      setSelectedBundleId(null);
      setSelectedBundleItemId(null);
      setBundleForm(initialForm);
      setBundleItemForm(initialBundleItemForm);
    }
  }

  async function saveVideo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSaving(true);
      resetMessages();
      const uploadedVideoAssetId = file ? await uploadFileDirect(file) : selectedVideo?.video_asset_id || null;
      const payload = {
        title: videoForm.title.trim(),
        slug: videoForm.slug.trim(),
        description: videoForm.description.trim(),
        price_amount: videoForm.price_amount.trim() || '0',
        currency: videoForm.currency.trim().toUpperCase() || 'RUB',
        video_asset_id: uploadedVideoAssetId,
      };
      const saved = selectedVideoId ? await uploadApi.updateVideoDraft(selectedVideoId, payload) : await uploadApi.createVideoDraft(payload);
      setSelectedVideoId(saved.id);
      setFile(null);
      setMessage(selectedVideoId ? 'Видео обновлено.' : 'Видеоурок сохранён.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить видео.');
    } finally {
      setSaving(false);
    }
  }

  async function saveProgram(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSaving(true);
      resetMessages();
      const payload = {
        title: programForm.title.trim(),
        slug: programForm.slug.trim(),
        description: programForm.description.trim(),
        price_amount: programForm.price_amount.trim() || '0',
        currency: programForm.currency.trim().toUpperCase() || 'RUB',
      };
      const saved = selectedProgramId ? await uploadApi.updateProgramDraft(selectedProgramId, payload) : await uploadApi.createProgramDraft(payload);
      setSelectedProgramId(saved.id);
      setMessage(selectedProgramId ? 'Программа обновлена.' : 'Программа сохранена.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить программу.');
    } finally {
      setSaving(false);
    }
  }

  async function saveBundle(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSaving(true);
      resetMessages();
      const payload = {
        title: bundleForm.title.trim(),
        slug: bundleForm.slug.trim(),
        description: bundleForm.description.trim(),
        price_amount: bundleForm.price_amount.trim() || '0',
        currency: bundleForm.currency.trim().toUpperCase() || 'RUB',
      };
      const saved = selectedBundleId ? await uploadApi.updateBundleDraft(selectedBundleId, payload) : await uploadApi.createBundleDraft(payload);
      setSelectedBundleId(saved.id);
      setMessage('Черновик набора сохранён.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить набор.');
    } finally {
      setSaving(false);
    }
  }

  async function saveLesson(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProgramId) {
      setError('Сначала создайте или выберите программу.');
      return;
    }
    try {
      setSaving(true);
      resetMessages();
      const payload = {
        title: lessonForm.title.trim(),
        description: lessonForm.description.trim(),
        position: Number(lessonForm.position || '1'),
        video_asset_id: lessonForm.video_asset_id || null,
        is_preview: lessonForm.is_preview,
      };
      const saved = selectedLessonId ? await uploadApi.updateProgramLesson(selectedProgramId, selectedLessonId, payload) : await uploadApi.createProgramLesson(selectedProgramId, payload);
      setSelectedLessonId(saved.id);
      setMessage('Урок сохранён.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить урок.');
    } finally {
      setSaving(false);
    }
  }

  async function deleteLesson() {
    if (!selectedProgramId || !selectedLessonId) return;
    try {
      setActionId(selectedLessonId);
      resetMessages();
      await uploadApi.deleteProgramLesson(selectedProgramId, selectedLessonId);
      setSelectedLessonId(null);
      setMessage('Урок удалён из программы.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить урок.');
    } finally {
      setActionId(null);
    }
  }

  async function saveBundleItem(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedBundleId) {
      setError('Сначала создайте или выберите набор.');
      return;
    }
    try {
      setSaving(true);
      resetMessages();
      const payload = {
        item_type: bundleItemForm.item_type,
        target_id: bundleItemForm.target_id,
        position: Number(bundleItemForm.position || '1'),
      };
      const saved = selectedBundleItemId ? await uploadApi.updateBundleItem(selectedBundleId, selectedBundleItemId, payload) : await uploadApi.createBundleItem(selectedBundleId, payload);
      setSelectedBundleItemId(saved.id);
      setMessage('Материал добавлен в набор.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить материал набора.');
    } finally {
      setSaving(false);
    }
  }

  async function deleteBundleItem() {
    if (!selectedBundleId || !selectedBundleItemId) return;
    try {
      setActionId(selectedBundleItemId);
      resetMessages();
      await uploadApi.deleteBundleItem(selectedBundleId, selectedBundleItemId);
      setSelectedBundleItemId(null);
      setMessage('Материал удалён из набора.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить материал из набора.');
    } finally {
      setActionId(null);
    }
  }

  async function moveLesson(direction: -1 | 1) {
    if (!selectedProgramId || !selectedLessonId || selectedLessonIndex < 0) return;
    const swapIndex = selectedLessonIndex + direction;
    if (swapIndex < 0 || swapIndex >= sortedProgramLessons.length) return;
    const current = sortedProgramLessons[selectedLessonIndex];
    const swapWith = sortedProgramLessons[swapIndex];
    try {
      setActionId(current.id);
      resetMessages();
      await Promise.all([
        uploadApi.updateProgramLesson(selectedProgramId, current.id, { position: swapWith.position || swapIndex + 1 }),
        uploadApi.updateProgramLesson(selectedProgramId, swapWith.id, { position: current.position || selectedLessonIndex + 1 }),
      ]);
      setMessage('Порядок уроков обновлён.');
      await load();
      setSelectedLessonId(current.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить порядок уроков.');
    } finally {
      setActionId(null);
    }
  }

  async function moveBundleItem(direction: -1 | 1) {
    if (!selectedBundleId || !selectedBundleItemId || selectedBundleItemIndex < 0) return;
    const swapIndex = selectedBundleItemIndex + direction;
    if (swapIndex < 0 || swapIndex >= sortedBundleItems.length) return;
    const current = sortedBundleItems[selectedBundleItemIndex];
    const swapWith = sortedBundleItems[swapIndex];
    try {
      setActionId(current.id);
      resetMessages();
      await Promise.all([
        uploadApi.updateBundleItem(selectedBundleId, current.id, { position: swapWith.position || swapIndex + 1 }),
        uploadApi.updateBundleItem(selectedBundleId, swapWith.id, { position: current.position || selectedBundleItemIndex + 1 }),
      ]);
      setMessage('Порядок материалов обновлён.');
      await load();
      setSelectedBundleItemId(current.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить порядок материалов.');
    } finally {
      setActionId(null);
    }
  }

  async function publishAndComplete(action: () => Promise<unknown>, draftId: string, entity: TrainerContentTab) {
    try {
      setActionId(draftId);
      resetMessages();
      await action();
      await onboardingApi.completeStep('first_publish', { source: `trainer-content-studio-${entity}` }).catch(() => null);
      setMessage(`${resolveEntityLabel(entity)} опубликована.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось выполнить публикацию.');
    } finally {
      setActionId(null);
    }
  }

  async function submitVideoForReview(draftId: string) {
    try {
      setActionId(draftId);
      resetMessages();
      await uploadApi.submitVideoDraft(draftId);
      setMessage('Видео отправлено на проверку.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить видео на проверку.');
    } finally {
      setActionId(null);
    }
  }

  function lessonTargetLabel(videoAssetId?: string | null) {
    if (!videoAssetId) return 'Видеофайл не выбран';
    return assetVideoOptions.find((video) => video.video_asset_id === videoAssetId)?.title || 'Видеофайл из библиотеки';
  }

  function bundleTargetLabel(item: BundleItemDraft) {
    if (item.target_title || item.source_title || item.title || item.name || item.label) {
      return item.target_title || item.source_title || item.title || item.name || item.label || 'Материал';
    }
    const source = item.item_type === 'program'
      ? programs.find((program) => program.id === item.target_id || program.id === item.program_id)
      : videos.find((video) => video.id === item.target_id || video.id === item.video_id);
    return source?.title || 'Материал';
  }

  function renderContentCard(entity: StudioEntity, entityTab: TrainerContentTab) {
    const isSelected =
      (entityTab === 'videos' && selectedVideoId === entity.id) ||
      (entityTab === 'programs' && selectedProgramId === entity.id) ||
      (entityTab === 'bundles' && selectedBundleId === entity.id);
    const count = entityTab === 'videos'
      ? (entity as VideoDraft).video_asset_id ? 1 : 0
      : entityTab === 'programs'
        ? (entity as ProgramDraft).lessons?.length || 0
        : (entity as BundleDraft).items?.length || 0;

    return (
      <article key={entity.id} className={isSelected ? 'trainer-content-card trainer-content-card-active' : 'trainer-content-card'}>
        <div className="trainer-content-card-meta">
          <StatusBadge status={entity.status} />
          <span>{formatPrice(entity.price_amount, entity.currency)}</span>
        </div>
        <h3>{entity.title}</h3>
        <p>{entity.description || 'Описание пока не заполнено.'}</p>
        <div className="trainer-content-card-meta">
          <span>Публичный адрес: {entity.slug || 'не указан'}</span>
          <span>{entityCountLabel(entityTab, count)}</span>
        </div>
        <div className="trainer-content-actions">
          <button className="premium-secondary-button" type="button" onClick={() => {
            if (entityTab === 'videos') setSelectedVideoId(entity.id);
            if (entityTab === 'programs') setSelectedProgramId(entity.id);
            if (entityTab === 'bundles') setSelectedBundleId(entity.id);
          }}>
            Редактировать
          </button>
          {entityTab === 'videos' ? (
            <button className="premium-secondary-button" type="button" onClick={() => void submitVideoForReview(entity.id)} disabled={actionId === entity.id}>
              Отправить на проверку
            </button>
          ) : null}
          <button
            className="premium-primary-button"
            type="button"
            onClick={() => void publishAndComplete(
              () => entityTab === 'videos'
                ? uploadApi.publishVideoDraft(entity.id)
                : entityTab === 'programs'
                  ? uploadApi.publishProgramDraft(entity.id)
                  : uploadApi.publishBundleDraft(entity.id),
              entity.id,
              entityTab
            )}
            disabled={actionId === entity.id}
          >
            Опубликовать
          </button>
        </div>
      </article>
    );
  }

  if (loading) {
    return (
      <section className="trainer-content-studio">
        <div className="trainer-content-editor">
          <h2>Загружаем материалы</h2>
          <p>Получаем видео, программы и наборы тренера.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="trainer-content-studio">
      <div className="trainer-content-studio-hero">
        <div>
          <span className="trainer-content-kicker">Видео и материалы</span>
          <h2>Видео, программы и наборы</h2>
          <p>Загружайте видеоуроки, собирайте программы и наборы, готовьте материалы к публикации в каталоге.</p>
        </div>
        <div className="trainer-content-studio-tabs" role="tablist" aria-label="Разделы материалов">
          {contentTabs.map((item) => (
            <button
              key={item.id}
              type="button"
              className={tab === item.id ? 'trainer-content-studio-tab trainer-content-studio-tab-active' : 'trainer-content-studio-tab'}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="trainer-product-builder-metrics">
        {metrics.map((metric) => (
          <div className="trainer-content-metric" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            {metric.hint ? <small>{metric.hint}</small> : null}
          </div>
        ))}
      </div>

      {message ? <div className="trainer-content-state trainer-content-state-success">{message}</div> : null}
      {error ? <div className="trainer-content-state trainer-content-state-error">Не удалось загрузить материалы. Попробуйте обновить страницу или повторить действие позже.</div> : null}

      <div className="trainer-content-studio-grid">
        <div className="trainer-content-list">
          {tab === 'videos' && videos.length === 0 ? <div className="trainer-content-card"><h3>Видео пока нет</h3><p>Загрузите первый видеоурок, чтобы использовать его в программах и продуктах.</p></div> : null}
          {tab === 'programs' && programs.length === 0 ? <div className="trainer-content-card"><h3>Программ пока нет</h3><p>Создайте программу и добавьте уроки из библиотеки видео.</p></div> : null}
          {tab === 'bundles' && bundles.length === 0 ? <div className="trainer-content-card"><h3>Наборов пока нет</h3><p>Соберите несколько видео или программ в один платный набор.</p></div> : null}
          {tab === 'videos' ? videos.map((video) => renderContentCard(video, 'videos')) : null}
          {tab === 'programs' ? programs.map((program) => renderContentCard(program, 'programs')) : null}
          {tab === 'bundles' ? bundles.map((bundle) => renderContentCard(bundle, 'bundles')) : null}
        </div>

        <div className="trainer-content-editor">
          {tab === 'videos' ? (
            <form className="trainer-content-form" onSubmit={saveVideo}>
              <div className="trainer-content-editor-header">
                <div>
                  <h2>Видеоурок</h2>
                  <p>Загрузите файл, заполните название, описание и цену. После проверки видео можно опубликовать в каталоге или использовать в программе.</p>
                </div>
                <button className="premium-secondary-button" type="button" onClick={() => startNew('videos')} disabled={saving || Boolean(actionId)}>Новый видеоурок</button>
              </div>
              <label className="trainer-content-field"><span>Название видео</span><input className="input" value={videoForm.title} onChange={(event) => setVideoForm((current) => ({ ...current, title: event.target.value, slug: current.slug || makeSlug(event.target.value) }))} required /></label>
              <label className="trainer-content-field"><span>Публичный адрес</span><input className="input" value={videoForm.slug} onChange={(event) => setVideoForm((current) => ({ ...current, slug: makeSlug(event.target.value) }))} required /></label>
              <label className="trainer-content-field"><span>Описание</span><textarea className="textarea" rows={4} value={videoForm.description} onChange={(event) => setVideoForm((current) => ({ ...current, description: event.target.value }))} /></label>
              <div className="trainer-content-form-grid">
                <label className="trainer-content-field"><span>Цена</span><input className="input" type="number" min="0" step="0.01" value={videoForm.price_amount} onChange={(event) => setVideoForm((current) => ({ ...current, price_amount: event.target.value }))} /></label>
                <label className="trainer-content-field"><span>Валюта</span><input className="input" value={videoForm.currency} onChange={(event) => setVideoForm((current) => ({ ...current, currency: event.target.value.toUpperCase() }))} /></label>
                <label className="trainer-content-field"><span>Видеофайл</span><input className="input" type="file" accept="video/mp4,video/quicktime" onChange={(event) => setFile(event.target.files?.[0] || null)} /></label>
              </div>
              <FieldHint>Можно сначала сохранить черновик, а файл добавить позже.</FieldHint>
              <div className="trainer-content-actions">
                <button className="premium-primary-button" type="submit" disabled={saving}>{selectedVideoId ? 'Обновить видео' : 'Сохранить видео'}</button>
              </div>
            </form>
          ) : null}

          {tab === 'programs' ? (
            <div className="trainer-program-editor">
              <form className="trainer-content-form" onSubmit={saveProgram}>
                <div className="trainer-content-editor-header">
                  <div>
                    <h2>Программа</h2>
                    <p>Соберите программу из уроков, добавьте описание, цену и подготовьте продукт к публикации.</p>
                  </div>
                  <button className="premium-secondary-button" type="button" onClick={() => startNew('programs')} disabled={saving || Boolean(actionId)}>Новая программа</button>
                </div>
                <label className="trainer-content-field"><span>Название программы</span><input className="input" value={programForm.title} onChange={(event) => setProgramForm((current) => ({ ...current, title: event.target.value, slug: current.slug || makeSlug(event.target.value) }))} required /></label>
                <label className="trainer-content-field"><span>Публичный адрес</span><input className="input" value={programForm.slug} onChange={(event) => setProgramForm((current) => ({ ...current, slug: makeSlug(event.target.value) }))} required /></label>
                <label className="trainer-content-field"><span>Описание</span><textarea className="textarea" rows={4} value={programForm.description} onChange={(event) => setProgramForm((current) => ({ ...current, description: event.target.value }))} /></label>
                <div className="trainer-content-form-grid">
                  <label className="trainer-content-field"><span>Цена</span><input className="input" type="number" min="0" step="0.01" value={programForm.price_amount} onChange={(event) => setProgramForm((current) => ({ ...current, price_amount: event.target.value }))} /></label>
                  <label className="trainer-content-field"><span>Валюта</span><input className="input" value={programForm.currency} onChange={(event) => setProgramForm((current) => ({ ...current, currency: event.target.value.toUpperCase() }))} /></label>
                </div>
                <div className="trainer-content-actions">
                  <button className="premium-primary-button" type="submit" disabled={saving}>{selectedProgramId ? 'Обновить программу' : 'Сохранить программу'}</button>
                  {selectedProgramId ? <button className="premium-secondary-button" type="button" onClick={() => void publishAndComplete(() => uploadApi.publishProgramDraft(selectedProgramId), selectedProgramId, 'programs')} disabled={saving || Boolean(actionId)}>Опубликовать программу</button> : null}
                </div>
              </form>

              <div className="trainer-lesson-editor">
                <div className="trainer-content-editor-header">
                  <div>
                    <h3>Уроки программы</h3>
                    <p>Добавьте уроки, задайте порядок и привяжите нужный видеофайл из библиотеки.</p>
                  </div>
                  <button className="premium-secondary-button" type="button" onClick={() => { setSelectedLessonId(null); setLessonForm(initialLessonForm); }} disabled={!selectedProgramId}>Добавить урок</button>
                </div>
                <form className="trainer-content-form" onSubmit={saveLesson}>
                  <label className="trainer-content-field"><span>Название урока</span><input className="input" value={lessonForm.title} onChange={(event) => setLessonForm((current) => ({ ...current, title: event.target.value }))} required /></label>
                  <label className="trainer-content-field"><span>Описание урока</span><textarea className="textarea" rows={3} value={lessonForm.description} onChange={(event) => setLessonForm((current) => ({ ...current, description: event.target.value }))} /></label>
                  <div className="trainer-content-form-grid">
                    <label className="trainer-content-field"><span>Порядок</span><input className="input" type="number" min="1" value={lessonForm.position} onChange={(event) => setLessonForm((current) => ({ ...current, position: event.target.value }))} /></label>
                    <label className="trainer-content-field"><span>Видеофайл</span><select className="select" value={lessonForm.video_asset_id} onChange={(event) => setLessonForm((current) => ({ ...current, video_asset_id: event.target.value }))}><option value="">Выберите видеофайл</option>{assetVideoOptions.map((video) => <option key={video.id} value={video.video_asset_id || ''}>{video.title}</option>)}</select></label>
                  </div>
                  <label className="trainer-content-checkbox"><input type="checkbox" checked={lessonForm.is_preview} onChange={(event) => setLessonForm((current) => ({ ...current, is_preview: event.target.checked }))} /><span>Открытый урок для просмотра</span></label>
                  <div className="trainer-content-actions">
                    <button className="premium-primary-button" type="submit" disabled={saving || !selectedProgramId}>Сохранить урок</button>
                    <button className="premium-secondary-button" type="button" onClick={() => void deleteLesson()} disabled={!selectedLessonId || actionId === selectedLessonId}>Удалить урок</button>
                    <button className="premium-secondary-button" type="button" onClick={() => void moveLesson(-1)} disabled={selectedLessonIndex <= 0 || Boolean(actionId)}>Выше</button>
                    <button className="premium-secondary-button" type="button" onClick={() => void moveLesson(1)} disabled={selectedLessonIndex < 0 || selectedLessonIndex >= sortedProgramLessons.length - 1 || Boolean(actionId)}>Ниже</button>
                  </div>
                </form>
                <div className="trainer-lesson-list">
                  {sortedProgramLessons.map((lesson) => (
                    <button className={selectedLessonId === lesson.id ? 'trainer-lesson-card trainer-content-card-active' : 'trainer-lesson-card'} key={lesson.id} type="button" onClick={() => setSelectedLessonId(lesson.id)}>
                      <strong>{lesson.position}. {lesson.title}</strong>
                      <span>{lesson.is_preview ? 'Открытый урок' : 'Закрытый урок'} · {lessonTargetLabel(lesson.video_asset_id)}</span>
                    </button>
                  ))}
                  {!sortedProgramLessons.length ? <div className="trainer-lesson-card"><strong>Уроков пока нет</strong><span>Добавьте первый урок программы.</span></div> : null}
                </div>
              </div>
            </div>
          ) : null}

          {tab === 'bundles' ? (
            <div className="trainer-bundle-editor">
              <form className="trainer-content-form" onSubmit={saveBundle}>
                <div className="trainer-content-editor-header">
                  <div>
                    <h2>Набор</h2>
                    <p>Соберите несколько видео и программ в один платный набор.</p>
                  </div>
                  <button className="premium-secondary-button" type="button" onClick={() => startNew('bundles')} disabled={saving || Boolean(actionId)}>Новый набор</button>
                </div>
                <label className="trainer-content-field"><span>Название набора</span><input className="input" value={bundleForm.title} onChange={(event) => setBundleForm((current) => ({ ...current, title: event.target.value, slug: current.slug || makeSlug(event.target.value) }))} required /></label>
                <label className="trainer-content-field"><span>Публичный адрес</span><input className="input" value={bundleForm.slug} onChange={(event) => setBundleForm((current) => ({ ...current, slug: makeSlug(event.target.value) }))} required /></label>
                <label className="trainer-content-field"><span>Описание</span><textarea className="textarea" rows={4} value={bundleForm.description} onChange={(event) => setBundleForm((current) => ({ ...current, description: event.target.value }))} /></label>
                <div className="trainer-content-form-grid">
                  <label className="trainer-content-field"><span>Цена</span><input className="input" type="number" min="0" step="0.01" value={bundleForm.price_amount} onChange={(event) => setBundleForm((current) => ({ ...current, price_amount: event.target.value }))} /></label>
                  <label className="trainer-content-field"><span>Валюта</span><input className="input" value={bundleForm.currency} onChange={(event) => setBundleForm((current) => ({ ...current, currency: event.target.value.toUpperCase() }))} /></label>
                </div>
                <div className="trainer-content-actions">
                  <button className="premium-primary-button" type="submit" disabled={saving}>{selectedBundleId ? 'Сохранить набор' : 'Новый набор'}</button>
                  {selectedBundleId ? <button className="premium-secondary-button" type="button" onClick={() => void publishAndComplete(() => uploadApi.publishBundleDraft(selectedBundleId), selectedBundleId, 'bundles')} disabled={saving || Boolean(actionId)}>Опубликовать набор</button> : null}
                </div>
              </form>

              <form className="trainer-content-form" onSubmit={saveBundleItem}>
                <h3>Материалы набора</h3>
                <p>Для публикации набора целевые видео и программы должны быть опубликованы.</p>
                <div className="trainer-content-form-grid">
                  <label className="trainer-content-field"><span>Тип материала</span><select className="select" value={bundleItemForm.item_type} onChange={(event) => setBundleItemForm((current) => ({ ...current, item_type: event.target.value === 'program' ? 'program' : 'video' }))}><option value="video">Видео</option><option value="program">Программа</option></select></label>
                  <label className="trainer-content-field"><span>Материал</span><select className="select" value={bundleItemForm.target_id} onChange={(event) => setBundleItemForm((current) => ({ ...current, target_id: event.target.value }))}><option value="">Выберите материал</option>{bundleTargetOptions.map((target) => <option key={target.id} value={target.id}>{target.title}</option>)}</select></label>
                  <label className="trainer-content-field"><span>Порядок</span><input className="input" type="number" min="1" value={bundleItemForm.position} onChange={(event) => setBundleItemForm((current) => ({ ...current, position: event.target.value }))} /></label>
                </div>
                <div className="trainer-content-actions">
                  <button className="premium-primary-button" type="submit" disabled={saving || !selectedBundleId}>Добавить материал</button>
                  <button className="premium-secondary-button" type="button" onClick={() => void deleteBundleItem()} disabled={!selectedBundleItemId || actionId === selectedBundleItemId}>Удалить материал</button>
                  <button className="premium-secondary-button" type="button" onClick={() => void moveBundleItem(-1)} disabled={selectedBundleItemIndex <= 0 || Boolean(actionId)}>Выше</button>
                  <button className="premium-secondary-button" type="button" onClick={() => void moveBundleItem(1)} disabled={selectedBundleItemIndex < 0 || selectedBundleItemIndex >= sortedBundleItems.length - 1 || Boolean(actionId)}>Ниже</button>
                </div>
              </form>

              <div className="trainer-lesson-list">
                {sortedBundleItems.map((item) => (
                  <button className={selectedBundleItemId === item.id ? 'trainer-bundle-item-card trainer-content-card-active' : 'trainer-bundle-item-card'} key={item.id} type="button" onClick={() => setSelectedBundleItemId(item.id)}>
                    <strong>{bundleTargetLabel(item)}</strong>
                    <span>{item.item_type === 'program' ? 'Программа' : 'Видео'} · позиция {item.position || 0}</span>
                  </button>
                ))}
                {!sortedBundleItems.length ? <div className="trainer-bundle-item-card"><strong>Материалов пока нет</strong><span>Добавьте видео или программу в набор.</span></div> : null}
              </div>
            </div>
          ) : null}
        </div>

        <aside className="trainer-content-preview">
          <h3>Предпросмотр для каталога</h3>
          <StatusBadge status={(tab === 'videos' ? selectedVideo : tab === 'programs' ? selectedProgram : selectedBundle)?.status} />
          <strong>{preview.title}</strong>
          <p>{preview.description}</p>
          <span>{preview.typeLabel} · {preview.price} · {preview.accessLabel}</span>
          {preview.href ? <a className="premium-secondary-button" href={preview.href}>Предпросмотр</a> : <span>Предпросмотр появится после сохранения публичного адреса.</span>}
        </aside>
      </div>
    </section>
  );
}
