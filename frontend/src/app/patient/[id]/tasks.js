// app/patient/[id]/tasks.js
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView, RefreshControl } from 'react-native';
import { ActivityIndicator, Card, Checkbox, FAB } from 'react-native-paper';
import { useLocalSearchParams, useFocusEffect, useRouter } from 'expo-router';
// --- Corrected Import Paths ---
import { useAuth } from '../../../context/AuthContext';
import { apiGetPatientDetails, apiGetEncounterTasks, apiCompleteTask } from '../../../api/api';
import { COLORS, FONTS, SIZES } from '../../../constants/theme';

// Helper to format dates
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('en-US', {
    dateStyle: 'medium', timeStyle: 'short'
  });
};

// --- Added export default ---
export default function PatientTasksScreen() {
  const { id: patientId } = useLocalSearchParams();
  const { userToken } = useAuth();
  const router = useRouter();

  const [tasks, setTasks] = useState([]);
  const [encounterId, setEncounterId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch or re-fetch data
  const loadTasks = useCallback(async () => {
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
        // Fetch Tasks for that Encounter
        const taskData = await apiGetEncounterTasks(activeEncounter.id, userToken);
        setTasks(taskData || []);
      } else {
        setTasks([]);
      }
    } catch (error) {
      Alert.alert("Error", `Could not load tasks: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [userToken, patientId]);

  useFocusEffect(
    useCallback(() => {
      const fetchData = async () => {
        await loadTasks();
      };
      fetchData();
    }, [loadTasks])
  );

  // Handle Task Completion
  const handleCompleteTask = async (taskId) => {
    Alert.alert("Complete Task", "Are you sure?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Complete",
          onPress: async () => {
            try {
              await apiCompleteTask(taskId, userToken);
              Alert.alert("Success", "Task marked as complete.");
              loadTasks(); // Refresh list
            } catch (error) {
              Alert.alert("Error", `Could not complete task: ${error.message}`);
            }
          }
        }
      ]
    );
  };

  const handleCreateTask = () => {
    if (!encounterId) return;
    router.push({
      pathname: '/patient/createTask', // This route needs to be created
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
          <RefreshControl refreshing={isLoading} onRefresh={loadTasks} />
        }
      >
        {tasks.length === 0 ? (
          <Text style={styles.emptyText}>No tasks found for this encounter.</Text>
        ) : (
          tasks.map((task) => (
            <Card style={styles.card} key={task.id}>
              <Card.Title
                title={task.description}
                titleNumberOfLines={3}
                titleStyle={styles.cardTitle}
                subtitle={`Status: ${task.status} | Due: ${formatDate(task.due_at)}`}
                subtitleStyle={styles.cardSubtitle}
                right={() => (
                  <Checkbox.Android
                    status={task.status === 'completed' ? 'checked' : 'unchecked'}
                    onPress={() => task.status !== 'completed' && handleCompleteTask(task.id)}
                    color={COLORS.primary}
                    disabled={task.status === 'completed'}
                  />
                )}
                rightStyle={styles.checkbox}
              />
              {task.completed_at && (
                <Card.Content>
                  <Text style={styles.completedText}>
                    Completed: {formatDate(task.completed_at)}
                  </Text>
                </Card.Content>
              )}
            </Card>
          ))
        )}
      </ScrollView>

      <FAB
        style={styles.fab}
        icon="plus"
        color={COLORS.white}
        onPress={handleCreateTask}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  scrollContainer: { padding: SIZES.padding, paddingBottom: 80 },
  loaderContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  card: { marginBottom: SIZES.padding, backgroundColor: COLORS.surface },
  cardTitle: { ...FONTS.h4, color: COLORS.text, fontWeight: 'bold' },
  cardSubtitle: { fontSize: 12, color: COLORS.textLight, marginTop: 4 },
  completedText: { fontSize: 12, color: COLORS.success, fontStyle: 'italic', marginTop: 4 },
  checkbox: { paddingRight: SIZES.padding },
  emptyText: { ...FONTS.body, color: COLORS.textLight, textAlign: 'center', marginTop: 50 },
  fab: {
    position: 'absolute', margin: 16, right: 0, bottom: 0, backgroundColor: COLORS.primary,
  },
});