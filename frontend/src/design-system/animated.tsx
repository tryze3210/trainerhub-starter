'use client';

import type { HTMLAttributes, ReactNode } from 'react';
import { useEffect, useRef, useState } from 'react';

type AnimatedProps<T extends HTMLElement> = HTMLAttributes<T> & {
  children: ReactNode;
  delayMs?: number;
};

function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}

function useReveal(delayMs = 0) {
  const ref = useRef<HTMLElement | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) {
      return undefined;
    }

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) {
      setVisible(true);
      return undefined;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          window.setTimeout(() => setVisible(true), delayMs);
          observer.disconnect();
        }
      },
      { rootMargin: '0px 0px -12% 0px', threshold: 0.16 },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [delayMs]);

  return { ref, visible };
}

export function AnimatedSection({ children, className, delayMs = 0, ...props }: AnimatedProps<HTMLElement>) {
  const { ref, visible } = useReveal(delayMs);

  return (
    <section
      className={cx('animated-section', visible && 'animated-section-visible', className)}
      ref={ref}
      {...props}
    >
      {children}
    </section>
  );
}

export function AnimatedCard({ children, className, delayMs = 0, ...props }: AnimatedProps<HTMLElement>) {
  const { ref, visible } = useReveal(delayMs);

  return (
    <article className={cx('animated-card', visible && 'animated-card-visible', className)} ref={ref} {...props}>
      {children}
    </article>
  );
}

export function AnimatedMetric({ children, className, delayMs = 0, ...props }: AnimatedProps<HTMLElement>) {
  const { ref, visible } = useReveal(delayMs);

  return (
    <article className={cx('animated-metric', visible && 'animated-metric-visible', className)} ref={ref} {...props}>
      {children}
    </article>
  );
}
