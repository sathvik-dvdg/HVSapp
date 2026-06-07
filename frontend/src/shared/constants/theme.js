// constants/theme.js
import { DefaultTheme as PaperDefaultTheme } from 'react-native-paper';

export const COLORS = {
  primary: '#2F80ED',
  accent: '#56CCF2',
  danger: '#E53935',
  background: '#F5F7FB',
  surface: '#FFFFFF',
  text: '#1F2937',
  textLight: '#6B7280',
  border: '#D7DEE8',
  white: '#FFFFFF',
  lightGray: '#EEF2F7',
  secondary: '#0F766E',
  light: { text: '#1F2937', background: '#FFFFFF', tint: '#2F80ED' },
  dark: { text: '#FFFFFF', background: '#111827', tint: '#56CCF2' },
};

export const SIZES = {
  // Spacing
  base: 8,
  padding: 16,
  paddingLarge: 24,
  radius: 12, // Border radius for cards and buttons

  // Fonts
  h1: 30,
  h2: 24,
  h3: 18,
  h4: 16,
  body: 14,
};

export const FONTS = {
  h1: { fontSize: SIZES.h1, fontWeight: '700', color: COLORS.primary, marginBottom: SIZES.base },
  h2: { fontSize: SIZES.h2, fontWeight: '700', color: COLORS.text, marginBottom: SIZES.base },
  h3: { fontSize: SIZES.h3, fontWeight: '600', color: COLORS.text, marginBottom: SIZES.base / 2 },
  h4: { fontSize: SIZES.h4, fontWeight: '600', color: COLORS.text },
  body: { fontSize: SIZES.body, color: COLORS.textLight, lineHeight: 22 },
};

// Create the theme for React Native Paper
export const PaperTheme = {
  ...PaperDefaultTheme,
  colors: {
    ...PaperDefaultTheme.colors,
    primary: COLORS.primary,
    accent: COLORS.accent,
    error: COLORS.danger,
    background: COLORS.background,
    surface: COLORS.surface,
    text: COLORS.text,
    placeholder: COLORS.textLight,
    onSurface: COLORS.text,
    outline: COLORS.border,
  },
  roundness: SIZES.radius, // Apply global border radius
};
