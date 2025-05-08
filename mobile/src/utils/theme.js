/**
 * VidID Theme Configuration
 * Centralized theme management for consistent styling
 */

// Color palette
export const colors = {
  // Primary colors
  primary: '#6a11cb',
  primaryDark: '#5805b3',
  primaryLight: '#8244e0',
  primaryGradient: ['#6a11cb', '#2575fc'],
  
  // Secondary colors
  secondary: '#2575fc',
  secondaryDark: '#1860e5',
  secondaryLight: '#4a95ff',
  
  // Accent colors
  accent: '#FF8C00',
  accentDark: '#E67E00',
  accentLight: '#FFA732',
  accentGradient: ['#FF8C00', '#FFA500'],
  
  // Text colors
  text: '#333333',
  textLight: '#666666',
  textMuted: '#999999',
  
  // Background colors
  background: '#f8f8f8',
  card: '#ffffff',
  border: '#eeeeee',
  divider: '#f5f5f5',
  
  // Status colors
  success: '#4CAF50',
  error: '#F44336',
  warning: '#FFC107',
  info: '#2196F3',
  
  // Utility colors
  black: '#000000',
  white: '#ffffff',
  transparent: 'transparent',
};

// Typography
export const typography = {
  // Font families
  fontFamily: 'System',
  
  // Font sizes
  fontSizes: {
    xs: 12,
    small: 14,
    medium: 16,
    large: 18,
    xl: 20,
    xxl: 22,
    xxxl: 24,
    title: 28,
    header: 32,
  },
  
  // Font weights
  fontWeights: {
    regular: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  
  // Line heights
  lineHeights: {
    tight: 1.25,
    normal: 1.5,
    loose: 1.75,
  },
};

// Spacing system
export const spacing = {
  xs: 4,
  small: 8,
  medium: 12,
  base: 16,
  large: 20,
  xl: 24,
  xxl: 32,
  xxxl: 40,
  jumbo: 48,
};

// Border radius
export const borderRadius = {
  xs: 4,
  small: 8,
  medium: 12,
  large: 16,
  xl: 20,
  xxl: 24,
  round: 9999,
};

// Shadows
export const shadows = {
  none: {
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  small: {
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  medium: {
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  large: {
    shadowColor: colors.black,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 8,
  },
};

// Animation timing
export const animation = {
  veryFast: 100,
  fast: 200,
  normal: 300,
  slow: 500,
  verySlow: 800,
};

// Default theme
export const defaultTheme = {
  dark: false,
  colors: {
    primary: colors.primary,
    background: colors.background,
    card: colors.card,
    text: colors.text,
    border: colors.border,
    notification: colors.accent,
  },
};

// Dark theme
export const darkTheme = {
  dark: true,
  colors: {
    primary: colors.primary,
    background: '#121212',
    card: '#1E1E1E',
    text: '#FFFFFF',
    border: '#333333',
    notification: colors.accent,
  },
};

// Common button styles
export const buttonStyles = {
  // Primary button
  primary: {
    backgroundColor: colors.primary,
    textColor: colors.white,
    borderRadius: borderRadius.round,
    paddingVertical: spacing.medium,
    paddingHorizontal: spacing.xl,
  },
  
  // Secondary button
  secondary: {
    backgroundColor: colors.secondary,
    textColor: colors.white,
    borderRadius: borderRadius.round,
    paddingVertical: spacing.medium,
    paddingHorizontal: spacing.xl,
  },
  
  // Outline button
  outline: {
    backgroundColor: colors.transparent,
    textColor: colors.primary,
    borderColor: colors.primary,
    borderWidth: 1,
    borderRadius: borderRadius.round,
    paddingVertical: spacing.medium,
    paddingHorizontal: spacing.xl,
  },
  
  // Text button (no background)
  text: {
    backgroundColor: colors.transparent,
    textColor: colors.primary,
    paddingVertical: spacing.small,
    paddingHorizontal: spacing.medium,
  },
};

// Common input styles
export const inputStyles = {
  default: {
    backgroundColor: colors.white,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: borderRadius.medium,
    paddingVertical: spacing.medium,
    paddingHorizontal: spacing.base,
    fontSize: typography.fontSizes.medium,
    color: colors.text,
  },
  
  focused: {
    borderColor: colors.primary,
  },
  
  error: {
    borderColor: colors.error,
  },
};

export default {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  animation,
  defaultTheme,
  darkTheme,
  buttonStyles,
  inputStyles,
};
