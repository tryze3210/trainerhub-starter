import Link from 'next/link';

import { AnimatedCard, AnimatedSection } from '@/design-system';

import { CommercialProofBand } from './commercial-proof-band';
import { FinalPremiumCta } from './final-premium-cta';
import { HeroBusinessConsole } from './hero-business-console';
import { PlatformMapSection } from './platform-map-section';
import { ProductExperienceTimeline } from './product-experience-timeline';
import { RoleWorkspaceSection } from './role-workspace-section';

const painRows = [
  'Клиенты теряются между чатами, таблицами и личными сообщениями.',
  'Оплаты приходится проверять вручную.',
  'Контент разбросан по ссылкам и облакам.',
  'Доступы сложно контролировать после покупки.',
  'Тренеру трудно видеть реальную выручку и прогресс учеников.',
];

export function MarketingHomePage() {
  return (
    <main className="premium-landing premium-home-page">
      <section className="premium-hero" aria-labelledby="home-hero-title">
        <div className="premium-container premium-hero-grid">
          <div className="premium-hero-copy">
            <span className="premium-eyebrow">TRAINERHUB / BUSINESS OS FOR COACHES</span>
            <h1 className="premium-hero-title" id="home-hero-title">
              Превратите тренерскую экспертизу в премиальный цифровой продукт
            </h1>
            <p className="premium-hero-subtitle">
              TrainerHub объединяет каталог программ, видеоуроки, подписки, CRM, расписание, оплаты, доступы и аналитику
              в одном рабочем пространстве для тренеров.
            </p>
            <div className="premium-actions">
              <Link href="/register" className="premium-primary-button">
                Начать как тренер
              </Link>
              <Link href="/catalog" className="premium-secondary-button">
                Посмотреть каталог
              </Link>
            </div>
            <p className="premium-trust-line">Программы · Подписки · Ученики · Оплаты · Выплаты</p>
          </div>

          <HeroBusinessConsole />
        </div>
      </section>

      <AnimatedSection className="premium-section" aria-labelledby="pain-title">
        <div className="premium-container premium-editorial-grid">
          <div>
            <span className="premium-eyebrow">OPERATING COST</span>
            <h2 className="premium-section-title" id="pain-title">
              Когда бизнес тренера растёт, ручные процессы начинают стоить денег
            </h2>
          </div>
          <div className="premium-row-list">
            {painRows.map((row, index) => (
              <AnimatedCard className="premium-row-list__item" delayMs={index * 90} key={row}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <p>{row}</p>
              </AnimatedCard>
            ))}
          </div>
        </div>
      </AnimatedSection>

      <div className="premium-container">
        <PlatformMapSection />
        <RoleWorkspaceSection />
        <ProductExperienceTimeline />
        <CommercialProofBand />
        <FinalPremiumCta />
      </div>
    </main>
  );
}
