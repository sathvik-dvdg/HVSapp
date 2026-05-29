import { Audio } from 'expo-av'; // For permission requests
import { Alert } from 'react-native';

//
// --- 1. BASE URL CONFIGURATION (CRITICAL!) ---
//
// THIS IS THE MOST IMPORTANT LINE.
// Replace '192.168.X.X' with your backend computer's local IP address.
// You CANNOT use 'http://127.0.0.1:8000' if running on a real device.
//
const BASE_URL = 'http://10.19.73.68:8000'; // Updated to machine IP for Android access
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

        const response = await fetch(`${BASE_URL}/api/v1/login/token`, {
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
    const url = `${BASE_URL}${endpoint}`;
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


// --- Audio Recording & WebSocket Logic ---

let audioSocket = null;
let audioRecording = null;

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
export const startStreamingAudio = async (encounterId, token, onMessageReceived) => {
    if (audioSocket || audioRecording) {
        console.warn('Streaming already in progress.');
        return false;
    }
    console.log(`Starting audio stream for encounter ${encounterId}...`);

    try {
        // 1. Connect WebSocket (Add token to URL)
        const sessionId = Date.now().toString();
        // Replace 'http' with 'ws' for the WebSocket protocol
        const websocketUrl = `${BASE_URL.replace('http', 'ws')}/ws/dictation/${sessionId}?encounter_id=${encounterId}&token=${token}`;
        console.log('Connecting to WebSocket:', websocketUrl);

        audioSocket = new WebSocket(websocketUrl);

        audioSocket.onopen = async () => {
            console.log('WebSocket Connected! Starting recording...');
            // 2. Prepare Audio Recording 
            await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
            audioRecording = new Audio.Recording();

            // --- CRITICAL AUDIO CONFIG ---
            // This MUST match the backend's ASR_RATE_HZ (16000)
            await audioRecording.prepareToRecordAsync({
                isMeteringEnabled: true,
                android: {
                    extension: '.pcm',
                    outputFormat: Audio.RECORDING_OPTION_ANDROID_OUTPUT_FORMAT_PCM_16BIT,
                    audioEncoder: Audio.RECORDING_OPTION_ANDROID_AUDIO_ENCODER_PCM_16BIT,
                    sampleRate: 16000,
                    numberOfChannels: 1,
                },
                ios: {
                    extension: '.wav',
                    audioQuality: Audio.RECORDING_OPTION_IOS_AUDIO_QUALITY_LOW,
                    sampleRate: 16000,
                    numberOfChannels: 1,
                    linearPCMBitDepth: 16,
                    linearPCMIsBigEndian: false,
                    linearPCMIsFloat: false,
                },
            });

            // 3. Set up the streaming callback
            // NOTE: expo-av is not a true streaming library.
            // This is a placeholder. For real streaming, you'd use a different
            // library or custom native code to send chunks.
            // For now, the connection is open and the backend is waiting.
            audioRecording.setOnRecordingStatusUpdate((status) => {
                // (Placeholder for actual streaming logic)
            });

            await audioRecording.startAsync();
            console.log('Recording started! (Note: True streaming not yet implemented)');
        };

        audioSocket.onmessage = (event) => {
            // This callback receives messages from the backend (live transcript, errors, etc.)
            console.log('WS Message:', event.data);
            try {
                const message = JSON.parse(event.data);
                onMessageReceived(message); // Pass message to the React component
            } catch (e) { console.error("WS parse error:", e); }
        };

        audioSocket.onerror = (e) => {
            console.error('WebSocket Error:', e.message);
            Alert.alert('Connection Error', 'Live dictation connection failed.');
        };

        audioSocket.onclose = (e) => {
            console.log('WebSocket Closed:', e.code, e.reason);
            // Auto-stop recording if WS closes
            if (audioRecording) stopStreamingAudio();
        };

        return true;
    } catch (err) {
        console.error('Failed to start streaming', err);
        Alert.alert('Error', `Could not start stream: ${err.message}`);
        // Clean up resources if failed
        if (audioRecording) await audioRecording.stopAndUnloadAsync();
        if (audioSocket) audioSocket.close();
        audioRecording = null;
        audioSocket = null;
        await Audio.setAudioModeAsync({ allowsRecordingIOS: false });
        return false;
    }
};

/**
 * Stops audio recording and closes WebSocket.
 * This signals the backend to finalize and save the note.
 */
export const stopStreamingAudio = async () => {
    console.log('Stopping audio stream...');

    // --- 1. Stop Recording ---
    if (audioRecording) {
        try {
            await audioRecording.stopAndUnloadAsync();
            console.log('Recording stopped.');
        } catch (err) {
            console.error('Failed to stop recording', err);
        }
    }

    // --- 2. Close WebSocket (This triggers the backend to save the note) ---
    if (audioSocket) {
        try {
            audioSocket.close(1000, "Client stopped recording"); // 1000 = Normal closure
        } catch (e) { console.error("Error closing WebSocket:", e); }
    }

    // Reset state
    audioRecording = null;
    audioSocket = null;
    await Audio.setAudioModeAsync({ allowsRecordingIOS: false });
};