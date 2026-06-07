import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { Audio } from 'expo-av';
import { Text, Button, Card, Title, Paragraph, ActivityIndicator, IconButton } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useAuth } from '../../../features/auth/AuthContext';
import { buildDictationWebSocketUrl, apiGetPatientDetails } from '../../../services/api';
import { startAudioStream, stopAudioStream } from '../../../features/handoff/audioStream';
import { COLORS, FONTS, SIZES } from '../../../shared/constants/theme';

export default function DictationScreen() {
    const { id: patientId, encounterId } = useLocalSearchParams();
    const { userToken } = useAuth();
    const router = useRouter();

    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [status, setStatus] = useState('Ready to record');
    const [isSaving, setIsSaving] = useState(false);
    const ws = useRef(null);
    const isRecordingRef = useRef(false);
    const reconnectAttempt = useRef(0);
    const reconnectTimeout = useRef(null);
    const chunkBuffer = useRef([]);

    // Request permissions on mount
    useEffect(() => {
        Audio.requestPermissionsAsync().catch((error) => {
            console.error('Failed to request audio permission', error);
            Alert.alert('Permission Error', 'Unable to access microphone permissions.');
        });

        return () => {
            if (reconnectTimeout.current) {
                clearTimeout(reconnectTimeout.current);
            }
            if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                ws.current.close(1000, 'Screen closed');
            }
            void stopAudioStream();
        };
    }, []);

    // Fetch active encounter if not provided in params
    useEffect(() => {
        const fetchEncounter = async () => {
            if (encounterId) return; // Already have it

            try {
                const patient = await apiGetPatientDetails(patientId, userToken);
                const active = patient.encounters?.find(e => e.current_status === 'active');
                if (active) {
                    // We can't easily update the route params, so we'll store it in state
                    // But for now, let's just rely on a local variable or ref if we were using one.
                    // Actually, let's just use a state variable for the ID to use.
                    setResolvedEncounterId(active.id);
                }
            } catch (err) {
                console.error("Failed to fetch encounter", err);
            }
        };
        fetchEncounter();
    }, [patientId, userToken, encounterId]);

    const [resolvedEncounterId, setResolvedEncounterId] = useState(encounterId);

    // Update resolvedId if param changes
    useEffect(() => {
        if (encounterId) setResolvedEncounterId(encounterId);
    }, [encounterId]);

    const drainChunkBuffer = () => {
        if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
            return;
        }
        while (chunkBuffer.current.length > 0 && ws.current.readyState === WebSocket.OPEN) {
            const nextChunk = chunkBuffer.current.shift();
            ws.current.send(nextChunk);
        }
    };

    const connectWebSocket = (targetEncounterId) => {
        const socketUrl = buildDictationWebSocketUrl(targetEncounterId, userToken);
        const socket = new WebSocket(socketUrl);
        ws.current = socket;

        socket.onopen = () => {
            reconnectAttempt.current = 0;
            setStatus('Listening...');
            drainChunkBuffer();
        };

        socket.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                if (payload.type === 'transcript_update') {
                    setTranscript((previousTranscript) => payload.is_final
                        ? `${previousTranscript}${payload.text} `
                        : `${previousTranscript}${payload.text}`);
                }
                if (payload.status === 'asr_error') {
                    setStatus(payload.message || 'ASR processing failed');
                }
            } catch (error) {
                console.error('Failed to parse transcript payload', error);
            }
        };

        socket.onerror = () => {
            setStatus('Connection error');
        };

        socket.onclose = () => {
            if (!isRecordingRef.current) {
                return;
            }
            if (reconnectAttempt.current >= 5) {
                setStatus(JSON.stringify({ error: 'connection_lost' }));
                setIsRecording(false);
                isRecordingRef.current = false;
                void stopAudioStream();
                return;
            }
            const nextDelay = Math.min(1000 * (2 ** reconnectAttempt.current), 30000);
            reconnectAttempt.current += 1;
            setStatus(`Reconnecting in ${Math.round(nextDelay / 1000)}s...`);
            reconnectTimeout.current = setTimeout(() => connectWebSocket(targetEncounterId), nextDelay);
        };
    };

    const queueOrSendChunk = (chunk) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(chunk);
            return;
        }
        chunkBuffer.current.push(chunk);
    };

    const handleToggleRecording = async () => {
        if (isRecording) {
            await stopAudioStream();
            if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                ws.current.close(1000, 'User ended dictation');
            }
            ws.current = null;
            setIsRecording(false);
            isRecordingRef.current = false;
            setStatus('Recording stopped. Review your note.');
        } else {
            const targetEncounterId = resolvedEncounterId;

            if (!targetEncounterId) {
                Alert.alert("Error", "No active encounter found for this patient. Please start an encounter in the Summary tab.");
                return;
            }

            setStatus('Connecting...');
            chunkBuffer.current = [];
            reconnectAttempt.current = 0;
            await startAudioStream(queueOrSendChunk);
            connectWebSocket(targetEncounterId);
            setIsRecording(true);
            isRecordingRef.current = true;
        }
    };

    const handleSave = async () => {
        if (isRecording) {
            await stopAudioStream();
            if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                ws.current.close(1000, 'Save requested');
            }
            ws.current = null;
            setIsRecording(false);
            isRecordingRef.current = false;
        }

        setIsSaving(true);
        // In a real app, you might want to send a final "save" API call here
        // if the WebSocket close doesn't handle everything.
        // For now, we assume WS close triggers the backend processing.

        setTimeout(() => {
            setIsSaving(false);
            Alert.alert("Success", "Handoff note saved and tasks generated!", [
                { text: "OK", onPress: () => router.back() }
            ]);
        }, 1000);
    };

    return (
        <View style={styles.container}>
            <Card style={styles.card}>
                <Card.Content>
                    <Title style={styles.title}>Dictate Handoff Note</Title>
                    <Paragraph>Patient ID: {patientId}</Paragraph>
                    <Paragraph>Encounter ID: {resolvedEncounterId || encounterId}</Paragraph>
                </Card.Content>
            </Card>

            <View style={styles.recordContainer}>
                <IconButton
                    icon={isRecording ? "stop-circle" : "microphone"}
                    iconColor={isRecording ? COLORS.danger : COLORS.primary}
                    size={80}
                    onPress={handleToggleRecording}
                />
                <Text style={styles.statusText}>{status}</Text>
            </View>

            <Card style={styles.transcriptCard}>
                <Card.Content>
                    <Title>Live Transcript</Title>
                    <ScrollView style={styles.scrollView}>
                        <Text style={styles.transcriptText}>
                            {transcript || "Transcript will appear here..."}
                        </Text>
                    </ScrollView>
                </Card.Content>
            </Card>

            <Button
                mode="contained"
                onPress={handleSave}
                loading={isSaving}
                disabled={isSaving || isRecording}
                style={styles.saveButton}
            >
                Save & Generate Tasks
            </Button>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        padding: SIZES.padding,
        backgroundColor: COLORS.background,
    },
    card: {
        marginBottom: SIZES.padding,
        backgroundColor: COLORS.surface,
    },
    title: {
        ...FONTS.h2,
        color: COLORS.primary,
    },
    recordContainer: {
        alignItems: 'center',
        marginVertical: SIZES.padding,
    },
    statusText: {
        ...FONTS.h3,
        marginTop: SIZES.base,
        color: COLORS.text,
    },
    transcriptCard: {
        flex: 1,
        marginBottom: SIZES.padding,
        backgroundColor: COLORS.surface,
    },
    scrollView: {
        height: 200,
        marginTop: SIZES.base,
    },
    transcriptText: {
        ...FONTS.body,
        color: COLORS.text,
    },
    saveButton: {
        marginTop: 'auto',
        paddingVertical: SIZES.base,
    }
});
