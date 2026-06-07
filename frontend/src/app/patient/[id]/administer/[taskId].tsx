import React from 'react';
import { useLocalSearchParams } from 'expo-router';

import MedicationAdminScreen from '../../../../features/medication/MedicationAdminScreen';

export default function MedicationAdminRoute() {
  const params = useLocalSearchParams<{
    id: string;
    taskId: string;
    patientName?: string;
    dateOfBirth?: string;
    bedNumber?: string;
    drugName?: string;
    dose?: string;
    routeName?: string;
    requiresWitness?: string;
  }>();

  return (
    <MedicationAdminScreen
      bedNumber={params.bedNumber}
      dateOfBirth={params.dateOfBirth}
      dose={params.dose}
      drugName={params.drugName || 'Medication'}
      patientId={params.id}
      patientName={params.patientName || 'Unknown Patient'}
      requiresWitness={params.requiresWitness === 'true'}
      routeName={params.routeName}
      taskId={params.taskId}
    />
  );
}
