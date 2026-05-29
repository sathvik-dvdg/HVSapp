// app/patient/[id]/history.js
import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView, RefreshControl, FlatList } from 'react-native';
import { ActivityIndicator, Card, Title, Paragraph, Chip } from 'react-native-paper';
import { useLocalSearchParams, useFocusEffect } from 'expo-router';
// --- Corrected Import Paths ---
import { useAuth } from '../../../context/AuthContext';
import { apiGetPatientHistory } from '../../../api/api';
import { COLORS, FONTS, SIZES } from '../../../constants/theme';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

// Helper to format dates
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString('en-US', {
    dateStyle: 'medium', timeStyle: 'short'
  });
};

// --- Added export default ---
export default function PatientHistoryScreen() {
  const { id: patientId } = useLocalSearchParams();
  const { userToken } = useAuth();

  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch data function
  const loadHistory = useCallback(async () => {
    if (!userToken || !patientId) return;
    setIsLoading(true);
    try {
      const historyData = await apiGetPatientHistory(patientId, userToken);
      setHistory(historyData || []);
    } catch (error) {
      Alert.alert("Error", `Could not load patient history: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [userToken, patientId]);

  // useFocusEffect runs every time the screen comes into view
  useFocusEffect(
    useCallback(() => {
      const fetchData = async () => {
        await loadHistory();
      };
      fetchData();
    }, [loadHistory])
  );

  const getIconForType = (type) => {
    switch (type) {
      case 'ENCOUNTER': return 'hospital-building';
      case 'NOTE': return 'note-text-outline';
      case 'TASK': return 'clipboard-check-outline';
      default: return 'help-circle';
    }
  };

  const renderHistoryItem = ({ item }) => (
    <View style={styles.itemContainer}>
      <View style={styles.iconContainer}>
        <Icon name={getIconForType(item.type)} size={24} color={COLORS.primary} />
      </View>
      <View style={styles.contentContainer}>
        <Text style={styles.subject}>{item.subject}</Text>
        <Text style={styles.detail}>{item.detail}</Text>
        <Text style={styles.timestamp}>{formatDate(item.timestamp)}</Text>
      </View>
      <Chip style={styles.chip} textStyle={styles.chipText}>{item.type}</Chip>
    </View>
  );

  if (isLoading) {
    return (
      <View style={styles.loaderContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {history.length === 0 ? (
        <Text style={styles.emptyText}>No history found for this patient.</Text>
      ) : (
        <FlatList
          data={history}
          keyExtractor={(item) => `${item.type}_${item.id}_${item.timestamp}`}
          renderItem={renderHistoryItem}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={isLoading} onRefresh={loadHistory} />
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  list: {
    padding: SIZES.padding,
  },
  loaderContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  emptyText: {
    ...FONTS.body,
    color: COLORS.textLight,
    textAlign: 'center',
    marginTop: 50,
  },
  itemContainer: {
    flexDirection: 'row',
    backgroundColor: COLORS.surface,
    borderRadius: SIZES.radius,
    padding: SIZES.padding,
    marginBottom: SIZES.padding,
    alignItems: 'center',
  },
  iconContainer: {
    marginRight: SIZES.padding,
  },
  contentContainer: {
    flex: 1,
  },
  subject: {
    ...FONTS.h4,
    color: COLORS.text,
    fontWeight: 'bold',
    textTransform: 'capitalize',
  },
  detail: {
    ...FONTS.body,
    color: COLORS.text,
    textTransform: 'capitalize',
  },
  timestamp: {
    ...FONTS.body,
    fontSize: 12,
    color: COLORS.textLight,
    marginTop: SIZES.base,
  },
  chip: {
    backgroundColor: COLORS.lightGray,
  },
  chipText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: COLORS.textLight,
  }
});