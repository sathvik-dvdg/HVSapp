let rawUrl = process.env.EXPO_PUBLIC_API_URL || 'http://10.173.179.68:8000';

if (!rawUrl.startsWith('http')) {
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

async function request(method, path, body = null) {
  const headers = {
    'Content-Type': 'application/json',
    ..._accessToken ? { Authorization: `Bearer ${_accessToken}` } : {},
  };

  console.log(`[API] ${method} ${BASE_URL}/api/v1${path}`);
  const res = await fetch(`${BASE_URL}/api/v1${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

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
