// app/(tabs)/patients.js
import React, { useState } from 'react';
import { View, Text, StyleSheet, FlatList, Alert, TouchableOpacity } from 'react-native';
import { Searchbar, Card, Title, Paragraph, ActivityIndicator } from 'react-native-paper';
import { useAuth } from '../../context/AuthContext';
import { apiSearchPatients } from '../../api/api';
import { COLORS, FONTS, SIZES } from '../../constants/theme';
import { Link, useRouter } from 'expo-router';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

export default function PatientListScreen() {
  const { userToken } = useAuth();
  const router = useRouter(); // Use router for navigation
  const [searchQuery, setSearchQuery] = useState('');
  const [patients, setPatients] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false); // To show "no results"

  const handleSearch = async () => {
    if (!searchQuery) {
      setPatients([]);
      setHasSearched(false);
      return;
    }
    
    setIsLoading(true);
    setHasSearched(true); // Mark that a search has been attempted
    try {
      const results = await apiSearchPatients(searchQuery, userToken);
      setPatients(results || []); // Ensure results is an array
    } catch (error) {
      Alert.alert("Search Failed", error.message);
      setPatients([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Navigate to the patient's detail screen
  // This will link to app/patient/[id].js
  const handlePatientPress = (patientId) => {
    router.push(`/patient/${patientId}`);
  };

  const renderPatientItem = ({ item }) => (
    <TouchableOpacity onPress={() => handlePatientPress(item.id)}>
      <Card style={styles.card}>
        <Card.Content style={styles.cardContent}>
          <View style={styles.iconContainer}>
            <Icon name="account-circle" size={40} color={COLORS.primary} />
          </View>
          <View style={styles.textContainer}>
            <Title style={styles.patientName}>{item.full_name}</Title>
            <Paragraph style={styles.patientId}>ID: {item.id}</Paragraph>
            {item.date_of_birth && (
              <Paragraph style={styles.patientDob}>DOB: {item.date_of_birth}</Paragraph>
            )}
          </View>
          <Icon name="chevron-right" size={24} color={COLORS.textLight} />
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Searchbar
        placeholder="Search patients by name..."
        onChangeText={setSearchQuery}
        value={searchQuery}
        onIconPress={handleSearch}
        onSubmitEditing={handleSearch} // Allow searching from keyboard
        style={styles.searchbar}
      />

      {isLoading ? (
        <ActivityIndicator size="large" color={COLORS.primary} style={styles.loader} />
      ) : (
        <FlatList
          data={patients}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderPatientItem}
          contentContainerStyle={styles.list}
          ListEmptyComponent={() => (
            hasSearched && !isLoading && (
              <View style={styles.emptyContainer}>
                <Text style={styles.emptyText}>No patients found matching "{searchQuery}".</Text>
              </View>
            )
          )}
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
  searchbar: {
    margin: SIZES.padding,
    backgroundColor: COLORS.surface,
  },
  loader: {
    marginTop: 50,
  },
  list: {
    paddingHorizontal: SIZES.padding,
    paddingBottom: SIZES.padding,
  },
  card: {
    marginBottom: SIZES.base,
    backgroundColor: COLORS.surface,
  },
  cardContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    marginRight: SIZES.padding,
  },
  textContainer: {
    flex: 1,
  },
  patientName: {
    ...FONTS.h3,
    color: COLORS.text,
    marginBottom: 0,
  },
  patientId: {
    ...FONTS.body,
    fontSize: 12,
    color: COLORS.textLight,
  },
  patientDob: {
    ...FONTS.body,
    fontSize: 12,
    color: COLORS.textLight,
  },
  emptyContainer: {
    marginTop: 50,
    alignItems: 'center',
  },
  emptyText: {
    ...FONTS.h3,
    color: COLORS.textLight,
  },
});