import * as SecureStore from 'expo-secure-store';

const AUTH_STORAGE_KEY = 'hvs_auth';

let rawUrl = process.env.EXPO_PUBLIC_API_URL;
if (!rawUrl) {
  console.warn('EXPO_PUBLIC_API_URL is missing. Falling back to localhost.');
  rawUrl = 'http://localhost:8000';
} else if (!rawUrl.startsWith('http')) {
  rawUrl = `http://${rawUrl}`;
}

export const BASE_URL = rawUrl.replace(/\/+$/, '');
export const WS_BASE_URL = BASE_URL.replace(/^http/, (protocol) => (protocol === 'https' ? 'wss' : 'ws'));

let accessToken = null;
let refreshToken = null;
let refreshPromise = null;
let unauthorizedHandler = null;

export const setTokens = (nextAccessToken, nextRefreshToken) => {
  accessToken = nextAccessToken;
  refreshToken = nextRefreshToken;
};

export const clearTokens = () => {
  accessToken = null;
  refreshToken = null;
};

export const setUnauthorizedHandler = (handler) => {
  unauthorizedHandler = handler;
};

export const getStoredSession = async () => {
  const stored = await SecureStore.getItemAsync(AUTH_STORAGE_KEY);
  if (!stored) {
    return null;
  }
  return JSON.parse(stored);
};

export const saveAuthSession = async ({ user, accessToken: nextAccessToken, refreshToken: nextRefreshToken }) => {
  setTokens(nextAccessToken, nextRefreshToken);
  await SecureStore.setItemAsync(
    AUTH_STORAGE_KEY,
    JSON.stringify({ user, accessToken: nextAccessToken, refreshToken: nextRefreshToken })
  );
};

export const clearAuthSession = async () => {
  clearTokens();
  await SecureStore.deleteItemAsync(AUTH_STORAGE_KEY);
};

const parseErrorMessage = async (response) => {
  const payload = await response.json().catch(() => ({}));
  if (typeof payload.detail === 'string') {
    return payload.detail;
  }
  if (payload.detail && typeof payload.detail === 'object') {
    return payload.detail.message || JSON.stringify(payload.detail);
  }
  return `API Error: ${response.status}`;
};

const handleUnauthorized = async () => {
  await clearAuthSession();
  if (typeof unauthorizedHandler === 'function') {
    unauthorizedHandler();
  }
};

const rotateRefreshToken = async () => {
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  const response = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = await response.json();
  const currentSession = await getStoredSession();
  await saveAuthSession({
    user: currentSession?.user ?? null,
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
  });
  return payload.access_token;
};

async function request(method, path, body = null, options = {}) {
  const { isRetry = false, headers: extraHeaders = {}, contentType = 'application/json' } = options;
  const headers = {
    ...extraHeaders,
    ...(contentType ? { 'Content-Type': contentType } : {}),
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
  };

  const response = await fetch(`${BASE_URL}/api/v1${path}`, {
    method,
    headers,
    body: body == null ? undefined : contentType === 'application/json' ? JSON.stringify(body) : body,
  });

  if (response.status === 401 && !isRetry && refreshToken && path !== '/auth/refresh') {
    try {
      refreshPromise = refreshPromise ?? rotateRefreshToken();
      await refreshPromise;
      return await request(method, path, body, { ...options, isRetry: true });
    } catch (error) {
      await handleUnauthorized();
      throw error;
    } finally {
      refreshPromise = null;
    }
  }

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  if (response.status === 204) {
    return null;
  }

  const responseContentType = response.headers.get('content-type') || '';
  if (!responseContentType.includes('application/json')) {
    return null;
  }

  return response.json();
}

const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  put: (path, body) => request('PUT', path, body),
  patch: (path, body) => request('PATCH', path, body),
  delete: (path) => request('DELETE', path),
};

export default api;

export const loginUser = async (username, password) => {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${BASE_URL}/api/v1/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData.toString(),
  });

  if (!response.ok) {
    throw new Error(await parseErrorMessage(response));
  }

  const payload = await response.json();
  setTokens(payload.access_token, payload.refresh_token);
  return payload;
};

export const logoutUser = async () => {
  try {
    if (refreshToken) {
      await api.post('/auth/logout', { refresh_token: refreshToken });
    }
  } finally {
    await clearAuthSession();
  }
};

export const registerUser = async (userData) => api.post('/register', userData);
export const registerPatient = async (patientData) => api.post('/patients/register', patientData);
export const createEncounter = async (encounterData) => api.post('/encounters/', encounterData);
export const updateEncounter = async (encounterId, encounterData) => api.patch(`/encounters/${encounterId}`, encounterData);
export const fetchPatients = async (query) => api.get(`/patients/search/?query=${encodeURIComponent(query)}`);
export const fetchPatient = async (patientId) => api.get(`/patients/${encodeURIComponent(patientId)}`);
export const fetchPatientHistory = async (patientId) => api.get(`/patients/${encodeURIComponent(patientId)}/history`);
export const fetchEncounterNotes = async (encounterId) => api.get(`/encounters/${encounterId}/notes`);
export const fetchCriticalAlerts = async () => api.get('/encounters/alerts/critical');
export const createAdminUser = async (userData) => api.post('/register', userData);
export const fetchMedicationTasks = async (patientId) => api.get(`/medications/tasks/${encodeURIComponent(patientId)}`);
export const administerMedicationTask = async (taskId, payload) => api.post(`/medications/tasks/${taskId}/administer`, payload);
export const fetchMyTasks = async () => [];
export const registerDeviceToken = async (deviceToken) => api.put('/auth/device-token', { device_token: deviceToken });

export const buildDictationWebSocketUrl = (encounterId, token) => `${WS_BASE_URL}/ws/dictation/${encounterId}?token=${encodeURIComponent(token)}`;

export const login = loginUser;
export const logout = logoutUser;
export const apiRegisterPatient = registerPatient;
export const apiCreateEncounter = createEncounter;
export const apiUpdateEncounter = updateEncounter;
export const apiSearchPatients = fetchPatients;
export const apiGetPatientDetails = fetchPatient;
export const apiGetPatientHistory = fetchPatientHistory;
export const apiGetEncounterNotes = fetchEncounterNotes;
export const apiGetCriticalAlerts = fetchCriticalAlerts;
export const apiAdminCreateUser = createAdminUser;
export const apiGetMedicationTasks = fetchMedicationTasks;
export const apiAdministerMedicationTask = administerMedicationTask;
