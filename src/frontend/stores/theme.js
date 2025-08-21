// Theme Store for OpenWebUI
// Manages theme switching between original and blueprint themes

import { writable, derived } from 'svelte/store';

// Available themes
export const THEMES = {
  ORIGINAL: 'original',
  BLUEPRINT: 'blueprint'
};

// Theme configuration
const themeConfig = {
  [THEMES.ORIGINAL]: {
    name: 'Original',
    description: 'Classic OpenWebUI theme',
    cssClass: 'theme-original',
    files: []
  },
  [THEMES.BLUEPRINT]: {
    name: 'Blueprint',
    description: 'Technical drawing inspired theme for tojo.world',
    cssClass: 'theme-blueprint',
    files: [
      '/src/frontend/styles/blueprint-theme.css',
      '/src/frontend/styles/blueprint-components.css'
    ]
  }
};

// Get theme from localStorage or default to blueprint for tojo.world
function getInitialTheme() {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem('openwebui-theme');
    return stored && Object.values(THEMES).includes(stored) ? stored : THEMES.BLUEPRINT;
  }
  return THEMES.BLUEPRINT;
}

// Create theme store
export const currentTheme = writable(getInitialTheme());

// Derived store for theme configuration
export const themeSettings = derived(currentTheme, ($currentTheme) => {
  return themeConfig[$currentTheme];
});

// Theme switching function
export function setTheme(theme) {
  if (Object.values(THEMES).includes(theme)) {
    currentTheme.set(theme);
    
    // Persist to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('openwebui-theme', theme);
      
      // Update document class for CSS targeting
      document.documentElement.className = 
        document.documentElement.className.replace(/theme-\w+/g, '');
      document.documentElement.classList.add(themeConfig[theme].cssClass);
    }
  }
}

// Initialize theme on first load
export function initializeTheme() {
  if (typeof window !== 'undefined') {
    const theme = getInitialTheme();
    setTheme(theme);
  }
}

// Get available themes
export function getAvailableThemes() {
  return Object.entries(THEMES).map(([key, value]) => ({
    id: value,
    ...themeConfig[value]
  }));
}

// Check if theme is active
export function isThemeActive(theme) {
  let current;
  currentTheme.subscribe(value => current = value)();
  return current === theme;
}

// Blueprint theme utilities
export const blueprintUtils = {
  // Check if blueprint theme is active
  isActive: () => isThemeActive(THEMES.BLUEPRINT),
  
  // Get blueprint CSS variables
  getCSSVariables: () => ({
    '--blueprint-primary': '#003d7a',
    '--blueprint-secondary': '#0066cc',
    '--blueprint-tertiary': '#4da6ff',
    '--blueprint-accent': '#ff6b35',
    '--paper-base': '#fefcf6',
    '--paper-secondary': '#f8f6f0',
    '--paper-tertiary': '#f0ede5',
    '--line-primary': '#003d7a',
    '--line-secondary': '#666a73',
    '--line-construction': '#b8bcc8',
    '--line-grid': 'rgba(0, 61, 122, 0.1)',
    '--text-primary': '#1a1d23',
    '--text-secondary': '#4a5568',
    '--text-tertiary': '#718096',
    '--text-blueprint': '#003d7a'
  }),
  
  // Apply tojo.world branding
  applyBranding: () => {
    if (typeof document !== 'undefined') {
      // Add tojo.world watermark if not present
      if (!document.querySelector('.tojo-watermark')) {
        const watermark = document.createElement('div');
        watermark.className = 'tojo-watermark';
        watermark.textContent = 'hosted on tojo.world';
        document.body.appendChild(watermark);
      }
    }
  }
};

// Auto-initialize on module load
if (typeof window !== 'undefined') {
  initializeTheme();
}