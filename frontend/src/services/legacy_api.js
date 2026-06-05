import { startAudioStream, stopAudioStream } from '../features/handoff/audioStream';

// Use environment variable, fallback to localhost
const BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000';
// Strip http:// or https:// for WebSocket
const WS_BASE_URL = BASE_URL.replace(/^http/, 'ws');

export const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    // UPDATED to point to the new Phase 1 auth endpoint
    const response = await fetch(`${BASE_URL}/api/v1/auth/token`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
    });

    if (!response.ok) {
        throw new Error('Login failed');
    }

    return await response.json();
};

export const fetchWithToken = async (endpoint, token, options = {}) => {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });

    if (!response.ok) {
        if (response.status === 401) {
            console.error("Token expired or invalid.");
            throw new Error("Unauthorized");
        }
        throw new Error(`API Error: ${response.status}`);
    }

    return await response.json();
};

export const startStreamingAudio = async (encounterId, token, onTranscript, onError) => {
    const wsUrl = `${WS_BASE_URL}/ws/dictation/${encounterId}?token=${token}`;
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
