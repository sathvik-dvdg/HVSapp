import React, { useMemo, useState } from 'react';
import {
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Button } from 'react-native-paper';
import { useRouter } from 'expo-router';

import { apiAdministerMedicationTask } from '../../services/api';
import { COLORS, SIZES } from '../../shared/constants/theme';

type MedicationAdminScreenProps = {
  patientId: string;
  taskId: string;
  patientName: string;
  dateOfBirth?: string | null;
  bedNumber?: string | null;
  drugName: string;
  dose?: string | null;
  routeName?: string | null;
  requiresWitness?: boolean;
};

const formatDateOfBirth = (dateOfBirth?: string | null): string => {
  if (!dateOfBirth) {
    return 'Unknown';
  }
  try {
    return new Date(dateOfBirth).toLocaleDateString();
  } catch {
    return dateOfBirth;
  }
};

export default function MedicationAdminScreen({
  patientId,
  taskId,
  patientName,
  dateOfBirth,
  bedNumber,
  drugName,
  dose,
  routeName,
  requiresWitness = false,
}: MedicationAdminScreenProps) {
  const router = useRouter();
  const [patientVerified, setPatientVerified] = useState(false);
  const [drugNameConfirmation, setDrugNameConfirmation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [witnessId, setWitnessId] = useState('');
  const [witnessModalVisible, setWitnessModalVisible] = useState(false);

  const drugConfirmed = useMemo(
    () => drugNameConfirmation.trim().toLowerCase() === drugName.trim().toLowerCase(),
    [drugName, drugNameConfirmation]
  );

  const submitAdministration = async () => {
    setIsSubmitting(true);
    try {
      await apiAdministerMedicationTask(Number(taskId), {
        patient_verified: true,
        drug_name_confirmed: true,
        witness_id: witnessId ? Number(witnessId) : null,
      });
      Alert.alert('Medication Administered', 'The medication task has been recorded successfully.', [
        { text: 'OK', onPress: () => router.back() },
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to administer medication.';
      Alert.alert('Administration Failed', message);
    } finally {
      setIsSubmitting(false);
      setWitnessModalVisible(false);
    }
  };

  const handleFinalConfirmation = () => {
    if (requiresWitness && !witnessId.trim()) {
      setWitnessModalVisible(true);
      return;
    }
    void submitAdministration();
  };

  const handleAdministerPress = () => {
    Alert.alert(
      'Confirm Medication',
      `Confirm the right patient, medication, dose, and route for ${drugName}.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Continue',
          onPress: () => {
            Alert.alert(
              'Final Clinical Confirmation',
              'This will record the medication as administered. Continue only if administration is complete.',
              [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: requiresWitness ? 'Witness Required' : 'Administer',
                  onPress: () => {
                    if (requiresWitness) {
                      setWitnessModalVisible(true);
                    } else {
                      handleFinalConfirmation();
                    }
                  },
                },
              ]
            );
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.heading}>Medication Administration</Text>
        <Text style={styles.subheading}>Patient ID: {patientId}</Text>

        <View style={styles.card}>
          <Text style={styles.stepTitle}>Step 1: Verify Patient Identity</Text>
          <Text style={styles.patientName}>{patientName}</Text>
          <Text style={styles.detailText}>DOB: {formatDateOfBirth(dateOfBirth)}</Text>
          <Text style={styles.detailText}>Bed: {bedNumber || 'Unassigned'}</Text>
          <Pressable
            accessibilityRole="checkbox"
            onPress={() => setPatientVerified((currentValue) => !currentValue)}
            style={styles.checkboxRow}
          >
            <View style={[styles.checkbox, patientVerified && styles.checkboxChecked]} />
            <Text style={styles.checkboxLabel}>I have verified patient identity</Text>
          </Pressable>
        </View>

        <View style={styles.card}>
          <Text style={styles.stepTitle}>Step 2: Confirm Medication</Text>
          <Text style={styles.detailText}>Medication: {drugName}</Text>
          <Text style={styles.detailText}>Dose: {dose || 'Not specified'}</Text>
          <Text style={styles.detailText}>Route: {routeName || 'Not specified'}</Text>
          <TextInput
            autoCapitalize="none"
            editable={patientVerified}
            onChangeText={setDrugNameConfirmation}
            placeholder="Retype medication name exactly"
            placeholderTextColor="#7D8A99"
            style={[styles.input, !patientVerified && styles.inputDisabled]}
            value={drugNameConfirmation}
          />
          <Text style={styles.helperText}>
            Retype <Text style={styles.helperStrong}>{drugName}</Text> exactly before administering.
          </Text>
        </View>

        <Button
          mode="contained"
          disabled={!patientVerified || !drugConfirmed || isSubmitting}
          loading={isSubmitting}
          onPress={handleAdministerPress}
          style={styles.submitButton}
        >
          Administer Medication
        </Button>
      </ScrollView>

      <Modal animationType="slide" transparent visible={witnessModalVisible}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.stepTitle}>Witness Confirmation</Text>
            <Text style={styles.detailText}>
              Enter the active nurse or doctor witness ID for this controlled substance.
            </Text>
            <TextInput
              keyboardType="number-pad"
              onChangeText={setWitnessId}
              placeholder="Witness user ID"
              placeholderTextColor="#7D8A99"
              style={styles.input}
              value={witnessId}
            />
            <View style={styles.modalButtons}>
              <Button mode="text" onPress={() => setWitnessModalVisible(false)}>
                Cancel
              </Button>
              <Button mode="contained" disabled={!witnessId.trim() || isSubmitting} onPress={handleFinalConfirmation}>
                Confirm Witness
              </Button>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: SIZES.padding,
    gap: SIZES.padding,
  },
  heading: {
    fontSize: SIZES.h2,
    fontWeight: '700',
    color: COLORS.primary,
  },
  subheading: {
    fontSize: SIZES.body,
    color: COLORS.textLight,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.radius,
    padding: SIZES.padding,
    gap: SIZES.base,
  },
  stepTitle: {
    fontSize: SIZES.h3,
    fontWeight: '600',
    color: COLORS.text,
  },
  patientName: {
    fontSize: SIZES.h2,
    fontWeight: '700',
    color: COLORS.primary,
  },
  detailText: {
    fontSize: SIZES.body,
    color: COLORS.text,
  },
  checkboxRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: SIZES.base,
    marginTop: SIZES.base,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: COLORS.primary,
  },
  checkboxChecked: {
    backgroundColor: COLORS.primary,
  },
  checkboxLabel: {
    fontSize: SIZES.body,
    color: COLORS.text,
    flex: 1,
  },
  input: {
    backgroundColor: '#FFFFFF',
    borderColor: COLORS.border,
    borderRadius: SIZES.radius,
    borderWidth: 1,
    color: COLORS.text,
    paddingHorizontal: SIZES.padding,
    paddingVertical: SIZES.base,
  },
  inputDisabled: {
    backgroundColor: '#E9ECEF',
  },
  helperText: {
    fontSize: SIZES.body,
    color: COLORS.textLight,
  },
  helperStrong: {
    fontWeight: '700',
  },
  submitButton: {
    marginTop: SIZES.base,
  },
  modalBackdrop: {
    alignItems: 'center',
    backgroundColor: 'rgba(0, 0, 0, 0.45)',
    flex: 1,
    justifyContent: 'center',
    padding: SIZES.padding,
  },
  modalCard: {
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.radius,
    gap: SIZES.padding,
    padding: SIZES.padding,
    width: '100%',
  },
  modalButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: SIZES.base,
  },
});
