'use client';

import { useEffect, useState } from 'react';

import { useCountUp } from '@/design-system';

const purchases = [
  'Анна купила программу «Сила и мобильность»',
  'Илья продлил подписку на 30 дней',
  'Мария записалась на персональную сессию',
];

export function HeroBusinessConsole() {
  const [ready, setReady] = useState(false);
  const revenue = useCountUp({
    from: 0,
    to: 428000,
    durationMs: 1400,
    formatter: (value) => `${Math.round(value / 1000)} тыс ₽`,
  });
  const students = useCountUp({ from: 0, to: 184, durationMs: 1100 });

  useEffect(() => {
    const timer = window.setTimeout(() => setReady(true), 240);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <aside className="premium-console premium-console-glow" aria-label="Превью рабочего пространства TrainerHub">
      <div className="premium-console__bar">
        <span>TrainerHub Pro</span>
        <strong>Live workspace</strong>
      </div>

      <div className="premium-console__metrics">
        <article className="premium-console-card">
          <small>Выручка за месяц</small>
          <strong className="premium-count">{revenue}</strong>
          <span>Продажи программ и подписок</span>
        </article>
        <article className="premium-console-card">
          <small>Активные ученики</small>
          <strong className="premium-count">{students}</strong>
          <span>С доступом к материалам</span>
        </article>
      </div>

      <div className="premium-console__grid">
        <article className="premium-console-card premium-console-card--shimmer">
          <small>Сегодняшние занятия</small>
          <strong>6 сессий</strong>
          <span>2 группы · 4 персональных записи</span>
        </article>
        <article className="premium-console-card">
          <small>Продажи программ</small>
          <strong>31 покупка</strong>
          <span>Основной спрос: силовой блок</span>
        </article>
      </div>

      <article className="premium-console-card">
        <div className="premium-console-card__row">
          <div>
            <small>Запуск программы</small>
            <strong>Сила и мобильность</strong>
          </div>
          <span>{ready ? '82%' : '0%'}</span>
        </div>
        <div className="premium-progress">
          <span className="premium-progress-fill" data-ready={ready ? 'true' : 'false'} />
        </div>
      </article>

      <div className="premium-console__rows" aria-label="Последние покупки">
        {purchases.map((purchase, index) => (
          <div className={`premium-console-row premium-console-row-enter premium-console-row-enter--${index + 1}`} key={purchase}>
            <span />
            <p>{purchase}</p>
          </div>
        ))}
      </div>
    </aside>
  );
}
