import { Audio } from 'expo-av'; // For permission requests
import { Alert } from 'react-native';
import { startAudioStream, stopAudioStream } from '../features/handoff/audioStream';

// --- 1. BASE URL CONFIGURATION (CRITICAL!) ---
// Consumes the full URL from .env.development
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://10.19.73.68:8000';
// ---------------------------------------------

/**
 * Performs login using username and password (x-www-form-urlencoded).
 * Corresponds to: POST /api/v1/login/token
 */
export const apiLogin = async (username, password) => {
    console.log(`API: Attempting login for ${username}`);
    try {
        const body = new URLSearchParams();
        body.append('username', username);
        body.append('password', password);

        const response = await fetch(`${API_BASE_URL}/api/v1/login/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: body.toString(),
        });

        // 1. Read the raw response text first
        const rawText = await response.text();
        let data;

        // 2. Safely attempt to parse it as JSON
        try {
            data = JSON.parse(rawText);
        } catch (parseError) {
            // 3. If parsing fails, throw the raw server output (e.g., "Internal Server Error")
            throw new Error(`Server Error (${response.status}): ${rawText}`);
        }

        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }
        if (!data.access_token) {
            throw new Error('No access_token received from server');
        }

        console.log('API: Login successful.');
        return data.access_token;

    } catch (error) {
        console.error('API Error (apiLogin):', error);
        Alert.alert('Login Failed', error.message);
        return null;
    }
};
/**
 * Generic helper function for making authenticated API calls (JSON).
 */
const fetchWithToken = async (endpoint, token, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`;
    console.log(`API: Calling ${options.method || 'GET'} ${url}`);

    if (!token) {
        Alert.alert('Authentication Error', 'No auth token found. Please log in again.');
        throw new Error('No auth token found');
    }

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
        'Authorization': `Bearer ${token}`,
    };

    try {
        const response = await fetch(url, { ...options, headers });

        if (response.status === 401) {
            Alert.alert('Unauthorized', 'Your session expired. Please log in again.');
            throw new Error('Unauthorized');
        }
        if (response.status === 403) {
            Alert.alert('Access Denied', 'You do not have permission for this action.');
            throw new Error('Forbidden');
        }

        if (response.status === 204 || response.headers.get('content-length') === '0') {
            return { success: true };
        }

        const data = await response.json();

        if (!response.ok) {
            const errorMessage = data.detail ?
                (typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.detail)
                : `API Error ${response.status}`;
            throw new Error(errorMessage);
        }

        return data;

    } catch (error) {
        console.error(`API Error (fetchWithToken ${endpoint}):`, error.message);
        if (error.message !== 'Unauthorized' && error.message !== 'Forbidden') {
            Alert.alert('API Error', error.message);
        }
        throw error;
    }
};

// --- Admin Functions ---
export const apiAdminCreateUser = (userData, adminToken) => {
    return fetchWithToken('/api/v1/admin/users', adminToken, {
        method: 'POST',
        body: JSON.stringify(userData),
    });
};

export const apiAdminGetUserList = (adminToken) => {
    return fetchWithToken('/api/v1/admin/users', adminToken);
};

// --- Patient and Encounter Functions ---
export const apiRegisterPatient = (patientData, token) => {
    return fetchWithToken('/api/v1/patients/register', token, {
        method: 'POST',
        body: JSON.stringify(patientData),
    });
};

export const apiSearchPatients = (query, token) => {
    return fetchWithToken(`/api/v1/patients/search/?query=${encodeURIComponent(query)}`, token);
};

export const apiGetPatientDetails = (patientId, token) => {
    return fetchWithToken(`/api/v1/patients/${patientId}`, token);
};

export const apiGetPatientHistory = (patientId, token) => {
    return fetchWithToken(`/api/v1/patients/${patientId}/history`, token);
};

export const apiCreateEncounter = (encounterData, token) => {
    return fetchWithToken('/api/v1/encounters/', token, {
        method: 'POST',
        body: JSON.stringify(encounterData),
    });
};

export const apiGetEncounterDetails = (encounterId, token) => {
    return fetchWithToken(`/api/v1/encounters/${encounterId}`, token);
};

export const apiUpdateEncounter = (encounterId, patchData, token) => {
    return fetchWithToken(`/api/v1/encounters/${encounterId}`, token, {
        method: 'PATCH',
        body: JSON.stringify(patchData),
    });
};

export const apiUpdateLabStatus = (encounterId, statusData, token) => {
    return fetchWithToken(`/api/v1/encounters/${encounterId}/lab-status`, token, {
        method: 'PATCH',
        body: JSON.stringify(statusData),
    });
};

export const apiGetCriticalAlerts = (token) => {
    return fetchWithToken('/api/v1/encounters/alerts/critical', token);
};

export const apiGetEncounterNotes = (encounterId, token) => {
    return fetchWithToken(`/api/v1/encounters/${encounterId}/notes`, token);
};

// --- Task Management Functions ---
export const apiGetMyTasks = (token) => {
    return fetchWithToken('/api/v1/tasks/me', token);
};

export const apiGetEncounterTasks = (encounterId, token) => {
    return fetchWithToken(`/api/v1/tasks/encounter/${encounterId}`, token);
};

export const apiCreateTask = (taskData, token) => {
    return fetchWithToken('/api/v1/tasks/', token, {
        method: 'POST',
        body: JSON.stringify(taskData),
    });
};

export const apiCompleteTask = (taskId, token) => {
    return fetchWithToken(`/api/v1/tasks/${taskId}/complete`, token, {
        method: 'PATCH',
    });
};

export const requestAudioPermissions = async () => {
    console.log('Requesting microphone permissions...');
    try {
        const { status } = await Audio.requestPermissionsAsync();
        if (status === 'granted') {
            console.log('Permission granted!');
            await Audio.setAudioModeAsync({
                allowsRecordingIOS: true,
                playsInSilentModeIOS: true,
            });
            return true;
        } else {
            console.log('Permission denied!');
            Alert.alert('Permission Required', 'Microphone access is needed for dictation.');
            return false;
        }
    } catch (err) {
        console.error('Failed to request permissions', err);
        Alert.alert('Error', 'Could not request microphone permissions.');
        return false;
    }
};

/**
 * Starts audio recording and connects to WebSocket for live streaming.
 */
export const startStreamingAudio = async (encounterId, token, onTranscript, onError) => {
    // Converts http:// to ws:// and https:// to wss:// natively
    const wsUrl = `${API_BASE_URL.replace(/^http/, 'ws')}/ws/dictation/${encounterId}?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[Dictation] WebSocket open, starting audio stream');
        startAudioStream((pcmChunk) => {
            if (ws.readyState === WebSocket.OPEN) {
               ws.send(pcmChunk);
            }
        });
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.transcript) {
            onTranscript(data.transcript, data.is_final);
        }
    };

    ws.onerror = (error) => {
        console.error('[Dictation] WebSocket error:', error);
        onError(error);
    };

    ws.onclose = (event) => {
        console.log('[Dictation] WebSocket closed:', event.code, event.reason);
        stopAudioStream();
    };

    return ws;
 };

export const stopStreamingAudio = (ws) => {
    stopAudioStream();
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'User ended dictation');
    }
 };