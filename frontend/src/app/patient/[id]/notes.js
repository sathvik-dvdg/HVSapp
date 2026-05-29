// app/patient/[id]/notes.js
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView, RefreshControl } from 'react-native';
import { ActivityIndicator, Card, Title, Paragraph, FAB } from 'react-native-paper';
import { useLocalSearchParams, useFocusEffect, useRouter } from 'expo-router';
// --- Corrected Import Paths ---
import { useAuth } from '../../../context/AuthContext';
import { apiGetPatientDetails, apiGetEncounterNotes } from '../../../api/api';
import { COLORS, FONTS, SIZES } from '../../../constants/theme';

// Helper to format dates
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('en-US', {
    dateStyle: 'medium', timeStyle: 'short'
  });
};

// --- Added export default ---
export default function PatientNotesScreen() {
  const { id: patientId } = useLocalSearchParams();
  const { userToken } = useAuth();
  const router = useRouter();

  const [notes, setNotes] = useState([]);
  const [encounterId, setEncounterId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch data function
  const loadNotes = useCallback(async () => {
    if (!userToken || !patientId) return;
    setIsLoading(true);

    try {
      // Find the active encounter ID
      const patient = await apiGetPatientDetails(patientId, userToken);
      const activeEncounter = patient.encounters?.find(
        (e) => e.current_status === 'active'
      );

      if (activeEncounter) {
        setEncounterId(activeEncounter.id);
        // Fetch notes for that encounter
        const noteData = await apiGetEncounterNotes(activeEncounter.id, userToken);
        setNotes(noteData || []);
      } else {
        setNotes([]);
      }
    } catch (error) {
      Alert.alert("Error", `Could not load clinical notes: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [userToken, patientId]);

  // useFocusEffect runs every time the screen comes into view
  useFocusEffect(
    useCallback(() => {
      const fetchData = async () => {
        await loadNotes();
      };
      fetchData();
    }, [loadNotes])
  );

  const handleStartDictation = () => {
    if (!encounterId) {
      Alert.alert("Error", "Cannot start dictation, no active encounter found.");
      return;
    }
    // Navigate to a new screen for dictation (we'll create this next)
    router.push({
      pathname: `/patient/${patientId}/dictation`, // This route needs to be created
      params: { encounterId: encounterId }
    });
  };

  if (isLoading) {
    return (
      <View style={styles.loaderContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContainer}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={loadNotes} />
        }
      >
        {notes.length === 0 ? (
          <Text style={styles.emptyText}>No clinical notes found for this encounter.</Text>
        ) : (
          notes.map((note) => (
            <Card style={styles.card} key={note.id}>
              <Card.Title
                title={`Note #${note.id} (${note.note_type})`}
                subtitle={`By Author ${note.author_id} on ${formatDate(note.created_at)}`}
                titleStyle={styles.cardTitle}
                subtitleStyle={styles.cardSubtitle}
              />
              <Card.Content>
                <Paragraph style={styles.noteContent}>{note.content}</Paragraph>
              </Card.Content>
            </Card>
          ))
        )}
      </ScrollView>

      {/* Floating Action Button to add a new note */}
      <FAB
        style={styles.fab}
        icon="microphone-plus"
        color={COLORS.white}
        onPress={handleStartDictation}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scrollContainer: { padding: SIZES.padding },
  loaderContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  card: { marginBottom: SIZES.padding, backgroundColor: COLORS.surface },
  cardTitle: { ...FONTS.h4, color: COLORS.primary, fontWeight: 'bold' },
  cardSubtitle: { fontSize: 12, color: COLORS.textLight },
  noteContent: { ...FONTS.body, color: COLORS.text, marginTop: SIZES.base },
  emptyText: { ...FONTS.body, color: COLORS.textLight, textAlign: 'center', marginTop: 50 },
  fab: {
    position: 'absolute', margin: 16, right: 0, bottom: 0, backgroundColor: COLORS.primary,
  },
});