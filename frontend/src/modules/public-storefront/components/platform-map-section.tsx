'use client';

import { useEffect, useState } from 'react';

import { AnimatedSection } from '@/design-system';

type PlatformModule = {
  title: string;
  description: string;
};

const modules: PlatformModule[] = [
  { title: 'Marketplace', description: 'Каталог программ и тренеров' },
  { title: 'Programs', description: 'Продукты, уроки и материалы' },
  { title: 'Video learning', description: 'Видеоуроки и защищённый доступ' },
  { title: 'Subscriptions', description: 'Подписки и статусы доступа' },
  { title: 'CRM', description: 'Клиенты, заметки и история' },
  { title: 'Booking', description: 'Расписание, места и записи' },
  { title: 'Payments', description: 'Оплаты, возвраты и статусы' },
  { title: 'Payouts', description: 'Балансы, выплаты и финансы' },
];

export function PlatformMapSection() {
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) {
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      setActiveIndex((current) => (current + 1) % modules.length);
    }, 1600);

    return () => window.clearInterval(intervalId);
  }, []);

  return (
    <AnimatedSection className="premium-section" aria-labelledby="platform-map-title">
      <div className="premium-section-header">
        <span className="premium-eyebrow">PLATFORM MAP</span>
        <h2 className="premium-section-title" id="platform-map-title">
          Одна система вместо разрозненного набора сервисов
        </h2>
      </div>

      <div className="premium-platform-map">
        {modules.slice(0, 4).map((module, index) => (
          <article
            className={`premium-platform-module ${activeIndex === index ? 'premium-platform-module-active' : ''}`}
            key={module.title}
          >
            <strong>{module.title}</strong>
            <span>{module.description}</span>
          </article>
        ))}

        <article className="premium-platform-core">
          <span>TrainerHub</span>
          <strong>Core</strong>
          <p>Доступы, роли, операции и аналитика связаны в одном рабочем контуре.</p>
        </article>

        {modules.slice(4).map((module, index) => {
          const moduleIndex = index + 4;
          return (
            <article
              className={`premium-platform-module ${activeIndex === moduleIndex ? 'premium-platform-module-active' : ''}`}
              key={module.title}
            >
              <strong>{module.title}</strong>
              <span>{module.description}</span>
            </article>
          );
        })}
      </div>
    </AnimatedSection>
  );
}
