// app/patient/[id]/_layout.js
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { createMaterialTopTabNavigator } from '@react-navigation/material-top-tabs';
import { Stack, useLocalSearchParams, withLayoutContext } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
// --- Corrected Import Paths ---
import { COLORS, FONTS, SIZES } from '../../../constants/theme';

const { Navigator } = createMaterialTopTabNavigator();
// Create a custom Expo Router navigator that wraps the Material Top Tabs
const MaterialTopTabs = withLayoutContext(Navigator);

export default function PatientDetailLayout() {
  const { id: patientId } = useLocalSearchParams(); // Gets patient ID from URL

  return (
    <>
      {/* Configure the PARENT stack header */}
      <Stack.Screen
        options={{
          headerShown: true,
          headerStyle: { backgroundColor: COLORS.surface },
          headerTintColor: COLORS.primary,
          headerTitle: () => (
            <View>
              <Text style={styles.headerTitle}>Patient Details</Text>
              <Text style={styles.headerSubtitle}>ID: {patientId}</Text>
            </View>
          ),
          headerBackTitleVisible: false,
        }}
      />

      {/* Render the Tab Navigator linked to the file system */}
      <MaterialTopTabs
        screenOptions={{
          tabBarActiveTintColor: COLORS.primary,
          tabBarInactiveTintColor: COLORS.textLight,
          tabBarIndicatorStyle: {
            backgroundColor: COLORS.primary,
          },
          tabBarStyle: {
            backgroundColor: COLORS.surface,
          },
          tabBarLabelStyle: {
            fontWeight: 'bold',
            fontSize: 12,
          },
        }}
      >
        <MaterialTopTabs.Screen
          name="index" // Automatically links to index.js
          options={{ title: 'Summary' }}
        />
        <MaterialTopTabs.Screen
          name="notes" // Automatically links to notes.js
          options={{ title: 'Notes' }}
        />
        <MaterialTopTabs.Screen
          name="tasks" // Automatically links to tasks.js
          options={{ title: 'Tasks' }}
        />
        <MaterialTopTabs.Screen
          name="history" // Automatically links to history.js
          options={{ title: 'History' }}
        />
        {/* Hide the dictation screen from the tab bar, but allow navigation to it */}
        <MaterialTopTabs.Screen
          name="dictation"
          options={{
            href: null, // This hides it from the tab bar
            title: 'Dictation'
          }}
        />
      </MaterialTopTabs>
    </>
  );
}

const styles = StyleSheet.create({
  headerContainer: {
    backgroundColor: COLORS.surface,
  },
  headerTitle: {
    ...FONTS.h3,
    color: COLORS.primary,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    ...FONTS.body,
    fontSize: 12,
    color: COLORS.textLight,
  },
});