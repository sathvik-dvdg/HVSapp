import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useAuth } from '../../../features/auth/AuthContext';
import { apiGetMedicationTasks } from '../../../services/api';

export default function MedicationTasksScreen() {
    const { id: patientId } = useLocalSearchParams();
    const { token, userRole } = useAuth();
    const router = useRouter();
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchTasks = async () => {
        try {
            const data = await apiGetMedicationTasks(patientId);
            setTasks(data);
        } catch (error) {
            Alert.alert("Error", error.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTasks();
    }, [patientId]);

    const handleAdminister = (taskId) => {
        const selectedTask = tasks.find((task) => task.id === taskId);
        router.push({
            pathname: `/patient/${patientId}/administer/${taskId}`,
            params: {
                patientName: selectedTask?.patient_name || 'Unknown Patient',
                dateOfBirth: selectedTask?.patient_date_of_birth || '',
                bedNumber: selectedTask?.bed_number || '',
                drugName: selectedTask?.drug_name || 'Medication',
                dose: selectedTask?.dose || '',
                routeName: selectedTask?.route || '',
                requiresWitness: 'false',
            },
        });
    };

    const handleSkip = (taskId) => {
        Alert.alert("Unsupported", "Skipping medication tasks is not available in this build.");
    };

    const renderTask = ({ item }) => {
        const isPending = item.status === 'pending';
        const isNurse = userRole === 'nurse' || userRole === 'admin';

        return (
            <View style={styles.card}>
                <View style={styles.headerRow}>
                    <Text style={styles.time}>Scheduled: {new Date(item.scheduled_at || item.scheduled_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</Text>
                    <Text style={[styles.statusBadge, { backgroundColor: isPending ? '#FF9800' : (item.status === 'administered' ? '#4CAF50' : '#F44336') }]}>
                        {item.status.toUpperCase()}
                    </Text>
                </View>
                
                {item.notes && <Text style={styles.notes}>Notes: {item.notes}</Text>}
                
                {isPending && isNurse && (
                    <View style={styles.buttonRow}>
                        <TouchableOpacity style={[styles.button, styles.administerBtn]} onPress={() => handleAdminister(item.id)}>
                            <Text style={styles.buttonText}>Administer</Text>
                        </TouchableOpacity>
                        <TouchableOpacity style={[styles.button, styles.skipBtn]} onPress={() => handleSkip(item.id)}>
                            <Text style={styles.buttonText}>Skip</Text>
                        </TouchableOpacity>
                    </View>
                )}
            </View>
        );
    };

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#007BFF" />
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <Text style={styles.header}>Medication Schedule</Text>
            <FlatList 
                data={tasks}
                keyExtractor={(item) => item.id.toString()}
                renderItem={renderTask}
                ListEmptyComponent={<Text style={styles.empty}>No medications scheduled for this patient.</Text>}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 16, backgroundColor: '#F8F9FA' },
    centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    header: { fontSize: 22, fontWeight: 'bold', marginBottom: 16, color: '#333' },
    card: { backgroundColor: 'white', padding: 16, borderRadius: 10, marginBottom: 12, elevation: 3, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4, shadowOffset: { width: 0, height: 2 } },
    headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
    time: { fontSize: 16, fontWeight: '600', color: '#444' },
    statusBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, color: 'white', fontSize: 12, fontWeight: 'bold', overflow: 'hidden' },
    notes: { fontSize: 14, color: '#666', fontStyle: 'italic', marginBottom: 8 },
    buttonRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 12 },
    button: { paddingVertical: 10, borderRadius: 6, flex: 0.48, alignItems: 'center' },
    administerBtn: { backgroundColor: '#28A745' },
    skipBtn: { backgroundColor: '#DC3545' },
    buttonText: { color: 'white', fontWeight: 'bold', fontSize: 14 },
    empty: { textAlign: 'center', marginTop: 40, color: '#888', fontSize: 16 }
});
