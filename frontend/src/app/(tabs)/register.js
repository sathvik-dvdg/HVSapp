// app/(tabs)/register.js
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { TextInput, Button } from 'react-native-paper';
import { useAuth } from '../../context/AuthContext';
import { apiRegisterPatient, apiCreateEncounter } from '../../api/api';
import { COLORS, FONTS, SIZES } from '../../constants/theme';
import { useRouter } from 'expo-router';

export default function RegisterPatientScreen() {
  const { userToken } = useAuth();
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  // Patient Fields
  const [fullName, setFullName] = useState('');
  const [dob, setDob] = useState(''); // Date of Birth (YYYY-MM-DD)
  const [contactInfo, setContactInfo] = useState('');

  // Triage Field
  const [triageNotes, setTriageNotes] = useState(''); // Placeholder, as backend doesn't store this yet

  const handleRegisterPatient = async () => {
    if (!fullName) {
      Alert.alert('Error', 'Patient Full Name is required.');
      return;
    }

    setIsLoading(true);
    try {
      // --- Step 1: Register the Patient ---
      const patientData = {
        full_name: fullName,
        date_of_birth: dob || null,
        contact_info: contactInfo || null,
      };

      const patientResult = await apiRegisterPatient(patientData, userToken);
      if (!patientResult || !patientResult.id) {
        throw new Error('Failed to register patient or received invalid response.');
      }

      console.log('Patient registered:', patientResult.id);

      // --- Step 2: Create their initial Triage Encounter ---
      const encounterData = {
        patient_id: patientResult.id,
        encounter_type: 'triage', // Set type as 'triage'
      };

      const encounterResult = await apiCreateEncounter(encounterData, userToken);
      if (!encounterResult || !encounterResult.id) {
        throw new Error('Patient was registered, but failed to create their encounter.');
      }

      console.log('Encounter created:', encounterResult.id);

      // --- Success ---
      Alert.alert(
        'Success',
        `Patient ${patientResult.full_name} (ID: ${patientResult.id}) has been registered and a triage encounter (ID: ${encounterResult.id}) is open.`
      );

      // Clear form
      setFullName('');
      setDob('');
      setContactInfo('');
      setTriageNotes('');

      // Navigate to the new patient's detail page
      router.push(`/patient/${patientResult.id}`);

    } catch (error) {
      Alert.alert('Registration Failed', error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <Text style={styles.title}>New Patient Registration</Text>
        
        <TextInput
          label="Full Name"
          style={styles.input}
          value={fullName}
          onChangeText={setFullName}
          autoCapitalize="words"
          mode="outlined"
          theme={{ roundness: SIZES.radius }}
        />
        <TextInput
          label="Date of Birth (YYYY-MM-DD)"
          style={styles.input}
          value={dob}
          onChangeText={setDob}
          keyboardType="numeric"
          mode="outlined"
          theme={{ roundness: SIZES.radius }}
        />
        <TextInput
          label="Contact Info (Phone/Address)"
          style={styles.input}
          value={contactInfo}
          onChangeText={setContactInfo}
          mode="outlined"
          theme={{ roundness: SIZES.radius }}
        />
        
        <TextInput
          label="Initial Triage Notes (Optional)"
          style={styles.input}
          value={triageNotes}
          onChangeText={setTriageNotes}
          multiline
          numberOfLines={4}
          mode="outlined"
          theme={{ roundness: SIZES.radius }}
        />

        <Button
          mode="contained"
          onPress={handleRegisterPatient}
          loading={isLoading}
          disabled={isLoading}
          style={styles.button}
          labelStyle={styles.buttonLabel}
        >
          {isLoading ? 'Registering...' : 'Register Patient & Start Encounter'}
        </Button>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// Styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContainer: {
    padding: SIZES.padding,
  },
  title: {
    ...FONTS.h2,
    color: COLORS.primary,
    textAlign: 'center',
    marginBottom: SIZES.paddingLarge,
  },
  input: {
    marginBottom: SIZES.padding,
  },
  button: {
    paddingVertical: SIZES.base,
    marginTop: SIZES.padding,
    borderRadius: SIZES.radius,
  },
  buttonLabel: {
    fontSize: 16,
    fontWeight: 'bold',
  }
});