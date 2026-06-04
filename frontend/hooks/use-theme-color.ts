/**
 * Learn more about light and dark modes:
 * https://docs.expo.dev/guides/color-schemes/
 */
import { COLORS } from '../src/shared/constants/theme';
import { useColorScheme } from './use-color-scheme';

export function useThemeColor(
  props: { light?: string; dark?: string },
  colorName: string
) {
  const theme = useColorScheme() ?? 'light';
  const colorFromProps = props[theme];

  if (colorFromProps) {
    return colorFromProps;
  }

  // Cast COLORS to 'any' to bypass TypeScript's strict index signature checks
  const safeColors: any = COLORS;

  // 1. Check if your theme uses nested light/dark objects (Expo default)
  if (safeColors[theme] && safeColors[theme][colorName]) {
    return safeColors[theme][colorName];
  }
  
  // 2. Check if your theme uses a flat list of colors (Custom themes)
  if (safeColors[colorName]) {
    return safeColors[colorName];
  }

  // 3. Fallback to prevent a hard crash if the colorName doesn't exist
  return theme === 'light' ? '#000' : '#fff';
}