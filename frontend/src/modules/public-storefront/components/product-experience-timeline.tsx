'use client';

import { useEffect, useState } from 'react';

import { AnimatedSection } from '@/design-system';

const steps = [
  'Создаёте программу',
  'Публикуете в каталоге',
  'Ученик покупает доступ',
  'Обучается в личном кабинете',
  'Тренер видит прогресс и выручку',
];

export function ProductExperienceTimeline() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) {
      setActiveStep(steps.length - 1);
      return undefined;
    }

    const intervalId = window.setInterval(() => {
      setActiveStep((current) => (current + 1) % steps.length);
    }, 1700);

    return () => window.clearInterval(intervalId);
  }, []);

  return (
    <AnimatedSection className="premium-section" aria-labelledby="experience-title">
      <div className="premium-section-header">
        <span className="premium-eyebrow">PRODUCT FLOW</span>
        <h2 className="premium-section-title" id="experience-title">
          От создания программы до управляемого обучения
        </h2>
      </div>

      <div className="premium-timeline">
        <div className="premium-timeline-line" aria-hidden="true">
          <span className="premium-timeline-line-fill" style={{ width: `${((activeStep + 1) / steps.length) * 100}%` }} />
        </div>
        {steps.map((step, index) => (
          <article
            className={`premium-timeline-step ${index <= activeStep ? 'premium-timeline-step-active' : ''}`}
            key={step}
          >
            <span>{String(index + 1).padStart(2, '0')}</span>
            <h3>{step}</h3>
          </article>
        ))}
      </div>
    </AnimatedSection>
  );
}
