import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="stack" style={{ gap: 32 }}>
      <section className="hero card dark">
        <div className="stack" style={{ gap: 18 }}>
          <span className="badge secondary">TrainerHub</span>
          <h1 className="title-xl">Коммерческая платформа для тренеров, видео, программ и подписок</h1>
          <p className="lead" style={{ color: 'rgba(248,250,252,0.82)' }}>
            В этой версии фронта добавлены trainer onboarding, trainer dashboard shell и модульное разделение клиентского кода для trainers, checkout, payments и upload.
          </p>
          <div className="inline">
            <Link href="/register" className="button lg">Создать аккаунт</Link>
            <Link href="/catalog" className="button ghost lg">Открыть каталог</Link>
            <Link href="/trainer/dashboard" className="button secondary lg">Trainer dashboard</Link>
          </div>
        </div>
      </section>

      <section className="grid-3">
        <div className="card">
          <span className="badge">Onboarding</span>
          <h3 className="title-md" style={{ marginTop: 14 }}>Регистрация тренера</h3>
          <p>Регистрация теперь поддерживает роль trainer и ведёт пользователя в отдельный onboarding flow.</p>
        </div>

        <div className="card">
          <span className="badge secondary">Dashboard shell</span>
          <h3 className="title-md" style={{ marginTop: 14 }}>Отдельная зона тренера</h3>
          <p>Trainer dashboard, onboarding и upload flow вынесены в собственный навигационный shell.</p>
        </div>

        <div className="card">
          <span className="badge success">Module split</span>
          <h3 className="title-md" style={{ marginTop: 14 }}>Нормальный клиентский API-слой</h3>
          <p>Транспорт и API разделены по модулям: trainers, checkout, payments, upload, auth, trainer onboarding.</p>
        </div>
      </section>

      <section className="grid-2">
        <div className="card hero">
          <div className="stack" style={{ gap: 14 }}>
            <span className="badge">Для тренеров</span>
            <h2 className="title-lg">Путь тренера теперь собран</h2>
            <ul className="list">
              <li className="list-item">Регистрация с ролью trainer</li>
              <li className="list-item">Создание trainer profile</li>
              <li className="list-item">Dashboard shell и CMS summary</li>
              <li className="list-item">Upload flow для видео</li>
            </ul>
          </div>
        </div>

        <div className="card">
          <div className="stack" style={{ gap: 16 }}>
            <span className="badge warning">Быстрый старт</span>
            <h2 className="title-lg">Проверка сценария</h2>
            <p>Создай trainer-аккаунт, заверши onboarding, загрузи первое видео и проверь dashboard / payments / orders.</p>
            <div className="inline">
              <Link href="/register" className="button">Регистрация</Link>
              <Link href="/trainer/onboarding" className="button secondary">Onboarding</Link>
              <Link href="/trainer/videos" className="button ghost">Upload flow</Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
