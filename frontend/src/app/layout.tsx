import type { Metadata } from 'next';
import Link from 'next/link';
import { AuthProvider } from '@/components/auth-provider';
import { SessionNav } from '@/components/session-nav';
import './globals.css';

export const metadata: Metadata = {
  title: 'TrainerHub',
  description: 'Платформа для онлайн-тренировок, программ и подписок',
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
          <header className="site-header">
            <div className="container">
              <div className="site-header__inner">
                <Link href="/" className="brand" aria-label="TrainerHub home">
                  <span className="brand__mark">T</span>
                  <span>TrainerHub</span>
                </Link>
                <SessionNav />
              </div>
            </div>
          </header>

          <main className="page">
            <div className="container">{children}</div>
          </main>

          <footer className="site-footer">
            <div className="container">
              <div className="site-footer__inner">
                <div className="stack" style={{ gap: 6 }}>
                  <strong>TrainerHub</strong>
                  <span>Платформа для тренеров, онлайн-тренировок, программ и подписок.</span>
                </div>

                <div className="inline">
                  <Link href="/catalog">Каталог</Link>
                  <Link href="/learning">Обучение</Link>
                  <Link href="/trainers">Тренеры</Link>
                  <Link href="/subscriptions">Подписки</Link>
                </div>
              </div>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
