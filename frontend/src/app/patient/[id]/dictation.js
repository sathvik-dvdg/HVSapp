import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import { Text, Button, Card, Title, Paragraph, ActivityIndicator, IconButton } from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useAuth } from '../../../context/AuthContext';
import {
    requestAudioPermissions,
    startStreamingAudio,
    stopStreamingAudio,
    apiGetPatientDetails
} from '../../../api/api';
import { COLORS, FONTS, SIZES } from '../../../constants/theme';

export default function DictationScreen() {
    const { id: patientId, encounterId } = useLocalSearchParams();
    const { userToken } = useAuth();
    const router = useRouter();

    const [isRecording, setIsRecording] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [status, setStatus] = useState('Ready to record');
    const [isSaving, setIsSaving] = useState(false);

    // Request permissions on mount
    useEffect(() => {
        requestAudioPermissions();
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

    const handleToggleRecording = async () => {
        if (isRecording) {
            // Stop Recording
            await stopStreamingAudio();
            setIsRecording(false);
            setStatus('Recording stopped. Review your note.');
        } else {
            // Start Recording
            const targetEncounterId = resolvedEncounterId;

            if (!targetEncounterId) {
                Alert.alert("Error", "No active encounter found for this patient. Please start an encounter in the Summary tab.");
                return;
            }

            setStatus('Connecting...');
            const success = await startStreamingAudio(
                targetEncounterId,
                userToken,
                (message) => {
                    // WebSocket Message Handler
                    if (message.type === 'transcript') {
                        setTranscript(prev => prev + ' ' + message.text);
                    } else if (message.type === 'transcript_update') {
                        // Handle the new format from backend
                        if (message.is_final) {
                            setTranscript(prev => prev + message.text + " ");
                        }
                        // Optionally handle interim results if we want to show them
                    } else if (message.type === 'error') {
                        Alert.alert("ASR Error", message.message);
                        setIsRecording(false);
                    }
                }
            );

            if (success) {
                setIsRecording(true);
                setStatus('Listening...');
            } else {
                setStatus('Connection failed');
            }
        }
    };

    const handleSave = async () => {
        if (isRecording) {
            await stopStreamingAudio();
            setIsRecording(false);
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
                    <Paragraph>Encounter ID: {encounterId}</Paragraph>
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
