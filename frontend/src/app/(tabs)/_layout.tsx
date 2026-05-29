// app/(tabs)/_layout.js
import { Tabs } from 'expo-router';
import React from 'react';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { COLORS } from '../../constants/theme';
import { useAuth } from '../../context/AuthContext';

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
          } else if (route.name === 'createUser') { // Admin screen
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
        name="dashboard" // Links to app/(tabs)/dashboard.js
        options={{ title: 'Dashboard' }} 
      />
      <Tabs.Screen 
        name="patients" // Links to app/(tabs)/patients.js
        options={{ title: 'Patients' }} 
      />
      <Tabs.Screen 
        name="register" // Links to app/(tabs)/register.js
        options={{ title: 'Register' }} 
      />
      <Tabs.Screen name="settings"
      options={{ title: 'Settings' }}
      />

      {/* --- THIS IS THE FIX: Conditional Rendering --- */}
      {/* Only render this Tab.Screen component if the user is an admin */}
      {userRole === 'admin' && (
        <Tabs.Screen
          // This MUST match your file name: app/(tabs)/createUser.js
          name="createUser" 
          options={{
            title: 'Create User',
          }}
        />
      )}
    </Tabs>
  );
}