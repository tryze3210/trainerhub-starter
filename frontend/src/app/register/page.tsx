'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useAuthSession } from '@/components/auth-provider';
import { authApi } from '@/lib/api';
import { persistTokens } from '@/lib/auth';

export default function RegisterPage() {
  const router = useRouter();
  const { isAuthenticated, refreshSession } = useAuthSession();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<'user' | 'trainer'>('user');
  const [msg, setMsg] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/cabinet');
    }
  }, [isAuthenticated, router]);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setMsg('');
    setSuccess('');

    try {
      setLoading(true);
      const payload = await authApi.register({
        full_name: fullName,
        email,
        password,
        role,
      });
      persistTokens(payload.access_token, payload.refresh_token);
      await refreshSession();
      setSuccess('Аккаунт успешно создан');
      const nextPath = payload.user.active_role === 'trainer' ? '/trainer/onboarding' : '/cabinet';
      router.push(nextPath);
      router.refresh();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Не удалось зарегистрироваться');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="stack" style={{ gap: 10, marginBottom: 22 }}>
          <span className="badge">Регистрация</span>
          <h1 className="title-lg">Создай аккаунт в TrainerHub</h1>
          <p>Для клиента это быстрый вход в кабинет. Для тренера — старт onboarding, заявки и будущей публикации.</p>
        </div>

        <form className="form" onSubmit={onSubmit}>
          <div className="form-group">
            <label className="label" htmlFor="full_name">Полное имя</label>
            <input
              id="full_name"
              className="input"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              autoComplete="name"
              placeholder="Можно заполнить позже в onboarding"
            />
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="label" htmlFor="email">Email</label>
              <input id="email" className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
            </div>

            <div className="form-group">
              <label className="label" htmlFor="role">Роль</label>
              <select id="role" className="select" value={role} onChange={(e) => setRole(e.target.value as 'user' | 'trainer')}>
                <option value="user">Покупатель / клиент</option>
                <option value="trainer">Тренер</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="label" htmlFor="password">Пароль</label>
            <input id="password" className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" required />
          </div>

          {msg ? <div className="card error compact">{msg}</div> : null}
          {success ? <div className="card success compact">{success}</div> : null}

          <button className="button lg w-full" type="submit" disabled={loading}>
            {loading ? 'Создаём аккаунт...' : role === 'trainer' ? 'Создать trainer-аккаунт' : 'Создать аккаунт'}
          </button>
        </form>

        <div className="auth-footer">
          <span className="muted">Уже есть аккаунт?</span>
          <Link href="/login">Войти</Link>
        </div>
      </div>
    </div>
  );
}
