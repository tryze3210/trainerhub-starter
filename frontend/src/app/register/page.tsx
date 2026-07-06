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
    <div className="premium-landing premium-auth-page premium-register-page">
      <div className="premium-container premium-auth-layout">
        <section className="premium-auth-copy" aria-labelledby="register-title">
          <span className="premium-eyebrow">TRAINERHUB ONBOARDING</span>
          <h1 className="premium-hero-title" id="register-title">
            Создайте аккаунт в TrainerHub
          </h1>
          <p className="premium-hero-subtitle">
            Клиент получает кабинет для покупок и обучения. Тренер начинает onboarding, готовит профиль, продукты и
            будущую публикацию в marketplace.
          </p>
          <div className="premium-auth-proof" aria-label="Что можно сделать после регистрации">
            <span>Кабинет ученика</span>
            <span>Trainer onboarding</span>
            <span>Каталог продуктов</span>
            <span>Оплаты и доступы</span>
          </div>
        </section>

        <div className="premium-auth-card">
          <div className="premium-auth-card-header">
            <span className="premium-eyebrow">CREATE ACCOUNT</span>
            <h2>Регистрация</h2>
            <p>Выберите роль сейчас. Данные профиля можно будет уточнить после входа.</p>
          </div>

          <form className="premium-auth-form" onSubmit={onSubmit}>
            <label className="premium-auth-field" htmlFor="full_name">
              <span>Полное имя</span>
              <input
                id="full_name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                autoComplete="name"
                placeholder="Можно заполнить позже в onboarding"
              />
            </label>

            <div className="premium-auth-field-grid">
              <label className="premium-auth-field" htmlFor="email">
                <span>Email</span>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </label>

              <label className="premium-auth-field" htmlFor="role">
                <span>Роль</span>
                <select id="role" value={role} onChange={(e) => setRole(e.target.value as 'user' | 'trainer')}>
                  <option value="user">Покупатель / клиент</option>
                  <option value="trainer">Тренер</option>
                </select>
              </label>
            </div>

            <label className="premium-auth-field" htmlFor="password">
              <span>Пароль</span>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </label>

            {msg ? (
              <div className="premium-auth-message premium-auth-message-error">
                {msg}
              </div>
            ) : null}
            {success ? (
              <div className="premium-auth-message premium-auth-message-success">
                {success}
              </div>
            ) : null}

            <button className="premium-primary-button premium-auth-submit" type="submit" disabled={loading}>
              {loading ? 'Создаём аккаунт...' : role === 'trainer' ? 'Создать trainer-аккаунт' : 'Создать аккаунт'}
            </button>
          </form>

          <div className="premium-auth-footer">
            <span>Уже есть аккаунт?</span>
            <Link href="/login">Войти</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
