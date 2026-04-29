'use client';

import { useEffect, useMemo, useState } from 'react';
import { ErrorCard, LoadingCard } from '@/components/async-state';
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

type ContentTab = 'videos' | 'programs' | 'bundles';

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

function statusTone(status?: string) {
  switch (status) {
    case 'published':
      return 'success';
    case 'review':
    case 'submitted':
    case 'under_review':
      return 'warning';
    case 'archived':
      return 'secondary';
    default:
      return 'secondary';
  }
}

function statusLabel(status?: string) {
  switch (status) {
    case 'published':
      return 'Published';
    case 'review':
      return 'Review';
    case 'submitted':
      return 'Submitted';
    case 'under_review':
      return 'Under review';
    case 'archived':
      return 'Archived';
    default:
      return 'Draft';
  }
}

function toFormState(
  draft?: Pick<VideoDraft | ProgramDraft | BundleDraft, 'title' | 'slug' | 'description' | 'price_amount' | 'currency'> | null
): DraftFormState {
  if (!draft) {
    return initialForm;
  }
  return {
    title: draft.title || '',
    slug: draft.slug || '',
    description: draft.description || '',
    price_amount: draft.price_amount || '0',
    currency: draft.currency || 'RUB',
  };
}

function toLessonFormState(lesson?: ProgramLessonDraft | null): LessonFormState {
  if (!lesson) {
    return initialLessonForm;
  }
  return {
    title: lesson.title || '',
    description: lesson.description || '',
    position: String(lesson.position || 1),
    video_asset_id: lesson.video_asset_id || '',
    is_preview: Boolean(lesson.is_preview),
  };
}

function toBundleItemFormState(item?: BundleItemDraft | null): BundleItemFormState {
  if (!item) {
    return initialBundleItemForm;
  }
  return {
    item_type: item.item_type === 'program' ? 'program' : 'video',
    target_id: item.target_id || '',
    position: String(item.position || 1),
  };
}

function formatPrice(value?: string, currency?: string) {
  const number = Number(value || 0);
  if (!Number.isFinite(number) || number <= 0) {
    return 'Бесплатно';
  }
  return `${number.toFixed(2)} ${currency || 'RUB'}`;
}

function resolveEntityLabel(tab: ContentTab) {
  if (tab === 'videos') return 'видео';
  if (tab === 'programs') return 'программа';
  return 'bundle';
}

export function TrainerUploadPanel() {
  const [tab, setTab] = useState<ContentTab>('videos');
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

  const selectedVideo = useMemo(
    () => videos.find((video) => video.id === selectedVideoId) || null,
    [selectedVideoId, videos]
  );
  const selectedProgram = useMemo(
    () => programs.find((program) => program.id === selectedProgramId) || null,
    [selectedProgramId, programs]
  );
  const selectedBundle = useMemo(
    () => bundles.find((bundle) => bundle.id === selectedBundleId) || null,
    [selectedBundleId, bundles]
  );
  const selectedLesson = useMemo(
    () => selectedProgram?.lessons?.find((lesson) => lesson.id === selectedLessonId) || null,
    [selectedLessonId, selectedProgram]
  );
  const selectedBundleItem = useMemo(
    () => selectedBundle?.items?.find((item) => item.id === selectedBundleItemId) || null,
    [selectedBundleItemId, selectedBundle]
  );

  const assetVideoOptions = useMemo(
    () => videos.filter((video) => video.video_asset_id),
    [videos]
  );

  const bundleTargetOptions = useMemo(() => {
    return bundleItemForm.item_type === 'program' ? programs : videos;
  }, [bundleItemForm.item_type, programs, videos]);

  const sortedProgramLessons = useMemo(
    () => [...(selectedProgram?.lessons || [])].sort((left, right) => (left.position || 0) - (right.position || 0)),
    [selectedProgram]
  );

  const sortedBundleItems = useMemo(
    () => [...(selectedBundle?.items || [])].sort((left, right) => (left.position || 0) - (right.position || 0)),
    [selectedBundle]
  );

  const selectedLessonIndex = sortedProgramLessons.findIndex((lesson) => lesson.id === selectedLessonId);
  const selectedBundleItemIndex = sortedBundleItems.findIndex((item) => item.id === selectedBundleItemId);
  const canMoveLessonUp = selectedLessonIndex > 0;
  const canMoveLessonDown = selectedLessonIndex >= 0 && selectedLessonIndex < sortedProgramLessons.length - 1;
  const canMoveBundleItemUp = selectedBundleItemIndex > 0;
  const canMoveBundleItemDown = selectedBundleItemIndex >= 0 && selectedBundleItemIndex < sortedBundleItems.length - 1;

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить content studio');
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
    setSelectedLessonId((currentId) =>
      currentId && selectedProgram?.lessons?.some((lesson) => lesson.id === currentId)
        ? currentId
        : selectedProgram?.lessons?.[0]?.id || null
    );
  }, [selectedProgram]);

  useEffect(() => {
    setBundleForm(toFormState(selectedBundle));
    setSelectedBundleItemId((currentId) =>
      currentId && selectedBundle?.items?.some((item) => item.id === currentId)
        ? currentId
        : selectedBundle?.items?.[0]?.id || null
    );
  }, [selectedBundle]);

  useEffect(() => {
    setLessonForm(toLessonFormState(selectedLesson));
  }, [selectedLesson]);

  useEffect(() => {
    setBundleItemForm((current) => {
      const next = toBundleItemFormState(selectedBundleItem);
      if (selectedBundleItem) {
        return next;
      }
      const firstTarget = (current.item_type === 'program' ? programs[0]?.id : videos[0]?.id) || '';
      return {
        ...current,
        target_id: current.target_id || firstTarget,
      };
    });
  }, [selectedBundleItem, programs, videos]);

  useEffect(() => {
    if (!bundleTargetOptions.some((item) => item.id === bundleItemForm.target_id)) {
      setBundleItemForm((current) => ({
        ...current,
        target_id: bundleTargetOptions[0]?.id || '',
      }));
    }
  }, [bundleItemForm.item_type, bundleItemForm.target_id, bundleTargetOptions]);

  function resetMessages() {
    setError('');
    setMessage('');
  }

  async function saveVideo(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setSaving(true);
      resetMessages();

      let uploadedVideoAssetId = selectedVideo?.video_asset_id || null;
      if (file) {
        uploadedVideoAssetId = await uploadFileDirect(file);
      }

      const payload = {
        title: videoForm.title.trim(),
        slug: videoForm.slug.trim(),
        description: videoForm.description.trim(),
        price_amount: videoForm.price_amount.trim() || '0',
        currency: videoForm.currency.trim().toUpperCase() || 'RUB',
        video_asset_id: uploadedVideoAssetId,
      };

      const savedDraft = selectedVideoId
        ? await uploadApi.updateVideoDraft(selectedVideoId, payload)
        : await uploadApi.createVideoDraft(payload);

      setSelectedVideoId(savedDraft.id);
      setFile(null);
      setMessage(
        file
          ? 'Видео-черновик сохранён. Файл загружен, теперь его можно отправлять на review и publish.'
          : 'Черновик видео сохранён.'
      );
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить видео-черновик');
    } finally {
      setSaving(false);
    }
  }

  async function saveProgram(event: React.FormEvent<HTMLFormElement>) {
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
      const savedDraft = selectedProgramId
        ? await uploadApi.updateProgramDraft(selectedProgramId, payload)
        : await uploadApi.createProgramDraft(payload);
      setSelectedProgramId(savedDraft.id);
      setMessage('Черновик программы сохранён. Теперь можно собрать lessons editor и публиковать структуру курса как продукт.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить программу');
    } finally {
      setSaving(false);
    }
  }

  async function saveBundle(event: React.FormEvent<HTMLFormElement>) {
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
      const savedDraft = selectedBundleId
        ? await uploadApi.updateBundleDraft(selectedBundleId, payload)
        : await uploadApi.createBundleDraft(payload);
      setSelectedBundleId(savedDraft.id);
      setMessage('Черновик bundle сохранён. Теперь можно собрать состав оффера и публиковать storefront bundle.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить bundle');
    } finally {
      setSaving(false);
    }
  }

  async function saveLesson(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedProgramId) {
      setError('Сначала создай или выбери программу.');
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
      const savedLesson = selectedLessonId
        ? await uploadApi.updateProgramLesson(selectedProgramId, selectedLessonId, payload)
        : await uploadApi.createProgramLesson(selectedProgramId, payload);
      setSelectedLessonId(savedLesson.id);
      setMessage('Lesson сохранён. После публикации программы он появится на storefront.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить lesson');
    } finally {
      setSaving(false);
    }
  }

  async function deleteLesson() {
    if (!selectedProgramId || !selectedLessonId) {
      return;
    }
    try {
      setActionId(selectedLessonId);
      resetMessages();
      await uploadApi.deleteProgramLesson(selectedProgramId, selectedLessonId);
      setSelectedLessonId(null);
      setMessage('Lesson удалён из программы.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить lesson');
    } finally {
      setActionId(null);
    }
  }

  async function saveBundleItem(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedBundleId) {
      setError('Сначала создай или выбери bundle.');
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
      const savedItem = selectedBundleItemId
        ? await uploadApi.updateBundleItem(selectedBundleId, selectedBundleItemId, payload)
        : await uploadApi.createBundleItem(selectedBundleId, payload);
      setSelectedBundleItemId(savedItem.id);
      setMessage('Элемент bundle сохранён. Для публикации bundle целевые видео/программы должны уже быть published.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить элемент bundle');
    } finally {
      setSaving(false);
    }
  }

  async function deleteBundleItem() {
    if (!selectedBundleId || !selectedBundleItemId) {
      return;
    }
    try {
      setActionId(selectedBundleItemId);
      resetMessages();
      await uploadApi.deleteBundleItem(selectedBundleId, selectedBundleItemId);
      setSelectedBundleItemId(null);
      setMessage('Элемент удалён из bundle.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось удалить элемент bundle');
    } finally {
      setActionId(null);
    }
  }

  async function moveLesson(direction: -1 | 1) {
    if (!selectedProgramId || !selectedLessonId || selectedLessonIndex < 0) {
      return;
    }
    const swapIndex = selectedLessonIndex + direction;
    if (swapIndex < 0 || swapIndex >= sortedProgramLessons.length) {
      return;
    }

    const current = sortedProgramLessons[selectedLessonIndex];
    const swapWith = sortedProgramLessons[swapIndex];

    try {
      setActionId(current.id);
      resetMessages();
      await Promise.all([
        uploadApi.updateProgramLesson(selectedProgramId, current.id, { position: swapWith.position || swapIndex + 1 }),
        uploadApi.updateProgramLesson(selectedProgramId, swapWith.id, { position: current.position || selectedLessonIndex + 1 }),
      ]);
      setMessage('Порядок lessons обновлён.');
      await load();
      setSelectedLessonId(current.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить порядок lessons');
    } finally {
      setActionId(null);
    }
  }

  async function moveBundleItem(direction: -1 | 1) {
    if (!selectedBundleId || !selectedBundleItemId || selectedBundleItemIndex < 0) {
      return;
    }
    const swapIndex = selectedBundleItemIndex + direction;
    if (swapIndex < 0 || swapIndex >= sortedBundleItems.length) {
      return;
    }

    const current = sortedBundleItems[selectedBundleItemIndex];
    const swapWith = sortedBundleItems[swapIndex];

    try {
      setActionId(current.id);
      resetMessages();
      await Promise.all([
        uploadApi.updateBundleItem(selectedBundleId, current.id, { position: swapWith.position || swapIndex + 1 }),
        uploadApi.updateBundleItem(selectedBundleId, swapWith.id, { position: current.position || selectedBundleItemIndex + 1 }),
      ]);
      setMessage('Порядок bundle items обновлён.');
      await load();
      setSelectedBundleItemId(current.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось изменить порядок bundle items');
    } finally {
      setActionId(null);
    }
  }

  async function publishAndComplete(action: () => Promise<unknown>, draftId: string, entity: ContentTab) {
    try {
      setActionId(draftId);
      resetMessages();
      await action();
      await onboardingApi.completeStep('first_publish', {
        source: `trainer-content-studio-${entity}`,
      }).catch(() => null);
      setMessage(`${resolveEntityLabel(entity)} опубликована. Шаг first_publish отмечен в onboarding.`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось выполнить публикацию');
    } finally {
      setActionId(null);
    }
  }

  async function submitVideoForReview(draftId: string) {
    try {
      setActionId(draftId);
      resetMessages();
      await uploadApi.submitVideoDraft(draftId);
      setMessage('Видео отправлено на review. После этого его можно publish-ить через trainer CMS.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось отправить видео на review');
    } finally {
      setActionId(null);
    }
  }

  async function archiveVideo(draftId: string) {
    try {
      setActionId(draftId);
      resetMessages();
      await uploadApi.archiveVideoDraft(draftId);
      setMessage('Видео переведено в archived status.');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось архивировать видео');
    } finally {
      setActionId(null);
    }
  }

  function startNew(tabName: ContentTab) {
    resetMessages();
    if (tabName === 'videos') {
      setSelectedVideoId(null);
      setVideoForm(initialForm);
      setFile(null);
      return;
    }
    if (tabName === 'programs') {
      setSelectedProgramId(null);
      setSelectedLessonId(null);
      setProgramForm(initialForm);
      setLessonForm(initialLessonForm);
      return;
    }
    setSelectedBundleId(null);
    setSelectedBundleItemId(null);
    setBundleForm(initialForm);
    setBundleItemForm(initialBundleItemForm);
  }

  function lessonTargetLabel(videoAssetId?: string | null) {
    if (!videoAssetId) return 'asset missing';
    const target = assetVideoOptions.find((video) => video.video_asset_id === videoAssetId);
    return target ? `${target.title} · ${statusLabel(target.status)}` : videoAssetId;
  }

  function bundleTargetLabel(item: BundleItemDraft) {
    if (item.item_type === 'program') {
      return programs.find((program) => program.id === item.target_id)?.title || item.target_id;
    }
    return videos.find((video) => video.id === item.target_id)?.title || item.target_id;
  }

  function renderVideoCard(video: VideoDraft) {
    const isSelected = selectedVideoId === video.id;
    return (
      <article key={video.id} className={`card trainer-draft-card${isSelected ? ' is-selected' : ''}`}>
        <div className="stack" style={{ gap: 10 }}>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <span className={`badge ${statusTone(video.status)}`}>{statusLabel(video.status)}</span>
            <span className="muted">{formatPrice(video.price_amount, video.currency)}</span>
          </div>
          <div>
            <h3 style={{ marginBottom: 6 }}>{video.title}</h3>
            <p className="muted">slug: {video.slug}</p>
          </div>
          <p>{video.description || 'Описание видео пока не заполнено.'}</p>
          <div className="trainer-draft-card__meta">
            <span>asset: {video.video_asset_id ? 'connected' : 'missing'}</span>
            <span>v{video.current_version_number || 0}</span>
          </div>
          <div className="inline trainer-card-actions">
            <button className="button ghost" type="button" onClick={() => setSelectedVideoId(video.id)}>
              Edit
            </button>
            <button className="button secondary" type="button" onClick={() => void submitVideoForReview(video.id)} disabled={actionId === video.id}>
              Submit
            </button>
            <button className="button" type="button" onClick={() => void publishAndComplete(() => uploadApi.publishVideoDraft(video.id), video.id, 'videos')} disabled={actionId === video.id}>
              Publish
            </button>
            <button className="button ghost danger" type="button" onClick={() => void archiveVideo(video.id)} disabled={actionId === video.id}>
              Archive
            </button>
          </div>
        </div>
      </article>
    );
  }

  function renderProgramCard(program: ProgramDraft) {
    const isSelected = selectedProgramId === program.id;
    return (
      <article key={program.id} className={`card trainer-draft-card${isSelected ? ' is-selected' : ''}`}>
        <div className="stack" style={{ gap: 10 }}>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <span className={`badge ${statusTone(program.status)}`}>{statusLabel(program.status)}</span>
            <span className="muted">{formatPrice(program.price_amount, program.currency)}</span>
          </div>
          <div>
            <h3 style={{ marginBottom: 6 }}>{program.title}</h3>
            <p className="muted">slug: {program.slug}</p>
          </div>
          <p>{program.description || 'Описание программы пока не заполнено.'}</p>
          <div className="trainer-draft-card__meta">
            <span>lessons: {program.lessons?.length || 0}</span>
            <span>v{program.current_version_number || 0}</span>
          </div>
          <div className="inline trainer-card-actions">
            <button className="button ghost" type="button" onClick={() => setSelectedProgramId(program.id)}>
              Edit
            </button>
            <button className="button" type="button" onClick={() => void publishAndComplete(() => uploadApi.publishProgramDraft(program.id), program.id, 'programs')} disabled={actionId === program.id}>
              Publish
            </button>
          </div>
        </div>
      </article>
    );
  }

  function renderBundleCard(bundle: BundleDraft) {
    const isSelected = selectedBundleId === bundle.id;
    return (
      <article key={bundle.id} className={`card trainer-draft-card${isSelected ? ' is-selected' : ''}`}>
        <div className="stack" style={{ gap: 10 }}>
          <div className="inline" style={{ justifyContent: 'space-between' }}>
            <span className={`badge ${statusTone(bundle.status)}`}>{statusLabel(bundle.status)}</span>
            <span className="muted">{formatPrice(bundle.price_amount, bundle.currency)}</span>
          </div>
          <div>
            <h3 style={{ marginBottom: 6 }}>{bundle.title}</h3>
            <p className="muted">slug: {bundle.slug}</p>
          </div>
          <p>{bundle.description || 'Описание bundle пока не заполнено.'}</p>
          <div className="trainer-draft-card__meta">
            <span>items: {bundle.items?.length || 0}</span>
            <span>storefront-ready</span>
          </div>
          <div className="inline trainer-card-actions">
            <button className="button ghost" type="button" onClick={() => setSelectedBundleId(bundle.id)}>
              Edit
            </button>
            <button className="button" type="button" onClick={() => void publishAndComplete(() => uploadApi.publishBundleDraft(bundle.id), bundle.id, 'bundles')} disabled={actionId === bundle.id}>
              Publish
            </button>
          </div>
        </div>
      </article>
    );
  }

  if (loading) {
    return <LoadingCard text="Загружаем content studio тренера…" />;
  }

  return (
    <div className="stack" style={{ gap: 24 }}>
      <div className="card trainer-content-studio-hero">
        <div className="stack" style={{ gap: 10 }}>
          <span className="badge">Content studio</span>
          <h2 className="title-md" style={{ margin: 0 }}>Видео, программы и bundles в одном месте</h2>
          <p className="muted">
            Контур теперь закрывает не только upload flow. Можно собрать lessons editor для программы,
            composition editor для bundle и довести сущности до checkout-ready storefront.
          </p>
        </div>
        <div className="trainer-studio-tabs" role="tablist" aria-label="Trainer content tabs">
          {(['videos', 'programs', 'bundles'] as ContentTab[]).map((tabName) => (
            <button
              key={tabName}
              type="button"
              className={`trainer-studio-tab${tab === tabName ? ' is-active' : ''}`}
              onClick={() => setTab(tabName)}
            >
              {tabName === 'videos' ? `Видео (${videos.length})` : tabName === 'programs' ? `Программы (${programs.length})` : `Bundles (${bundles.length})`}
            </button>
          ))}
        </div>
      </div>

      {message ? <div className="card success">{message}</div> : null}
      {error ? <ErrorCard text={error} /> : null}

      {tab === 'videos' ? (
        <div className="grid-2 trainer-section-grid">
          <section className="card trainer-panel">
            <div className="row trainer-panel__header">
              <div>
                <h3 className="title-md" style={{ marginBottom: 6 }}>Video draft editor</h3>
                <p className="muted">Сначала собираем draft, затем цепляем asset, отправляем на review и публикуем.</p>
              </div>
              <div className="inline">
                <button className="button secondary" type="button" onClick={() => void load()} disabled={saving || Boolean(actionId)}>
                  Обновить
                </button>
                <button className="button" type="button" onClick={() => startNew('videos')} disabled={saving || Boolean(actionId)}>
                  Новый draft
                </button>
              </div>
            </div>

            <form className="form" onSubmit={saveVideo}>
              <div className="grid-2">
                <div className="form-group">
                  <label className="label" htmlFor="video_title">Название видео</label>
                  <input
                    id="video_title"
                    className="input"
                    value={videoForm.title}
                    onChange={(event) => {
                      const nextTitle = event.target.value;
                      setVideoForm((current) => ({
                        ...current,
                        title: nextTitle,
                        slug: current.slug ? current.slug : makeSlug(nextTitle),
                      }));
                    }}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="video_slug">Slug</label>
                  <input
                    id="video_slug"
                    className="input"
                    value={videoForm.slug}
                    onChange={(event) => setVideoForm((current) => ({ ...current, slug: makeSlug(event.target.value) }))}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="label" htmlFor="video_description">Описание</label>
                <textarea
                  id="video_description"
                  className="textarea"
                  rows={4}
                  value={videoForm.description}
                  onChange={(event) => setVideoForm((current) => ({ ...current, description: event.target.value }))}
                />
              </div>

              <div className="grid-3">
                <div className="form-group">
                  <label className="label" htmlFor="video_price">Цена</label>
                  <input
                    id="video_price"
                    className="input"
                    type="number"
                    min="0"
                    step="0.01"
                    value={videoForm.price_amount}
                    onChange={(event) => setVideoForm((current) => ({ ...current, price_amount: event.target.value }))}
                  />
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="video_currency">Валюта</label>
                  <input
                    id="video_currency"
                    className="input"
                    value={videoForm.currency}
                    onChange={(event) => setVideoForm((current) => ({ ...current, currency: event.target.value.toUpperCase() }))}
                  />
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="video_file">Видео-файл</label>
                  <input
                    id="video_file"
                    className="input"
                    type="file"
                    accept="video/mp4,video/quicktime"
                    onChange={(event) => setFile(event.target.files?.[0] || null)}
                  />
                </div>
              </div>

              <div className="trainer-note-box compact">
                <strong>Текущий asset</strong>
                <p>{selectedVideo?.video_asset_id || 'Пока не прикреплён. Можно сначала сохранить metadata draft, а файл добавить позже.'}</p>
              </div>

              <button className="button" type="submit" disabled={saving}>
                {saving ? 'Сохраняем…' : selectedVideoId ? 'Обновить video draft' : 'Создать video draft'}
              </button>
            </form>
          </section>

          <section className="stack" style={{ gap: 16 }}>
            {videos.length === 0 ? <div className="card"><p className="muted">Черновиков видео пока нет.</p></div> : videos.map(renderVideoCard)}
          </section>
        </div>
      ) : null}

      {tab === 'programs' ? (
        <div className="grid-2 trainer-section-grid">
          <section className="card trainer-panel">
            <div className="row trainer-panel__header">
              <div>
                <h3 className="title-md" style={{ marginBottom: 6 }}>Program draft editor</h3>
                <p className="muted">Собираем программу как продукт: metadata, lessons roadmap и checkout-ready publish.</p>
              </div>
              <button className="button" type="button" onClick={() => startNew('programs')} disabled={saving || Boolean(actionId)}>
                Новая программа
              </button>
            </div>

            <form className="form" onSubmit={saveProgram}>
              <div className="grid-2">
                <div className="form-group">
                  <label className="label" htmlFor="program_title">Название программы</label>
                  <input
                    id="program_title"
                    className="input"
                    value={programForm.title}
                    onChange={(event) => {
                      const nextTitle = event.target.value;
                      setProgramForm((current) => ({
                        ...current,
                        title: nextTitle,
                        slug: current.slug ? current.slug : makeSlug(nextTitle),
                      }));
                    }}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="program_slug">Slug</label>
                  <input
                    id="program_slug"
                    className="input"
                    value={programForm.slug}
                    onChange={(event) => setProgramForm((current) => ({ ...current, slug: makeSlug(event.target.value) }))}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="label" htmlFor="program_description">Описание</label>
                <textarea
                  id="program_description"
                  className="textarea"
                  rows={5}
                  value={programForm.description}
                  onChange={(event) => setProgramForm((current) => ({ ...current, description: event.target.value }))}
                />
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="label" htmlFor="program_price">Цена</label>
                  <input
                    id="program_price"
                    className="input"
                    type="number"
                    min="0"
                    step="0.01"
                    value={programForm.price_amount}
                    onChange={(event) => setProgramForm((current) => ({ ...current, price_amount: event.target.value }))}
                  />
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="program_currency">Валюта</label>
                  <input
                    id="program_currency"
                    className="input"
                    value={programForm.currency}
                    onChange={(event) => setProgramForm((current) => ({ ...current, currency: event.target.value.toUpperCase() }))}
                  />
                </div>
              </div>

              <button className="button" type="submit" disabled={saving}>
                {saving ? 'Сохраняем…' : selectedProgramId ? 'Обновить программу' : 'Создать программу'}
              </button>
            </form>

            <div className="trainer-composer card compact shadow-none surface-muted">
              <div className="row trainer-panel__header">
                <div>
                  <h4 className="title-sm" style={{ marginBottom: 4 }}>Lessons editor</h4>
                  <p className="muted">Каждый урок должен быть связан с уже загруженным video asset. Порядок можно менять прямо в roadmap.</p>
                </div>
                <button className="button ghost" type="button" onClick={() => { setSelectedLessonId(null); setLessonForm(initialLessonForm); }} disabled={!selectedProgramId}>
                  Новый lesson
                </button>
              </div>

              {!selectedProgramId ? (
                <div className="card compact warning">Сначала создай программу, чтобы редактировать её lessons.</div>
              ) : (
                <form className="form" onSubmit={saveLesson}>
                  <div className="grid-2">
                    <div className="form-group">
                      <label className="label" htmlFor="lesson_title">Название урока</label>
                      <input
                        id="lesson_title"
                        className="input"
                        value={lessonForm.title}
                        onChange={(event) => setLessonForm((current) => ({ ...current, title: event.target.value }))}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label className="label" htmlFor="lesson_position">Позиция</label>
                      <input
                        id="lesson_position"
                        className="input"
                        type="number"
                        min="1"
                        value={lessonForm.position}
                        onChange={(event) => setLessonForm((current) => ({ ...current, position: event.target.value }))}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="label" htmlFor="lesson_description">Описание урока</label>
                    <textarea
                      id="lesson_description"
                      className="textarea"
                      rows={3}
                      value={lessonForm.description}
                      onChange={(event) => setLessonForm((current) => ({ ...current, description: event.target.value }))}
                    />
                  </div>

                  <div className="grid-2">
                    <div className="form-group">
                      <label className="label" htmlFor="lesson_asset">Источник видео</label>
                      <select
                        id="lesson_asset"
                        className="select"
                        value={lessonForm.video_asset_id}
                        onChange={(event) => setLessonForm((current) => ({ ...current, video_asset_id: event.target.value }))}
                      >
                        <option value="">Выбери video asset</option>
                        {assetVideoOptions.map((video) => (
                          <option key={video.id} value={video.video_asset_id || ''}>
                            {video.title} · {statusLabel(video.status)}
                          </option>
                        ))}
                      </select>
                    </div>
                    <label className="checkbox trainer-checkbox-row">
                      <input
                        type="checkbox"
                        checked={lessonForm.is_preview}
                        onChange={(event) => setLessonForm((current) => ({ ...current, is_preview: event.target.checked }))}
                      />
                      <span>Дать preview-доступ к уроку</span>
                    </label>
                  </div>

                  <div className="inline trainer-card-actions">
                    <button className="button" type="submit" disabled={saving}>
                      {saving ? 'Сохраняем…' : selectedLessonId ? 'Обновить lesson' : 'Добавить lesson'}
                    </button>
                    <button className="button ghost danger" type="button" onClick={() => void deleteLesson()} disabled={!selectedLessonId || actionId === selectedLessonId}>
                      Удалить lesson
                    </button>
                    <button className="button ghost" type="button" onClick={() => void moveLesson(-1)} disabled={!selectedLessonId || !canMoveLessonUp || Boolean(actionId)}>
                      Выше
                    </button>
                    <button className="button ghost" type="button" onClick={() => void moveLesson(1)} disabled={!selectedLessonId || !canMoveLessonDown || Boolean(actionId)}>
                      Ниже
                    </button>
                  </div>
                </form>
              )}
            </div>
          </section>

          <section className="stack" style={{ gap: 16 }}>
            {programs.length === 0 ? <div className="card"><p className="muted">Черновиков программ пока нет.</p></div> : programs.map(renderProgramCard)}

            {selectedProgramId ? (
              <div className="card trainer-panel">
                <div className="row trainer-panel__header">
                  <div>
                    <h3 className="title-md" style={{ marginBottom: 6 }}>Lessons roadmap</h3>
                    <p className="muted">Что уже войдёт в опубликованную программу.</p>
                  </div>
                  <span className="badge secondary">{selectedProgram?.lessons?.length || 0}</span>
                </div>
                {(selectedProgram?.lessons || []).length ? (
                  <div className="stack" style={{ gap: 12 }}>
                    {sortedProgramLessons.map((lesson) => (
                      <article key={lesson.id} className={`card compact shadow-none surface-muted trainer-subitem-card${selectedLessonId === lesson.id ? ' is-selected' : ''}`}>
                        <div className="stack" style={{ gap: 8 }}>
                          <div className="inline" style={{ justifyContent: 'space-between' }}>
                            <strong>{lesson.position ? `Lesson ${lesson.position}` : 'Lesson'}</strong>
                            {lesson.is_preview ? <span className="badge success">Preview</span> : <span className="badge secondary">Locked</span>}
                          </div>
                          <h4 style={{ margin: 0 }}>{lesson.title}</h4>
                          <p>{lesson.description || 'Описание урока пока не заполнено.'}</p>
                          <div className="trainer-draft-card__meta">
                            <span>{lessonTargetLabel(lesson.video_asset_id)}</span>
                          </div>
                          <div className="inline trainer-card-actions trainer-reorder-controls">
                            <button className="button ghost" type="button" onClick={() => setSelectedLessonId(lesson.id)}>
                              Edit lesson
                            </button>
                            {selectedLessonId === lesson.id ? (
                              <>
                                <button className="button ghost" type="button" onClick={() => void moveLesson(-1)} disabled={!canMoveLessonUp || Boolean(actionId)}>Выше</button>
                                <button className="button ghost" type="button" onClick={() => void moveLesson(1)} disabled={!canMoveLessonDown || Boolean(actionId)}>Ниже</button>
                              </>
                            ) : null}
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state compact">
                    <h3>Уроков пока нет</h3>
                    <p>Добавь хотя бы один lesson, чтобы программа стала publish-ready.</p>
                  </div>
                )}
              </div>
            ) : null}
          </section>
        </div>
      ) : null}

      {tab === 'bundles' ? (
        <div className="grid-2 trainer-section-grid">
          <section className="card trainer-panel">
            <div className="row trainer-panel__header">
              <div>
                <h3 className="title-md" style={{ marginBottom: 6 }}>Bundle draft editor</h3>
                <p className="muted">Bundle становится оффером, когда в него собран состав из published видео и программ.</p>
              </div>
              <button className="button" type="button" onClick={() => startNew('bundles')} disabled={saving || Boolean(actionId)}>
                Новый bundle
              </button>
            </div>

            <form className="form" onSubmit={saveBundle}>
              <div className="grid-2">
                <div className="form-group">
                  <label className="label" htmlFor="bundle_title">Название bundle</label>
                  <input
                    id="bundle_title"
                    className="input"
                    value={bundleForm.title}
                    onChange={(event) => {
                      const nextTitle = event.target.value;
                      setBundleForm((current) => ({
                        ...current,
                        title: nextTitle,
                        slug: current.slug ? current.slug : makeSlug(nextTitle),
                      }));
                    }}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="bundle_slug">Slug</label>
                  <input
                    id="bundle_slug"
                    className="input"
                    value={bundleForm.slug}
                    onChange={(event) => setBundleForm((current) => ({ ...current, slug: makeSlug(event.target.value) }))}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="label" htmlFor="bundle_description">Описание</label>
                <textarea
                  id="bundle_description"
                  className="textarea"
                  rows={5}
                  value={bundleForm.description}
                  onChange={(event) => setBundleForm((current) => ({ ...current, description: event.target.value }))}
                />
              </div>

              <div className="grid-2">
                <div className="form-group">
                  <label className="label" htmlFor="bundle_price">Цена</label>
                  <input
                    id="bundle_price"
                    className="input"
                    type="number"
                    min="0"
                    step="0.01"
                    value={bundleForm.price_amount}
                    onChange={(event) => setBundleForm((current) => ({ ...current, price_amount: event.target.value }))}
                  />
                </div>
                <div className="form-group">
                  <label className="label" htmlFor="bundle_currency">Валюта</label>
                  <input
                    id="bundle_currency"
                    className="input"
                    value={bundleForm.currency}
                    onChange={(event) => setBundleForm((current) => ({ ...current, currency: event.target.value.toUpperCase() }))}
                  />
                </div>
              </div>

              <button className="button" type="submit" disabled={saving}>
                {saving ? 'Сохраняем…' : selectedBundleId ? 'Обновить bundle' : 'Создать bundle'}
              </button>
            </form>

            <div className="trainer-composer card compact shadow-none surface-muted">
              <div className="row trainer-panel__header">
                <div>
                  <h4 className="title-sm" style={{ marginBottom: 4 }}>Bundle composition editor</h4>
                  <p className="muted">Добавляй в bundle уже подготовленные видео и программы. Порядок можно менять прямо в составе оффера.</p>
                </div>
                <button className="button ghost" type="button" onClick={() => { setSelectedBundleItemId(null); setBundleItemForm(initialBundleItemForm); }} disabled={!selectedBundleId}>
                  Новый элемент
                </button>
              </div>

              {!selectedBundleId ? (
                <div className="card compact warning">Сначала создай bundle, чтобы собрать его состав.</div>
              ) : (
                <form className="form" onSubmit={saveBundleItem}>
                  <div className="grid-3">
                    <div className="form-group">
                      <label className="label" htmlFor="bundle_item_type">Тип</label>
                      <select
                        id="bundle_item_type"
                        className="select"
                        value={bundleItemForm.item_type}
                        onChange={(event) => setBundleItemForm((current) => ({
                          ...current,
                          item_type: event.target.value === 'program' ? 'program' : 'video',
                        }))}
                      >
                        <option value="video">Видео</option>
                        <option value="program">Программа</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="label" htmlFor="bundle_target">Цель</label>
                      <select
                        id="bundle_target"
                        className="select"
                        value={bundleItemForm.target_id}
                        onChange={(event) => setBundleItemForm((current) => ({ ...current, target_id: event.target.value }))}
                      >
                        <option value="">Выбери сущность</option>
                        {bundleTargetOptions.map((target) => (
                          <option key={target.id} value={target.id}>
                            {target.title} · {statusLabel(target.status)}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="label" htmlFor="bundle_position">Позиция</label>
                      <input
                        id="bundle_position"
                        className="input"
                        type="number"
                        min="1"
                        value={bundleItemForm.position}
                        onChange={(event) => setBundleItemForm((current) => ({ ...current, position: event.target.value }))}
                      />
                    </div>
                  </div>

                  <div className="trainer-note-box compact">
                    <strong>Publish rule</strong>
                    <p>Bundle publish пройдёт только если целевые видео и программы уже опубликованы.</p>
                  </div>

                  <div className="inline trainer-card-actions">
                    <button className="button" type="submit" disabled={saving}>
                      {saving ? 'Сохраняем…' : selectedBundleItemId ? 'Обновить элемент' : 'Добавить элемент'}
                    </button>
                    <button className="button ghost danger" type="button" onClick={() => void deleteBundleItem()} disabled={!selectedBundleItemId || actionId === selectedBundleItemId}>
                      Удалить элемент
                    </button>
                    <button className="button ghost" type="button" onClick={() => void moveBundleItem(-1)} disabled={!selectedBundleItemId || !canMoveBundleItemUp || Boolean(actionId)}>
                      Выше
                    </button>
                    <button className="button ghost" type="button" onClick={() => void moveBundleItem(1)} disabled={!selectedBundleItemId || !canMoveBundleItemDown || Boolean(actionId)}>
                      Ниже
                    </button>
                  </div>
                </form>
              )}
            </div>
          </section>

          <section className="stack" style={{ gap: 16 }}>
            {bundles.length === 0 ? <div className="card"><p className="muted">Черновиков bundle пока нет.</p></div> : bundles.map(renderBundleCard)}

            {selectedBundleId ? (
              <div className="card trainer-panel">
                <div className="row trainer-panel__header">
                  <div>
                    <h3 className="title-md" style={{ marginBottom: 6 }}>Bundle composition</h3>
                    <p className="muted">Что увидит пользователь на storefront bundle page.</p>
                  </div>
                  <span className="badge secondary">{selectedBundle?.items?.length || 0}</span>
                </div>
                {(selectedBundle?.items || []).length ? (
                  <div className="stack" style={{ gap: 12 }}>
                    {sortedBundleItems.map((item) => (
                      <article key={item.id} className={`card compact shadow-none surface-muted trainer-subitem-card${selectedBundleItemId === item.id ? ' is-selected' : ''}`}>
                        <div className="inline" style={{ justifyContent: 'space-between', gap: 12 }}>
                          <div className="stack" style={{ gap: 4 }}>
                            <strong>{bundleTargetLabel(item)}</strong>
                            <span className="muted">{item.item_type === 'program' ? 'Программа' : 'Видео'}</span>
                          </div>
                          <span className="badge ghost">#{item.position || 0}</span>
                        </div>
                        <div className="trainer-draft-card__meta">
                          <span>source id: {item.target_id}</span>
                        </div>
                        <div className="inline trainer-card-actions trainer-reorder-controls">
                          <button className="button ghost" type="button" onClick={() => setSelectedBundleItemId(item.id)}>
                            Edit item
                          </button>
                          {selectedBundleItemId === item.id ? (
                            <>
                              <button className="button ghost" type="button" onClick={() => void moveBundleItem(-1)} disabled={!canMoveBundleItemUp || Boolean(actionId)}>Выше</button>
                              <button className="button ghost" type="button" onClick={() => void moveBundleItem(1)} disabled={!canMoveBundleItemDown || Boolean(actionId)}>Ниже</button>
                            </>
                          ) : null}
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <div className="empty-state compact">
                    <h3>Состав пока пустой</h3>
                    <p>Добавь хотя бы один элемент, чтобы bundle стал publish-ready.</p>
                  </div>
                )}
              </div>
            ) : null}
          </section>
        </div>
      ) : null}
    </div>
  );
}
