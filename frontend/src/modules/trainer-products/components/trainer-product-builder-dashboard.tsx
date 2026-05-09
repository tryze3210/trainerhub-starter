'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';

import { trainerProductsApi, type TrainerProduct, type TrainerProductPayload } from '@/modules/trainer-products/api';

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

function statusBadge(status: string) {
  if (status === 'published') return 'badge badge-success';
  if (status === 'archived') return 'badge badge-muted';
  return 'badge';
}

export function TrainerProductBuilderDashboard() {
  const [products, setProducts] = useState<TrainerProduct[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [form, setForm] = useState<TrainerProductPayload>(emptyForm);
  const [videoIdsText, setVideoIdsText] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const selectedProduct = useMemo(
    () => products.find((product) => product.id === selectedId) || null,
    [products, selectedId],
  );

  async function reload() {
    setIsLoading(true);
    setError(null);
    try {
      const payload = await trainerProductsApi.list();
      setProducts(payload);
      if (!selectedId && payload[0]) {
        setSelectedId(payload[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить продукты');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedProduct) return;
    setForm({
      title: selectedProduct.title,
      slug: selectedProduct.slug,
      description: selectedProduct.description || '',
      product_type: selectedProduct.product_type === 'bundle' ? 'bundle' : 'video',
      access_type: selectedProduct.access_type === 'subscription' ? 'subscription' : 'one_time',
      currency: selectedProduct.currency || 'RUB',
      price_amount: selectedProduct.price_amount || '0.00',
      item_video_ids: selectedProduct.items?.map((item) => item.video_id || item.video).filter(Boolean) || [],
    });
    setVideoIdsText(selectedProduct.items?.map((item) => item.video_id || item.video).filter(Boolean).join('\n') || '');
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
      setMessage(selectedId ? 'Продукт обновлён' : 'Продукт создан');
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

  return (
    <div className="grid grid-2 gap-4">
      <section className="card">
        <div className="card-header">
          <div>
            <h2>Products</h2>
            <p>Draft, publish and archive trainer-owned video products and bundles.</p>
          </div>
          <button className="btn btn-secondary" onClick={newProduct} type="button">
            New product
          </button>
        </div>

        {isLoading ? <p>Загрузка...</p> : null}
        {!isLoading && products.length === 0 ? <p>Продуктов пока нет.</p> : null}

        <div className="stack gap-3">
          {products.map((product) => (
            <button
              className={`card text-left ${selectedId === product.id ? 'is-active' : ''}`}
              key={product.id}
              onClick={() => setSelectedId(product.id)}
              type="button"
            >
              <div className="row row-between">
                <strong>{product.title}</strong>
                <span className={statusBadge(product.status)}>{product.status}</span>
              </div>
              <p>{product.product_type} · {product.price_amount} {product.currency}</p>
              <p>Readiness: {product.readiness?.status || 'unknown'} · items: {product.items_count || 0}</p>
            </button>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <div>
            <h2>{selectedProduct ? 'Edit product' : 'Create product'}</h2>
            <p>Publishing is blocked until readiness checks pass.</p>
          </div>
        </div>

        {error ? <div className="alert alert-error">{error}</div> : null}
        {message ? <div className="alert alert-success">{message}</div> : null}

        <form className="form stack gap-3" onSubmit={submit}>
          <label>
            Title
            <input
              value={form.title}
              onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
              required
            />
          </label>
          <label>
            Slug
            <input
              value={form.slug || ''}
              onChange={(event) => setForm((current) => ({ ...current, slug: event.target.value }))}
              placeholder="generated from title when empty"
            />
          </label>
          <label>
            Description
            <textarea
              value={form.description || ''}
              onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              rows={4}
            />
          </label>

          <div className="grid grid-2 gap-3">
            <label>
              Product type
              <select
                value={form.product_type}
                onChange={(event) => setForm((current) => ({ ...current, product_type: event.target.value as 'video' | 'bundle' }))}
              >
                <option value="video">Single video</option>
                <option value="bundle">Video bundle</option>
              </select>
            </label>
            <label>
              Access type
              <select
                value={form.access_type}
                onChange={(event) => setForm((current) => ({ ...current, access_type: event.target.value as 'one_time' | 'subscription' }))}
              >
                <option value="one_time">One-time purchase</option>
                <option value="subscription">Subscription access</option>
              </select>
            </label>
          </div>

          <div className="grid grid-2 gap-3">
            <label>
              Price
              <input
                value={form.price_amount || '0.00'}
                onChange={(event) => setForm((current) => ({ ...current, price_amount: event.target.value }))}
                inputMode="decimal"
              />
            </label>
            <label>
              Currency
              <select
                value={form.currency || 'RUB'}
                onChange={(event) => setForm((current) => ({ ...current, currency: event.target.value }))}
              >
                <option value="RUB">RUB</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </label>
          </div>

          <label>
            Video ids
            <textarea
              value={videoIdsText}
              onChange={(event) => setVideoIdsText(event.target.value)}
              placeholder="One video UUID per line, or comma-separated"
              rows={5}
            />
          </label>

          <div className="row gap-2">
            <button className="btn" disabled={isSaving} type="submit">
              {selectedProduct ? 'Save product' : 'Create draft'}
            </button>
            {selectedProduct ? (
              <>
                <button className="btn btn-secondary" disabled={isSaving} onClick={() => runAction('publish')} type="button">
                  Publish
                </button>
                <button className="btn btn-secondary" disabled={isSaving} onClick={() => runAction('archive')} type="button">
                  Archive
                </button>
                <button className="btn btn-danger" disabled={isSaving || selectedProduct.status === 'published'} onClick={() => runAction('delete')} type="button">
                  Delete
                </button>
              </>
            ) : null}
          </div>
        </form>

        {selectedProduct?.readiness ? (
          <div className="card mt-4">
            <h3>Readiness checks</h3>
            <p>Status: <strong>{selectedProduct.readiness.status}</strong></p>
            <ul>
              {selectedProduct.readiness.checks.map((check) => (
                <li key={check.code}>
                  <strong>{check.title}</strong>: {check.status} — {check.message}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>
    </div>
  );
}
