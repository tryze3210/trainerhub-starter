import Link from 'next/link';

import { AnimatedSection } from '@/design-system';

export function FinalPremiumCta() {
  return (
    <AnimatedSection className="premium-section premium-final-cta-section" aria-labelledby="final-premium-cta-title">
      <div className="premium-final-cta">
        <span className="premium-eyebrow">TRAINERHUB</span>
        <h2 id="final-premium-cta-title">Готовы собрать тренерский бизнес в систему, которая выглядит и работает дороже?</h2>
        <p>Запустите каталог программ, оплату, обучение, CRM и личные кабинеты на единой платформе TrainerHub.</p>
        <div className="premium-actions">
          <Link href="/register" className="premium-primary-button">
            Начать как тренер
          </Link>
          <Link href="/catalog" className="premium-secondary-button">
            Открыть каталог
          </Link>
        </div>
      </div>
    </AnimatedSection>
  );
}
