import { SplashScreen, Stack, useRouter } from 'expo-router';
import { useEffect } from 'react';
// import { Provider as PaperProvider } from 'react-native-paper';
// import { PaperTheme } from '../constants/theme';
import { AuthProvider, useAuth } from '../context/AuthContext';
import LoadingScreen from './utility/LoadingScreen';

// Prevent the native splash screen from auto-hiding before auth check is complete
SplashScreen.preventAutoHideAsync();

/**
 * This component handles the core navigation logic.
 * It waits for the AuthContext to load the token,
 * then redirects the user to the correct screen group.
 */
function RootLayoutNav() {
  const { userToken, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) {
      // AuthContext is still checking SecureStore for a token.
      // We do nothing and let the LoadingScreen show.
      return;
    }

    // Auth check is complete, hide the native splash screen.
    SplashScreen.hideAsync();

    if (userToken) {
      // User is logged in. Send them to the main app dashboard.
      // Adjust '/(tabs)/dashboard' if your main screen is different.
      router.replace('/(tabs)/dashboard');
    } else {
      // User is not logged in. Send them to the login screen.
      // Adjust '/(auth)/login' if your login screen is different.
      router.replace('/(auth)/login');
    }
  }, [isLoading, userToken]); // Re-run this logic only when auth state changes

  // Show a loading screen while we're checking auth and redirecting
  if (isLoading) {
    return <LoadingScreen />;
  }

  // This Stack defines all possible screen groups.
  // The useEffect hook above handles which one is shown.
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(auth)" />
      <Stack.Screen name="(tabs)" />
      {/* Add other groups like (admin) or modals here */}
    </Stack>
  );
}

/**
 * This is the main layout for your entire app.
 * It wraps everything in the necessary Providers.
 */
export default function RootLayout() {
  return (
    // 1. AuthProvider handles login state and token
    <AuthProvider>
      {/* 2. PaperProvider handles the visual theme */}
      {/* <PaperProvider theme={PaperTheme}> */}
      <RootLayoutNav />
      {/* </PaperProvider> */}
    </AuthProvider>
  );
}