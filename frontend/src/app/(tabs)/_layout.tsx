// app/(tabs)/_layout.js
import { Tabs } from 'expo-router';
import React from 'react';
import { MaterialCommunityIcons as Icon } from '@expo/vector-icons';
import { COLORS } from '../../shared/constants/theme';
import { useAuth } from '../../features/auth/AuthContext';

export default function TabLayout() {
  const { userRole } = useAuth(); // Get the user's role

  return (
    <Tabs 
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName = 'help-circle'; // Default icon
          
          if (route.name === 'dashboard') {
            iconName = focused ? 'view-dashboard' : 'view-dashboard-outline';
          } else if (route.name === 'patients') {
            iconName = focused ? 'account-group' : 'account-group-outline';
          } else if (route.name === 'register') {
            iconName = focused ? 'clipboard-plus' : 'clipboard-plus-outline';
          } else if (route.name === 'settings') {
            iconName = focused ? 'cog' : 'cog-outline';
          } else if (route.name === 'createUser') {
            iconName = focused ? 'account-plus' : 'account-plus-outline';
          }
          
          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: 'gray',
        headerShown: false, 
      })}
    >
      {/* --- Standard Tabs (Visible to all) --- */}
      <Tabs.Screen 
        name="dashboard" 
        options={{ title: 'Dashboard' }} 
      />
      <Tabs.Screen 
        name="patients" 
        options={{ title: 'Patients' }} 
      />
      <Tabs.Screen 
        name="register" 
        options={{ title: 'Register' }} 
      />
      <Tabs.Screen 
        name="settings"
        options={{ title: 'Settings' }}
      />

      {/* --- CORRECT WAY TO HIDE TABS --- */}
      <Tabs.Screen
        name="createUser" 
        options={{
          title: 'Create User',
          // href: null completely hides the tab button from the bottom bar
          href: userRole === 'ADMIN' ? '/createUser' : null,
        }}
      />
    </Tabs>
  );
}