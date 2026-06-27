'use client';

import { createContext, useContext, useMemo, useState, type CSSProperties, type ReactNode } from 'react';

export type DSThemeMode = 'light' | 'dark' | 'system';
export type DSResolvedThemeMode = 'light' | 'dark';
export type DSBrandName = 'trainerhub' | 'studio' | 'academy' | 'wellness';

export type DSBrandPalette = {
  name: DSBrandName;
  label: string;
  primary: string;
  primaryHover: string;
  primarySoft: string;
  accent: string;
  accentSoft: string;
};

export type DSWhiteLabelTheme = Partial<{
  primary: string;
  primaryHover: string;
  primarySoft: string;
  accent: string;
  accentSoft: string;
  logoUrl: string;
}>;

export const dsBrandPalettes: Record<DSBrandName, DSBrandPalette> = {
  trainerhub: {
    name: 'trainerhub',
    label: 'TrainerHub',
    primary: '#2563eb',
    primaryHover: '#1d4ed8',
    primarySoft: 'rgba(37, 99, 235, 0.1)',
    accent: '#0f766e',
    accentSoft: 'rgba(15, 118, 110, 0.1)',
  },
  studio: {
    name: 'studio',
    label: 'Studio',
    primary: '#0f766e',
    primaryHover: '#115e59',
    primarySoft: 'rgba(15, 118, 110, 0.11)',
    accent: '#7c3aed',
    accentSoft: 'rgba(124, 58, 237, 0.1)',
  },
  academy: {
    name: 'academy',
    label: 'Academy',
    primary: '#0369a1',
    primaryHover: '#075985',
    primarySoft: 'rgba(3, 105, 161, 0.1)',
    accent: '#15803d',
    accentSoft: 'rgba(21, 128, 61, 0.1)',
  },
  wellness: {
    name: 'wellness',
    label: 'Wellness',
    primary: '#be123c',
    primaryHover: '#9f1239',
    primarySoft: 'rgba(190, 18, 60, 0.09)',
    accent: '#0e7490',
    accentSoft: 'rgba(14, 116, 144, 0.1)',
  },
};

type DSThemeContextValue = {
  mode: DSThemeMode;
  resolvedMode: DSResolvedThemeMode;
  brand: DSBrandName;
  setMode: (mode: DSThemeMode) => void;
  setBrand: (brand: DSBrandName) => void;
};

const DSThemeContext = createContext<DSThemeContextValue | null>(null);

function resolveMode(mode: DSThemeMode): DSResolvedThemeMode {
  if (mode !== 'system') {
    return mode;
  }

  if (typeof window === 'undefined') {
    return 'light';
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function getWhiteLabelThemeStyle(theme?: DSWhiteLabelTheme): CSSProperties | undefined {
  if (!theme) {
    return undefined;
  }

  return {
    '--color-primary': theme.primary,
    '--color-primary-hover': theme.primaryHover,
    '--color-primary-soft': theme.primarySoft,
    '--color-accent': theme.accent,
    '--color-accent-soft': theme.accentSoft,
    '--brand-logo-url': theme.logoUrl ? `url("${theme.logoUrl}")` : undefined,
  } as CSSProperties;
}

export function DSThemeProvider({
  children,
  initialMode = 'light',
  initialBrand = 'trainerhub',
  whiteLabel,
}: {
  children: ReactNode;
  initialMode?: DSThemeMode;
  initialBrand?: DSBrandName;
  whiteLabel?: DSWhiteLabelTheme;
}) {
  const [mode, setMode] = useState<DSThemeMode>(initialMode);
  const [brand, setBrand] = useState<DSBrandName>(initialBrand);
  const resolvedMode = resolveMode(mode);
  const style = getWhiteLabelThemeStyle(whiteLabel);
  const value = useMemo(
    () => ({
      mode,
      resolvedMode,
      brand,
      setMode,
      setBrand,
    }),
    [brand, mode, resolvedMode],
  );

  return (
    <DSThemeContext.Provider value={value}>
      <div
        className="ds-theme-root"
        data-brand={brand}
        data-theme={resolvedMode}
        data-white-label={whiteLabel ? 'true' : undefined}
        style={style}
      >
        {children}
      </div>
    </DSThemeContext.Provider>
  );
}

export function useDSTheme() {
  const value = useContext(DSThemeContext);

  if (!value) {
    throw new Error('useDSTheme must be used inside DSThemeProvider');
  }

  return value;
}
