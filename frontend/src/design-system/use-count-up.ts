'use client';

import { useEffect, useMemo, useState } from 'react';

type UseCountUpOptions = {
  from?: number;
  to: number;
  durationMs?: number;
  formatter?: (value: number) => string;
};

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') {
    return true;
  }

  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export function useCountUp({ from = 0, to, durationMs = 1200, formatter }: UseCountUpOptions): string {
  const [value, setValue] = useState(from);

  useEffect(() => {
    if (prefersReducedMotion()) {
      setValue(to);
      return undefined;
    }

    let frameId = 0;
    const start = performance.now();
    const distance = to - from;

    const tick = (now: number) => {
      const progress = Math.min((now - start) / durationMs, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(from + distance * eased);

      if (progress < 1) {
        frameId = requestAnimationFrame(tick);
      }
    };

    frameId = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(frameId);
  }, [durationMs, from, to]);

  return useMemo(() => (formatter ? formatter(value) : Math.round(value).toLocaleString('ru-RU')), [formatter, value]);
}
