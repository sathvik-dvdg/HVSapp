// app/(tabs)/dashboard.js
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, Alert } from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { apiGetCriticalAlerts, apiGetMyTasks } from '../../api/api';
import { Appbar, Card, Title, Paragraph, ActivityIndicator, Button } from 'react-native-paper';
import { COLORS, FONTS, SIZES } from '../../constants/theme';
import { Link } from 'expo-router'; // Use Link for navigation

export default function DashboardScreen() {
  const { userToken, userRole, signOut } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [alerts, setAlerts] = useState(null);
  const [myTasks, setMyTasks] = useState([]);

  // Function to fetch all necessary data
  const fetchData = async () => {
    if (!userToken) {
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      // Everyone gets critical alerts
      const alertData = await apiGetCriticalAlerts(userToken);
      setAlerts(alertData);

      // Only nurses get "My Tasks"
      if (userRole === 'nurse') {
        const taskData = await apiGetMyTasks(userToken);
        setMyTasks(taskData);
      }
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
      Alert.alert("Error", "Could not load dashboard data.");
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch data on initial load
  useEffect(() => {
    fetchData();
  }, [userToken, userRole]); // Refetch if user changes

  if (isLoading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Appbar.Header style={{ backgroundColor: COLORS.surface }}>
        <Appbar.Content title="Dashboard" titleStyle={styles.headerTitle} />
        <Appbar.Action icon="logout" color={COLORS.primary} onPress={signOut} />
      </Appbar.Header>

      <ScrollView
        contentContainerStyle={styles.scrollContainer}
        refreshControl={
          <RefreshControl refreshing={isLoading} onRefresh={fetchData} />
        }
      >
        <Text style={styles.welcomeText}>
          Welcome, {userRole === 'doctor' ? 'Doctor' : 'Nurse'}!
        </Text>

        {/* Critical Alerts Card */}
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.cardTitle}>🚨 Critical Alerts</Title>
            {alerts && (alerts.medication_overdue.length > 0 || alerts.lab_reports_delayed.length > 0) ? (
              <>
                <Paragraph style={styles.alertText}>
                  Overdue Medications: {alerts.medication_overdue.length}
                </Paragraph>
                <Paragraph style={styles.alertText}>
                  Delayed Lab Reports: {alerts.lab_reports_delayed.length}
                </Paragraph>
              </>
            ) : (
              <Paragraph>No critical alerts at this time.</Paragraph>
            )}
          </Card.Content>
        </Card>

        {/* Nurse's "My Tasks" Card */}
        {userRole === 'nurse' && (
          <Card style={styles.card}>
            <Card.Content>
              <Title style={styles.cardTitle}>My Pending Tasks</Title>
              {myTasks.length > 0 ? (
                myTasks.map(task => (
                  <View key={task.id} style={styles.taskItem}>
                    <Text style={styles.taskText}>{task.description}</Text>
                    {/* This Link would navigate to the patient's detail screen */}
                    <Link href={`/patient/${task.encounter_id}`} asChild>
                      <Button mode="outlined" compact>View Patient</Button>
                    </Link>
                  </View>
                ))
              ) : (
                <Paragraph>No pending tasks assigned to you.</Paragraph>
              )}
            </Card.Content>
          </Card>
        )}

      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  headerTitle: {
    color: COLORS.primary,
    fontWeight: 'bold',
  },
  scrollContainer: {
    padding: SIZES.padding,
  },
  welcomeText: {
    ...FONTS.h2,
    color: COLORS.text,
    marginBottom: SIZES.padding,
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
  alertText: {
    ...FONTS.body,
    fontSize: SIZES.h4,
    color: COLORS.danger,
    fontWeight: '600',
  },
  taskItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SIZES.base,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  taskText: {
    ...FONTS.body,
    color: COLORS.text,
    flex: 1,
    paddingRight: SIZES.base,
  }
});