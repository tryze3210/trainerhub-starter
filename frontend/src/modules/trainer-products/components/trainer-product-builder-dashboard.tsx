'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';

import {
  trainerProductsApi,
  type ProductReadinessCheck,
  type TrainerProduct,
  type TrainerProductPayload,
} from '@/modules/trainer-products/api';
import { uploadApi } from '@/modules/upload/api';
import { TrainerProductAdvancedIdField } from '@/modules/trainer-products/components/trainer-product-advanced-id-field';
import { TrainerProductMediaPicker } from '@/modules/trainer-products/components/trainer-product-media-picker';
import { TrainerSelectedMediaList } from '@/modules/trainer-products/components/trainer-selected-media-list';
import type { TrainerProductMediaVideo } from '@/modules/trainer-products/types/product-media';
import {
  TrainerEmptyState,
  TrainerErrorState,
  TrainerLoadingState,
  TrainerStatusBadge,
} from '@/modules/trainer-cabinet/components';
import { formatTrainerMoney, trainerProductTypeLabel, trainerStatusTone } from '@/modules/trainer-cabinet/components/trainer-format';

type ProductBuilderMetric = {
  label: string;
  value: string | number;
  hint?: string;
};

type ProductAccessType = 'one_time' | 'subscription';

type ProductBuilderPreview = {
  title: string;
  description: string;
  price: string;
  typeLabel: string;
  accessLabel: string;
  href?: string;
};

const emptyForm: TrainerProductPayload = {
  title: '',
  slug: '',
  description: '',
  product_type: 'video',
  access_type: 'one_time',
  currency: 'RUB',
  price_amount: '0.00',
  item_video_ids: [],
};

function parseVideoIds(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function accessLabel(value?: string): string {
  if (value === 'subscription') return 'Подписка';
  return 'Разовая покупка';
}

function productStatusLabel(value?: string): string {
  const status = (value || '').toLowerCase();
  if (status === 'draft') return 'Черновик';
  if (status === 'published') return 'Опубликован';
  if (status === 'archived') return 'В архиве';
  if (status === 'pending_review' || status === 'review' || status === 'under_review') return 'На проверке';
  if (status === 'submitted') return 'Отправлен на проверку';
  if (status === 'approved') return 'Одобрен';
  if (status === 'rejected') return 'Отклонён';
  return 'Требуется проверка';
}

function readinessLabel(value?: string): string {
  if (value === 'ready') return 'Готов к публикации';
  if (value === 'pass' || value === 'passed') return 'Готово';
  if (value === 'failed') return 'Требует исправления';
  if (value === 'warning') return 'Проверьте';
  if (value === 'pending') return 'В ожидании';
  if (value === 'blocker' || value === 'blocked') return 'Публикация недоступна';
  return 'Требуется проверка';
}

function checkTitle(check: ProductReadinessCheck): string {
  const known: Record<string, string> = {
    title_required: 'Название заполнено',
    description_required: 'Описание заполнено',
    price_required: 'Цена настроена',
    items_required: 'Материалы добавлены',
    access_required: 'Доступ настроен',
    title: 'Название продукта',
    description: 'Описание продукта',
    price: 'Цена',
    items: 'Материалы',
    access: 'Настройки доступа',
  };
  return known[check.code] || check.title || 'Проверка продукта';
}

function checkMessage(check: ProductReadinessCheck): string {
  const known: Record<string, string> = {
    title_required: 'Добавьте понятное название продукта.',
    description_required: 'Заполните описание для каталога и страницы покупки.',
    price_required: 'Проверьте цену и валюту продукта.',
    items_required: 'Добавьте видео или материалы из библиотеки.',
    access_required: 'Проверьте формат доступа.',
  };
  return known[check.code] || 'Требуется уточнение настроек продукта.';
}

function previewHref(product: TrainerProduct | null, slug?: string, type?: string): string | undefined {
  const publicSlug = slug || product?.slug;
  const productType = type || product?.product_type;
  if (!publicSlug) return undefined;
  if (productType === 'video') return `/catalog/videos/${publicSlug}`;
  if (productType === 'bundle') return `/catalog/bundles/${publicSlug}`;
  if (productType === 'program') return `/catalog/programs/${publicSlug}`;
  return undefined;
}

function buildPreview(form: TrainerProductPayload, selectedProduct: TrainerProduct | null): ProductBuilderPreview {
  const typeLabel = trainerProductTypeLabel(form.product_type || selectedProduct?.product_type);
  return {
    title: form.title || 'Название продукта',
    description: form.description || 'Короткое описание появится в каталоге и на странице покупки.',
    price: formatTrainerMoney(form.price_amount || selectedProduct?.price_amount || '0', form.currency || selectedProduct?.currency || 'RUB'),
    typeLabel,
    accessLabel: accessLabel(form.access_type || selectedProduct?.access_type),
    href: previewHref(selectedProduct, form.slug, form.product_type),
  };
}

function productMaterialCount(product: TrainerProduct): number {
  return product.items_count ?? product.items?.length ?? 0;
}

export function TrainerProductBuilderDashboard() {
  const searchParams = useSearchParams();
  const [products, setProducts] = useState<TrainerProduct[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [form, setForm] = useState<TrainerProductPayload>(emptyForm);
  const [videoIdsText, setVideoIdsText] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [mediaVideos, setMediaVideos] = useState<TrainerProductMediaVideo[]>([]);
  const [mediaVideosLoading, setMediaVideosLoading] = useState(false);
  const [mediaVideosError, setMediaVideosError] = useState<string | null>(null);

  const selectedProduct = useMemo(
    () => products.find((product) => product.id === selectedId) || null,
    [products, selectedId]
  );

  async function reload() {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await trainerProductsApi.list();
      setProducts(payload);
      if (!selectedId && payload[0]) setSelectedId(payload[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить продукты');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadMediaVideos = useCallback(async () => {
    setMediaVideosLoading(true);
    setMediaVideosError(null);
    try {
      const response = await uploadApi.listMyVideos();
      const videos = Array.isArray(response) ? response : [];
      setMediaVideos(videos);
    } catch {
      setMediaVideosError('Не удалось загрузить библиотеку видео.');
    } finally {
      setMediaVideosLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMediaVideos();
  }, [loadMediaVideos]);

  useEffect(() => {
    if (!selectedProduct) return;
    const itemIds = selectedProduct.items?.map((item) => item.video_id || item.video).filter(Boolean) || [];
    setForm({
      title: selectedProduct.title,
      slug: selectedProduct.slug,
      description: selectedProduct.description || '',
      product_type: selectedProduct.product_type === 'bundle' ? 'bundle' : 'video',
      access_type: selectedProduct.access_type === 'subscription' ? 'subscription' : 'one_time',
      currency: selectedProduct.currency || 'RUB',
      price_amount: selectedProduct.price_amount || '0.00',
      item_video_ids: itemIds,
    });
    setVideoIdsText(itemIds.join('\n'));
  }, [selectedProduct]);

  function newProduct() {
    setSelectedId(null);
    setForm(emptyForm);
    setVideoIdsText('');
    setError(null);
    setMessage(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    setMessage(null);
    const payload = { ...form, item_video_ids: parseVideoIds(videoIdsText) };

    try {
      const product = selectedId
        ? await trainerProductsApi.update(selectedId, payload)
        : await trainerProductsApi.create(payload);
      setSelectedId(product.id);
      setMessage(selectedId ? 'Черновик сохранён' : 'Черновик создан');
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить продукт');
    } finally {
      setIsSaving(false);
    }
  }

  async function runAction(action: 'publish' | 'archive' | 'delete') {
    if (!selectedId) return;
    setIsSaving(true);
    setError(null);
    setMessage(null);
    try {
      if (action === 'publish') {
        await trainerProductsApi.publish(selectedId);
        setMessage('Продукт опубликован');
      } else if (action === 'archive') {
        await trainerProductsApi.archive(selectedId);
        setMessage('Продукт отправлен в архив');
      } else {
        await trainerProductsApi.remove(selectedId);
        setSelectedId(null);
        setMessage('Продукт удалён');
      }
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Действие не выполнено');
    } finally {
      setIsSaving(false);
    }
  }

  const metrics: ProductBuilderMetric[] = [
    { label: 'Всего продуктов', value: products.length },
    { label: 'Опубликовано', value: products.filter((item) => item.status === 'published').length },
    { label: 'Черновики', value: products.filter((item) => item.status === 'draft').length },
    { label: 'На проверке', value: products.filter((item) => ['pending_review', 'review', 'submitted', 'under_review'].includes(item.status || '')).length },
    { label: 'Наборы', value: products.filter((item) => item.product_type === 'bundle').length },
    { label: 'С подпиской', value: products.filter((item) => item.access_type === 'subscription').length },
  ];
  const preview = buildPreview(form, selectedProduct);
  const readiness = selectedProduct?.readiness || null;
  const selectedVideoIds = useMemo(() => parseVideoIds(videoIdsText), [videoIdsText]);
  const isAttachVideoIntent = searchParams.get('intent') === 'attach-video';

  function updateSelectedVideoIds(videoIds: string[]) {
    setVideoIdsText(Array.from(new Set(videoIds)).join('\n'));
  }

  return (
    <section className="profile-workbench trainer-product-workbench">
      <header className="trainer-workbench-local-header">
        <div>
          <p className="premium-eyebrow">ПРОДУКТЫ ТРЕНЕРА</p>
          <h2>Продукты</h2>
          <p>Создавайте платные видео, наборы и программы, настраивайте цену, доступ и публикацию для каталога TrainerHub.</p>
        </div>
        <div className="trainer-workbench-local-header-actions">
          <button className="premium-primary-button" onClick={newProduct} type="button">Новый продукт</button>
          <Link className="premium-secondary-button" href="/trainer/videos?tab=videos&intent=upload">Загрузить видео</Link>
          <Link className="premium-secondary-button" href="/catalog">Открыть каталог</Link>
        </div>
      </header>

      <section className="profile-workbench-metrics" aria-label="Метрики продуктов">
        {metrics.map((metric) => (
          <article className="profile-workbench-metric" key={metric.label}>
            <span>{metric.label.replace('Всего продуктов', 'Всего')}</span>
            <strong>{metric.value}</strong>
          </article>
        ))}
      </section>

      {isLoading ? <TrainerLoadingState title="Загружаем продукты" /> : null}
      {error ? <TrainerErrorState message={error} onRetry={() => void reload()} /> : null}
      {message ? <div className="profile-workbench-panel"><TrainerStatusBadge tone="success">{message}</TrainerStatusBadge></div> : null}

      <section className="profile-workbench-rail-section">
        <header className="profile-workbench-section-header">
          <h3>Ваши продукты</h3>
          <p>Выберите продукт для редактирования или создайте новый.</p>
        </header>
        <div className="profile-workbench-rail trainer-product-rail" aria-label="Список продуктов">
          {!isLoading && products.length === 0 ? (
            <div className="trainer-workbench-empty-rail-card"><TrainerEmptyState title="Продуктов пока нет" description="Создайте первый платный продукт для каталога." /></div>
          ) : null}
          {products.map((product) => (
            <button
              className={selectedId === product.id ? 'profile-workbench-rail-card trainer-product-rail-card trainer-product-rail-card-active profile-workbench-rail-card-active' : 'profile-workbench-rail-card trainer-product-rail-card'}
              key={product.id}
              onClick={() => setSelectedId(product.id)}
              type="button"
            >
              <TrainerStatusBadge tone={trainerStatusTone(product.status)}>{productStatusLabel(product.status)}</TrainerStatusBadge>
              <strong>{product.title}</strong>
              <span>{trainerProductTypeLabel(product.product_type)}</span>
              <span>{formatTrainerMoney(product.price_amount, product.currency)}</span>
              <small>{productMaterialCount(product)} материалов</small>
            </button>
          ))}
        </div>
      </section>

      <form className="profile-workbench-editor-panel trainer-product-editor-panel" onSubmit={submit}>
        <header className="profile-workbench-section-header">
          <h3>{selectedProduct ? 'Редактирование продукта' : 'Новый продукт'}</h3>
          <p>Подготовьте описание, цену, формат доступа и материалы перед публикацией.</p>
        </header>

        <section className="trainer-editor-section">
          <h3>Основное</h3>
          <div className="trainer-editor-field-grid">
            <label className="trainer-editor-field">
              <span>Название</span>
              <input className="trainer-content-input" value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} required />
            </label>
            <label className="trainer-editor-field">
              <span>Публичный адрес</span>
              <input className="trainer-content-input" value={form.slug || ''} onChange={(event) => setForm((current) => ({ ...current, slug: event.target.value }))} placeholder="Например: power-start" />
              <small>Публичный адрес используется в ссылке на страницу продукта.</small>
            </label>
          </div>
          <label className="trainer-editor-field">
            <span>Описание</span>
            <textarea className="trainer-content-textarea" value={form.description || ''} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} rows={4} />
            <small>Описание видно ученикам в каталоге и на странице покупки.</small>
          </label>
        </section>

        <section className="trainer-editor-section">
          <h3>Цена и доступ</h3>
          <div className="trainer-editor-field-grid">
            <label className="trainer-editor-field">
              <span>Тип продукта</span>
              <select className="trainer-content-select" value={form.product_type} onChange={(event) => setForm((current) => ({ ...current, product_type: event.target.value as 'video' | 'bundle' }))}>
                <option value="video">Видео</option>
                <option value="bundle">Набор</option>
              </select>
            </label>
            <label className="trainer-editor-field">
              <span>Формат доступа</span>
              <select className="trainer-content-select" value={form.access_type} onChange={(event) => setForm((current) => ({ ...current, access_type: event.target.value as ProductAccessType }))}>
                <option value="one_time">Разовая покупка</option>
                <option value="subscription">Подписка</option>
              </select>
            </label>
            <label className="trainer-editor-field">
              <span>Цена</span>
              <input className="trainer-content-input" value={form.price_amount || '0.00'} onChange={(event) => setForm((current) => ({ ...current, price_amount: event.target.value }))} inputMode="decimal" />
            </label>
            <label className="trainer-editor-field">
              <span>Валюта</span>
              <select className="trainer-content-select" value={form.currency || 'RUB'} onChange={(event) => setForm((current) => ({ ...current, currency: event.target.value }))}>
                <option value="RUB">RUB</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </label>
          </div>
        </section>

        <section className={['trainer-editor-section', 'trainer-product-materials-panel', isAttachVideoIntent ? 'trainer-product-materials-panel-highlighted' : ''].filter(Boolean).join(' ')}>
          <div className="trainer-editor-section-header">
            <div>
              <h3>Материалы продукта</h3>
              <p>Выберите видео из библиотеки тренера. Если нужного видео ещё нет, загрузите его в разделе “Видео и материалы”.</p>
            </div>
            <Link className="premium-secondary-button" href="/trainer/videos?tab=videos&intent=upload">Загрузить видео</Link>
          </div>

          {isAttachVideoIntent ? <div className="trainer-product-materials-hint">Выберите загруженное видео и добавьте его в продукт.</div> : null}

          <TrainerProductMediaPicker
            videos={mediaVideos}
            selectedVideoIds={selectedVideoIds}
            loading={mediaVideosLoading}
            error={mediaVideosError}
            highlighted={isAttachVideoIntent}
            onChange={updateSelectedVideoIds}
            onRetry={loadMediaVideos}
          />
          <TrainerSelectedMediaList
            videos={mediaVideos}
            selectedVideoIds={selectedVideoIds}
            loading={mediaVideosLoading}
            onRemove={(videoId) => updateSelectedVideoIds(selectedVideoIds.filter((id) => id !== videoId))}
          />
          <TrainerProductAdvancedIdField value={videoIdsText} onChange={setVideoIdsText} />
        </section>

        <section className="trainer-editor-section">
          <h3>Публикация</h3>
          <div className="profile-workbench-actions trainer-product-actions">
            <button className="premium-primary-button" disabled={isSaving} type="submit">{selectedProduct ? 'Сохранить черновик' : 'Создать черновик'}</button>
            {selectedProduct ? (
              <>
                <button className="premium-secondary-button" disabled={isSaving} onClick={() => void runAction('publish')} type="button">Опубликовать</button>
                <button className="premium-secondary-button" disabled={isSaving} onClick={() => void runAction('archive')} type="button">Отправить в архив</button>
                <button className="trainer-product-danger-action" disabled={isSaving || selectedProduct.status === 'published'} onClick={() => void runAction('delete')} type="button">Удалить</button>
              </>
            ) : null}
          </div>
        </section>
      </form>

      <section className="profile-workbench-support-panels">
        <article className="profile-workbench-panel">
          <h3>Предпросмотр в каталоге</h3>
          <TrainerStatusBadge>{preview.typeLabel}</TrainerStatusBadge>
          <strong>{preview.title}</strong>
          <p>{preview.description}</p>
          <span>{preview.price} · {preview.accessLabel}</span>
          {preview.href ? (
            <Link className="premium-secondary-button" href={preview.href}>Предпросмотр</Link>
          ) : (
            <span>Предпросмотр появится после сохранения публичного адреса.</span>
          )}
        </article>

        <article className="profile-workbench-panel">
          <h3>Готовность к публикации</h3>
          <p>Перед публикацией TrainerHub проверяет, что у продукта есть название, цена, описание, материалы и корректные настройки доступа.</p>
          <div className="trainer-product-readiness-list">
            {(readiness?.checks || []).map((check) => (
              <div className="trainer-product-readiness-item" key={check.code}>
                <TrainerStatusBadge tone={trainerStatusTone(check.status)}>{readinessLabel(check.status)}</TrainerStatusBadge>
                <strong>{checkTitle(check)}</strong>
                <span>{checkMessage(check)}</span>
              </div>
            ))}
            {!readiness ? <TrainerEmptyState title="Проверка появится после сохранения" description="Сохраните черновик, чтобы увидеть готовность к публикации." /> : null}
          </div>
        </article>
      </section>
    </section>
  );
}
