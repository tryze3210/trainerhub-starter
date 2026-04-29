'use client';
import { Suspense } from 'react';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import { authApi } from '@/lib/api';
import { persistTokens } from '@/lib/auth';

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const nextPathFromQuery = searchParams.get('next') || '';
  const { isAuthenticated, refreshSession } = useAuthSession();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      router.replace(nextPathFromQuery || '/cabinet');
    }
  }, [isAuthenticated, nextPathFromQuery, router]);

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      setLoading(true);
      setMsg('');
      const payload = await authApi.login({ email, password });
      persistTokens(payload.access_token, payload.refresh_token);
      await refreshSession();
      const nextPath = nextPathFromQuery || (payload.user.active_role === 'trainer' ? '/trainer/dashboard' : '/cabinet');
      router.push(nextPath);
      router.refresh();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось выполнить вход');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="stack" style={{ gap: 10, marginBottom: 22 }}>
          <span className="badge secondary">Вход</span>
          <h1 className="title-lg">Войти в TrainerHub</h1>
          <p>Trainer-аккаунт после входа уходит в dashboard shell. Клиент остаётся в обычном кабинете.</p>
        </div>

        <form className="form" onSubmit={onSubmit}>
          <div className="form-group">
            <label className="label" htmlFor="email">Email</label>
            <input id="email" className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
          </div>

          <div className="form-group">
            <label className="label" htmlFor="password">Пароль</label>
            <input id="password" className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
          </div>

          {msg ? <div className="card error compact">{msg}</div> : null}

          <button className="button lg w-full" type="submit" disabled={loading}>
            {loading ? 'Входим...' : 'Войти'}
          </button>
        </form>

        <div className="auth-footer">
          <span className="muted">Нет аккаунта?</span>
          <Link href="/register">Создать</Link>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Загрузка...</div>}>
      <LoginPageContent />
    </Suspense>
  );
}

