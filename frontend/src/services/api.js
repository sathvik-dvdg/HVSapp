import * as SecureStore from 'expo-secure-store';

let rawUrl = process.env.EXPO_PUBLIC_API_URL;
if (!rawUrl) {
  console.warn("EXPO_PUBLIC_API_URL is missing. Falling back to localhost.");
  rawUrl = 'http://localhost:8000';
} else if (!rawUrl.startsWith('http')) {
  rawUrl = `http://${rawUrl}`;
}

export const BASE_URL = rawUrl.replace(/\/+$/, '');
export const WS_BASE_URL = BASE_URL.replace(/^http/, 'ws');

console.log("[API] Configured to connect to:", BASE_URL);

let _accessToken  = null;
let _refreshToken = null;

export const setTokens = (access, refresh) => {
  _accessToken  = access;
  _refreshToken = refresh;
};

export const clearTokens = () => {
  _accessToken  = null;
  _refreshToken = null;
};

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) { prom.reject(error); } else { prom.resolve(token); }
  });
  failedQueue = [];
};

async function request(method, path, body = null, isRetry = false) {
  const headers = {
    'Content-Type': 'application/json',
    ..._accessToken ? { Authorization: `Bearer ${_accessToken}` } : {},
  };

  if (!isRetry) console.log(`[API] ${method} ${BASE_URL}/api/v1${path}`);
  
  let res = await fetch(`${BASE_URL}/api/v1${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401 && !isRetry && _refreshToken && path !== '/auth/refresh') {
    if (isRefreshing) {
      return new Promise(function(resolve, reject) {
        failedQueue.push({ resolve, reject });
      }).then(token => {
        return request(method, path, body, true);
      }).catch(err => { throw err; });
    }

    isRefreshing = true;
    try {
      const refreshRes = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: _refreshToken })
      });
      
      if (!refreshRes.ok) throw new Error("Refresh failed");
      
      const data = await refreshRes.json();
      setTokens(data.access_token, data.refresh_token);
      
      const stored = await SecureStore.getItemAsync('hvs_auth');
      if (stored) {
          const authData = JSON.parse(stored);
          authData.accessToken = data.access_token;
          authData.refreshToken = data.refresh_token;
          await SecureStore.setItemAsync('hvs_auth', JSON.stringify(authData));
      }

      processQueue(null, data.access_token);
      return await request(method, path, body, true);
    } catch (err) {
      processQueue(err, null);
      clearTokens();
      await SecureStore.deleteItemAsync('hvs_auth');
      throw new Error("Session expired. Please log in again.");
    } finally {
      isRefreshing = false;
    }
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `API Error: ${res.status}`);
  }

  return await res.json();
}

const api = {
  get:    (path)         => request('GET',    path),
  post:   (path, body)   => request('POST',   path, body),
  put:    (path, body)   => request('PUT',    path, body),
  patch:  (path, body)   => request('PATCH',  path, body),
  delete: (path)         => request('DELETE', path),
};

export default api;

export const login = async (username, password) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  console.log(`[API] Attempting login to ${BASE_URL}/api/v1/auth/token`);
  const res = await fetch(`${BASE_URL}/api/v1/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed.');
  }

  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return data;
};

export const logout = async () => {
  try {
    if (_refreshToken) {
      await api.post('/auth/logout', { refresh_token: _refreshToken });
    }
  } finally {
    clearTokens();
  }
};

export const registerDeviceToken = async (deviceToken) => {
  return api.put('/auth/device-token', { device_token: deviceToken });
};

export const createAlertsSocket = () => {
  return { close: () => {} };
};
