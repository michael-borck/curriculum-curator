// Desktop Layout Optimization Utilities

import { useState, useEffect } from 'react';

export interface DesktopLayoutConfig {
  windowWidth: number;
  windowHeight: number;
  isSmallDesktop: boolean;
  isMediumDesktop: boolean;
  isLargeDesktop: boolean;
  isUltrawide: boolean;
  contentMaxWidth: number;
  previewPanelWidth: number;
  sidebarWidth: number;
  gridColumns: number;
  fontSize: {
    base: number;
    small: number;
    large: number;
  };
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
}

// Desktop breakpoints (different from mobile)
export const DESKTOP_BREAKPOINTS = {
  SMALL: 1024,   // Small laptops
  MEDIUM: 1366,  // Standard laptops
  LARGE: 1920,   // Desktop monitors
  ULTRAWIDE: 2560 // Ultrawide monitors
} as const;

export function useDesktopLayout(): DesktopLayoutConfig {
  const [windowSize, setWindowSize] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1400,
    height: typeof window !== 'undefined' ? window.innerHeight : 900
  });

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isSmallDesktop = windowSize.width >= DESKTOP_BREAKPOINTS.SMALL && windowSize.width < DESKTOP_BREAKPOINTS.MEDIUM;
  const isMediumDesktop = windowSize.width >= DESKTOP_BREAKPOINTS.MEDIUM && windowSize.width < DESKTOP_BREAKPOINTS.LARGE;
  const isLargeDesktop = windowSize.width >= DESKTOP_BREAKPOINTS.LARGE && windowSize.width < DESKTOP_BREAKPOINTS.ULTRAWIDE;
  const isUltrawide = windowSize.width >= DESKTOP_BREAKPOINTS.ULTRAWIDE;

  // Calculate optimal content widths based on screen size
  const getContentMaxWidth = (): number => {
    if (isSmallDesktop) return 760;
    if (isMediumDesktop) return 900;
    if (isLargeDesktop) return 1200;
    return 1400; // Ultrawide
  };

  const getPreviewPanelWidth = (): number => {
    if (isSmallDesktop) return 320;
    if (isMediumDesktop) return 380;
    if (isLargeDesktop) return 420;
    return 480; // Ultrawide
  };

  const getSidebarWidth = (): number => {
    if (isSmallDesktop) return 240;
    if (isMediumDesktop) return 280;
    return 320; // Large and ultrawide
  };

  const getGridColumns = (): number => {
    if (isSmallDesktop) return 1;
    if (isMediumDesktop) return 2;
    if (isLargeDesktop) return 2;
    return 3; // Ultrawide
  };

  const getFontSizes = () => {
    const baseScale = isSmallDesktop ? 0.9 : isMediumDesktop ? 1 : isLargeDesktop ? 1.1 : 1.2;
    return {
      base: 16 * baseScale,
      small: 14 * baseScale,
      large: 18 * baseScale
    };
  };

  const getSpacing = () => {
    const scale = isSmallDesktop ? 0.8 : isMediumDesktop ? 1 : 1.2;
    return {
      xs: 4 * scale,
      sm: 8 * scale,
      md: 16 * scale,
      lg: 24 * scale,
      xl: 32 * scale
    };
  };

  return {
    windowWidth: windowSize.width,
    windowHeight: windowSize.height,
    isSmallDesktop,
    isMediumDesktop,
    isLargeDesktop,
    isUltrawide,
    contentMaxWidth: getContentMaxWidth(),
    previewPanelWidth: getPreviewPanelWidth(),
    sidebarWidth: getSidebarWidth(),
    gridColumns: getGridColumns(),
    fontSize: getFontSizes(),
    spacing: getSpacing()
  };
}

export const getOptimalModalSize = (windowWidth: number, windowHeight: number) => {
  return {
    width: Math.min(Math.max(windowWidth * 0.8, 600), 1200),
    height: Math.min(Math.max(windowHeight * 0.8, 500), 900)
  };
};

export const getOptimalPreviewWidth = (windowWidth: number): number => {
  if (windowWidth < DESKTOP_BREAKPOINTS.MEDIUM) return 320;
  if (windowWidth < DESKTOP_BREAKPOINTS.LARGE) return 380;
  if (windowWidth < DESKTOP_BREAKPOINTS.ULTRAWIDE) return 420;
  return 480;
};

export const shouldShowPreviewByDefault = (windowWidth: number): boolean => {
  return windowWidth >= DESKTOP_BREAKPOINTS.MEDIUM;
};

export const getOptimalWizardLayout = (windowWidth: number) => {
  if (windowWidth < DESKTOP_BREAKPOINTS.MEDIUM) {
    return {
      containerMaxWidth: '90%',
      formGridColumns: 1,
      showCompactMode: true
    };
  }
  
  if (windowWidth < DESKTOP_BREAKPOINTS.LARGE) {
    return {
      containerMaxWidth: '900px',
      formGridColumns: 2,
      showCompactMode: false
    };
  }
  
  return {
    containerMaxWidth: '1200px',
    formGridColumns: 2,
    showCompactMode: false
  };
};

// CSS-in-JS utility for responsive styles
export const createResponsiveStyles = (layout: DesktopLayoutConfig) => ({
  container: {
    maxWidth: layout.contentMaxWidth,
    margin: '0 auto',
    padding: `0 ${layout.spacing.md}px`
  },
  
  grid: {
    display: 'grid',
    gridTemplateColumns: `repeat(${layout.gridColumns}, 1fr)`,
    gap: `${layout.spacing.md}px`
  },
  
  text: {
    fontSize: `${layout.fontSize.base}px`,
    lineHeight: 1.5
  },
  
  smallText: {
    fontSize: `${layout.fontSize.small}px`,
    lineHeight: 1.4
  },
  
  largeText: {
    fontSize: `${layout.fontSize.large}px`,
    lineHeight: 1.3
  },
  
  spacing: {
    marginBottom: `${layout.spacing.md}px`
  }
});

// Window state management for Tauri
export const saveWindowState = () => {
  if (typeof window !== 'undefined') {
    const state = {
      width: window.innerWidth,
      height: window.innerHeight,
      x: window.screenX,
      y: window.screenY
    };
    
    localStorage.setItem('curriculum_curator_window_state', JSON.stringify(state));
  }
};

export const restoreWindowState = () => {
  if (typeof window !== 'undefined') {
    try {
      const saved = localStorage.getItem('curriculum_curator_window_state');
      if (saved) {
        const state = JSON.parse(saved);
        return state;
      }
    } catch (error) {
      console.warn('Failed to restore window state:', error);
    }
  }
  return null;
};