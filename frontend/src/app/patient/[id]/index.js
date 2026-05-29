// app/patient/[id]/index.js
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView, RefreshControl } from 'react-native';
import { ActivityIndicator, Button, Card, Title, Paragraph } from 'react-native-paper';
import { useLocalSearchParams, useFocusEffect, useRouter } from 'expo-router';
// --- Corrected Import Paths ---
import { useAuth } from '../../../context/AuthContext';
import { apiGetPatientDetails, apiUpdateEncounter, apiCreateEncounter } from '../../../api/api';
import { COLORS, FONTS, SIZES } from '../../../constants/theme';

// Helper function to format dates
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  } catch (error) { return 'Invalid Date'; }
};

export default function PatientSummaryScreen() {
  const { id: patientId } = useLocalSearchParams();
  const { userToken } = useAuth();
  const router = useRouter();

  const [patient, setPatient] = useState(null);
  const [activeEncounter, setActiveEncounter] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch data function
  const loadData = useCallback(async () => {
    if (!userToken || !patientId) return;
    setIsLoading(true);

    try {
      const patientData = await apiGetPatientDetails(patientId, userToken);
      setPatient(patientData);

      // Find the first 'active' encounter
      const encounter = patientData.encounters?.find(
        (e) => e.current_status === 'active'
      );

      if (encounter) {
        setActiveEncounter(encounter);
      } else {
        setActiveEncounter(null); // No active encounter
      }
    } catch (error) {
      Alert.alert("Error", `Could not load patient details: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [userToken, patientId]); // Depend on token and ID

  // useFocusEffect runs every time the screen comes into view
  useFocusEffect(
    useCallback(() => {
      const fetchData = async () => {
        await loadData();
      };
      fetchData();
    }, [loadData])
  );

  // --- Actions ---
  const handleAdmit = async () => {
    if (!activeEncounter) {
      Alert.alert("Error", "No active encounter to admit.");
      return;
    }
    try {
      await apiUpdateEncounter(activeEncounter.id, { current_status: 'active' }, userToken);
      Alert.alert("Success", "Patient marked as Admitted.");
      loadData(); // Refresh data
    } catch (error) {
      Alert.alert("Error", `Could not admit patient: ${error.message}`);
    }
  };

  const handleDischarge = async () => {
    if (!activeEncounter) return;
    try {
      await apiUpdateEncounter(activeEncounter.id, { current_status: 'discharged' }, userToken);
      Alert.alert("Success", "Patient marked as Discharged.");
      loadData(); // Refresh data
    } catch (error) {
      Alert.alert("Error", `Could not discharge patient: ${error.message}`);
    }
  };

  const handleStartEncounter = async () => {
    try {
      // Create a new encounter with 'active' status and 'admission' type
      await apiCreateEncounter({
        patient_id: patientId,
        current_status: 'active',
        encounter_type: 'admission' // Required field
      }, userToken);
      Alert.alert("Success", "New encounter started.");
      loadData(); // Refresh data to show the new encounter
    } catch (error) {
      Alert.alert("Error", `Could not start encounter: ${error.message}`);
    }
  };

  if (isLoading) {
    return (
      <View style={styles.loaderContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={isLoading} onRefresh={loadData} />}
    >
      {/* Patient Info Card */}
      <Card style={styles.card}>
        <Card.Content>
          <Title style={styles.cardTitle}>{patient?.full_name || 'Loading...'}</Title>
          <Paragraph>DOB: {patient?.date_of_birth || 'N/A'}</Paragraph>
          <Paragraph>Contact: {patient?.contact_info || 'N/A'}</Paragraph>
          <Paragraph>Registered: {formatDate(patient?.registration_timestamp)}</Paragraph>
        </Card.Content>
      </Card>

      {/* Active Encounter Card */}
      {activeEncounter ? (
        <>
          <Card style={styles.card}>
            <Card.Content>
              <Title style={styles.cardTitle}>Status: {activeEncounter.current_status}</Title>
              <Paragraph>Admitted: {formatDate(activeEncounter.admitted_at)}</Paragraph>
              <Paragraph>Est. Stay: {activeEncounter.estimated_length_of_stay || 'N/A'}</Paragraph>

              <View style={styles.buttonRow}>
                <Button mode="contained" onPress={handleAdmit} style={styles.button}>Admit</Button>
                <Button mode="outlined" onPress={handleDischarge} style={styles.button}>Discharge</Button>
              </View>

              <Button
                mode="contained"
                icon="microphone"
                style={{ marginTop: SIZES.padding, backgroundColor: COLORS.secondary }}
                onPress={() => router.push({
                  pathname: `/patient/${patientId}/dictation`,
                  params: { encounterId: activeEncounter.id }
                })}
              >
                Dictate Handoff
              </Button>
            </Card.Content>
          </Card>

          <Card style={styles.card}>
            <Card.Content>
              <Title style={styles.cardTitle}>Lab Reports</Title>
              <Paragraph>Status: {activeEncounter.lab_report_status}</Paragraph>
              <Paragraph>Expected: {formatDate(activeEncounter.lab_report_expected_at)}</Paragraph>
            </Card.Content>
          </Card>
        </>
      ) : (
        <Card style={styles.card}>
          <Card.Content>
            <Title>No Active Encounter</Title>
            <Paragraph>This patient is not currently admitted.</Paragraph>
            <Button
              mode="contained"
              onPress={handleStartEncounter}
              style={{ marginTop: 10 }}
            >
              Start New Encounter
            </Button>
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContainer: {
    padding: SIZES.padding,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  card: {
    marginBottom: SIZES.padding,
    backgroundColor: COLORS.surface,
  },
  cardTitle: {
    ...FONTS.h3,
    color: COLORS.primary,
    marginBottom: SIZES.base,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: SIZES.padding,
  },
  button: {
    flex: 1,
    marginHorizontal: SIZES.base / 2,
  },
});