import React, { useEffect } from 'react';
import { Slot, useRouter, useSegments, useRootNavigationState } from 'expo-router';
import { Provider as PaperProvider } from 'react-native-paper';
import { AuthProvider, useAuth } from '../features/auth/AuthContext';

// We extract the routing logic into an inner component so it can consume the AuthContext
function RootNavigation() {
  const { isAuthenticated, loading } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  const navigationState = useRootNavigationState();

  useEffect(() => {
    // CRITICAL FIX: Do not attempt to route until the navigation tree is mounted
    if (!navigationState?.key || loading) return;

    const inAuthGroup = segments[0] === '(auth)';

    if (!isAuthenticated && !inAuthGroup) {
      // If the user is not authenticated and not in the auth group, send them to login
      router.replace('/(auth)/login');
    } else if (isAuthenticated && inAuthGroup) {
      // If the user is authenticated and tries to go to login, send them to dashboard
      router.replace('/(tabs)/dashboard');
    }
  }, [isAuthenticated, loading, segments, navigationState]);

  // Render the current route
  return <Slot />;
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <PaperProvider>
        <RootNavigation />
      </PaperProvider>
    </AuthProvider>
  );
}
