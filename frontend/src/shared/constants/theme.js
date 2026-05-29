// constants/theme.js
import { DefaultTheme as PaperDefaultTheme } from 'react-native-paper';

export const COLORS = {
  // Brand Colors
  primary: '#0067a7',
  accent: '#00a9e0',   // A bright, modern secondary blue for highlights
  
  // Neutral Colors
  white: '#FFFFFF',
  black: '#000000',
  text: '#333333',     // Dark gray for primary text
  textLight: '#777777', // Lighter gray for subtitles
  background: '#F8F9FA', // A very light gray for screen backgrounds
  surface: '#FFFFFF',  // Background for cards, inputs, etc.
  border: '#E0E0E0',   // Border color for inputs and cards

  // Status Colors
  success: '#28a745',
  warning: '#ffc107',
  danger: '#dc3545',
  info: '#17a2b8',
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
  h1: { fontSize: SIZES.h1, fontWeight: 'bold', color: COLORS.primary, marginBottom: SIZES.base },
  h2: { fontSize: SIZES.h2, fontWeight: 'bold', color: COLORS.text, marginBottom: SIZES.base },
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