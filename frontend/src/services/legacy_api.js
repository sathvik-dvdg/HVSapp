import { Audio } from 'expo-av'; // For permission requests
import { Alert } from 'react-native';
import { startAudioStream, stopAudioStream } from '../features/handoff/audioStream';

//
// --- 1. BASE URL CONFIGURATION (CRITICAL!) ---
//
// THIS IS THE MOST IMPORTANT LINE.
// Replace '192.168.X.X' with your backend computer's local IP address.
// You CANNOT use 'http://127.0.0.1:8000' if running on a real device.
//
const BASE_URL = process.env.EXPO_PUBLIC_API_URL || '10.19.73.68:8000';

const PROTOCOL = BASE_URL.includes('hvs.hospital') ? 'https' : 'http'; // Updated to machine IP for Android access
//
// ---------------------------------------------


/**
 * Performs login using username and password (x-www-form-urlencoded).
 * Corresponds to: POST /api/v1/login/token
 */
export const apiLogin = async (username, password) => {
    console.log(`API: Attempting login for ${username}`);
    try {
        // Use URLSearchParams for form-urlencoded data, as required by backend
        const body = new URLSearchParams();
        body.append('username', username);
        body.append('password', password);

        const response = await fetch(`${PROTOCOL}://${BASE_URL}/api/v1/login/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: body.toString(),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }
        if (!data.access_token) {
            throw new Error('No access_token received from server');
        }

        console.log('API: Login successful.');
        return data.access_token; // Return only the token

    } catch (error) {
        console.error('API Error (apiLogin):', error);
        Alert.alert('Login Failed', error.message);
        return null;
    }
};

/**
 * Generic helper function for making authenticated API calls (JSON).
 * Automatically adds the 'Authorization: Bearer <token>' header.
 */
const fetchWithToken = async (endpoint, token, options = {}) => {
    const url = `${PROTOCOL}://${BASE_URL}${endpoint}`;
    console.log(`API: Calling ${options.method || 'GET'} ${url}`);

    // Check if token exists before making the call
    if (!token) {
        Alert.alert('Authentication Error', 'No auth token found. Please log in again.');
        throw new Error('No auth token found');
    }

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
        'Authorization': `Bearer ${token}`, // Adds the JWT
    };

    try {
        const response = await fetch(url, { ...options, headers });

        // Handle common auth errors
        if (response.status === 401) { // Unauthorized
            Alert.alert('Unauthorized', 'Your session expired. Please log in again.');
            throw new Error('Unauthorized');
        }
        if (response.status === 403) { // Forbidden
            Alert.alert('Access Denied', 'You do not have permission for this action.');
            throw new Error('Forbidden');
        }

        // Handle successful but empty responses (e.g., PATCH, DELETE)
        if (response.status === 204 || response.headers.get('content-length') === '0') {
            return { success: true };
        }

        const data = await response.json();

        if (!response.ok) {
            // Use the specific error message from the backend
            const errorMessage = data.detail ?
                (typeof data.detail === 'object' ? JSON.stringify(data.detail) : data.detail)
                : `API Error ${response.status}`;
            throw new Error(errorMessage);
        }

        return data; // Return the JSON data from the backend

    } catch (error) {
        console.error(`API Error (fetchWithToken ${endpoint}):`, error.message);
        if (error.message && error.message.includes('[object Object]')) {
            console.error('Full Error Object:', JSON.stringify(error, null, 2));
        }
        // Alert the user only if it's not one of our custom errors
        if (error.message !== 'Unauthorized' && error.message !== 'Forbidden') {
            Alert.alert('API Error', error.message);
        }
        throw error; // Re-throw for the component to handle (e.g., stop loading)
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
 * Corresponds to: WS /ws/dictation/{session_id}?encounter_id={id}&token={jwt}
 */
export const startStreamingAudio = async (encounterId, token, onTranscript, onError) => {
    const WS_PROTOCOL = PROTOCOL === 'https' ? 'wss' : 'ws';
    const wsUrl = `${WS_PROTOCOL}://${BASE_URL}/ws/dictation/${encounterId}?token=${token}`;
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

/**
 * Stops audio recording and closes WebSocket.
 * This signals the backend to finalize and save the note.
 */
export const stopStreamingAudio = (ws) => {
    stopAudioStream();
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'User ended dictation');
    }
 };