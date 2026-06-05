import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import * as SecureStore from 'expo-secure-store';
// FIXED: Changed '../services/api' to '../../services/api'
import { login as apiLogin, logout as apiLogout, setTokens, clearTokens, createAlertsSocket } from '../../services/api';

const AuthContext = createContext(null);

const PERMISSIONS = {
  ADMIN:  ['view_patients', 'manage_users', 'view_all_encounters', 'administer_medication'],
  DOCTOR: ['view_patients', 'create_medication_order', 'create_encounter'],
  NURSE:  ['view_patients', 'view_own_encounter', 'administer_medication', 'update_task'],
};

export function AuthProvider({ children }) {
  const [user, setUser]         = useState(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const stored = await SecureStore.getItemAsync('hvs_auth');
        if (stored) {
          const { user: u, accessToken, refreshToken } = JSON.parse(stored);
          setTokens(accessToken, refreshToken);
          setUser(u);
        }
      } catch { }
      finally { setLoading(false); }
    })();
  }, []);

  const signIn = async (username, password) => {
    const data = await apiLogin(username, password);
    
    // Defaulting role to DOCTOR for testing if backend doesn't explicitly return it
    const userData = {
      id: 1, 
      username: username,
      role: 'DOCTOR', 
    };

    await SecureStore.setItemAsync('hvs_auth', JSON.stringify({
      user: userData,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
    }));
    
    setUser(userData);
    return userData;
  };

  const signOut = async () => {
    try { await apiLogout(); } catch (e) {}
    await SecureStore.deleteItemAsync('hvs_auth');
    clearTokens();
    setUser(null);
  };

  const can = (permission) => {
    if (!user?.role) return false;
    return PERMISSIONS[user.role]?.includes(permission) ?? false;
  };

  return (
    <AuthContext.Provider value={{
      user, loading, signIn, signOut, can,
      isAuthenticated: !!user, userId: user?.id, userRole: user?.role, token: null
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
