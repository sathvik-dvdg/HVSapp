import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { jwtDecode } from 'jwt-decode';
import {
  clearAuthSession,
  getStoredSession,
  loginUser,
  logoutUser,
  saveAuthSession,
  setTokens,
  setUnauthorizedHandler,
} from '../../services/api';

const AuthContext = createContext(null);

const PERMISSIONS = {
  admin: ['view_patients', 'manage_users', 'view_all_encounters', 'administer_medication'],
  doctor: ['view_patients', 'create_medication_order', 'create_encounter'],
  nurse: ['view_patients', 'view_own_encounter', 'administer_medication', 'update_task'],
};

const buildUserFromToken = (nextAccessToken, username = null) => {
  const decoded = jwtDecode(nextAccessToken);
  return {
    id: decoded.sub ? Number(decoded.sub) : null,
    username,
    role: typeof decoded.role === 'string' ? decoded.role.toLowerCase() : null,
  };
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [userToken, setUserToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const stored = await getStoredSession();
        if (stored) {
          const { user: storedUser, accessToken, refreshToken } = stored;
          setTokens(accessToken, refreshToken);
          setUser(storedUser);
          setUserToken(accessToken);
        }
      } catch (error) {
        console.error('Failed to restore auth session', error);
        await clearAuthSession();
      }
      finally { setLoading(false); }
    })();
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null);
      setUserToken(null);
    });

    return () => setUnauthorizedHandler(null);
  }, []);

  const signIn = async (username, password) => {
    const data = await loginUser(username, password);
    const userData = buildUserFromToken(data.access_token, username);

    await saveAuthSession({
      user: userData,
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
    });

    setUser(userData);
    setUserToken(data.access_token);
    return userData;
  };

  const signOut = async () => {
    try {
      await logoutUser();
    } catch (error) {
      console.error('Logout failed', error);
      await clearAuthSession();
    }
    setUser(null);
    setUserToken(null);
  };

  const can = (permission) => {
    if (!user?.role) return false;
    return PERMISSIONS[user.role]?.includes(permission) ?? false;
  };

  const contextValue = useMemo(() => ({
    user,
    loading,
    signIn,
    signOut,
    can,
    isAuthenticated: !!user,
    userId: user?.id ?? null,
    userRole: user?.role ?? null,
    userToken,
    token: userToken,
  }), [loading, user, userToken]);

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
