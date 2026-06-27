import type { Metadata } from 'next';
import Link from 'next/link';
import { AuthProvider } from '@/components/auth-provider';
import { SessionNav } from '@/components/session-nav';
import './globals.css';

export const metadata: Metadata = {
  title: 'TrainerHub — платформа для тренеров, программ и онлайн-продуктов',
  description: 'Премиальная платформа для тренеров: программы, видеоуроки, подписки, CRM, расписание, оплаты и аналитика.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body>
        <AuthProvider>
          <div className="app-shell">
            <header className="premium-site-header">
              <div className="premium-site-header__inner">
                <Link href="/" className="premium-brand" aria-label="TrainerHub">
                  <span className="premium-brand__mark">T</span>
                  <span className="premium-brand__text">TrainerHub</span>
                </Link>
                <SessionNav />
              </div>
            </header>

            <main className="premium-main">{children}</main>

            <footer className="premium-site-footer">
              <div className="premium-site-footer__inner">
                <div className="premium-site-footer__brand">
                  <Link href="/" className="premium-brand" aria-label="TrainerHub">
                    <span className="premium-brand__mark">T</span>
                    <span className="premium-brand__text">TrainerHub</span>
                  </Link>
                  <p>Платформа для тренеров, программ, видеоуроков, подписок и клиентского сопровождения.</p>
                </div>

                <div className="premium-site-footer__grid">
                  <div className="premium-site-footer__column">
                    <span className="premium-site-footer__title">Продукт</span>
                    <div className="premium-site-footer__links">
                      <Link href="/catalog" className="premium-footer-link">Каталог</Link>
                      <Link href="/trainers" className="premium-footer-link">Тренеры</Link>
                      <Link href="/register" className="premium-footer-link">Стать тренером</Link>
                    </div>
                  </div>
                  <div className="premium-site-footer__column">
                    <span className="premium-site-footer__title">Для пользователей</span>
                    <div className="premium-site-footer__links">
                      <Link href="/login" className="premium-footer-link">Войти</Link>
                      <Link href="/register" className="premium-footer-link">Регистрация</Link>
                      <Link href="/learning" className="premium-footer-link">Моё обучение</Link>
                    </div>
                  </div>
                </div>

                <div className="premium-site-footer__bottom">
                  © 2026 TrainerHub. Платформа для цифровых фитнес-продуктов.
                </div>
              </div>
            </footer>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
