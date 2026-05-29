// app/(tabs)/createUser.js
import { useNavigation } from 'expo-router'; // Import navigation hook
import { useState } from 'react'; // Import React
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text
} from 'react-native';
import { Button, SegmentedButtons, TextInput } from 'react-native-paper';
import { apiAdminCreateUser } from '../../api/api.js';
import { useAuth } from '../../context/AuthContext.js';
// Import theme (ensure this path is correct)
import { COLORS, FONTS, SIZES } from '../../constants/theme';

// Renamed component to match file name convention
export default function CreateUserScreen() {
  const { userToken: adminToken } = useAuth(); // Get the logged-in admin's token
  const navigation = useNavigation(); // Get navigation object

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('doctor'); // Default role
  const [isLoading, setIsLoading] = useState(false);

  const handleCreateUser = async () => {
    // 1. Validate required fields
    if (!username || !password || !fullName || !role) {
      Alert.alert('Error', 'Please fill in all fields.');
      return;
    }

    // 2. Check for admin token (from AuthContext)
    if (!adminToken) {
      Alert.alert('Authentication Error', 'Admin token not found. Please re-login as Admin.');
      return;
    }

    setIsLoading(true);
    try {
      // 3. Prepare data for the API (matches backend schema)
      const userData = {
        username: username,
        password: password,
        full_name: fullName,
        role: role,
      };

      // 4. Call the API
      const result = await apiAdminCreateUser(userData, adminToken);

      // 5. Handle success
      if (result && result.id) {
        Alert.alert(
          'Success',
          `User ${result.username} (Role: ${result.role}) created!`
        );
        // Clear the form
        setUsername('');
        setPassword('');
        setFullName('');
        setRole('doctor');
        // Optional: Navigate away after success
        // navigation.goBack(); 
      } else {
        throw new Error('Failed to create user or received invalid response.');
      }
    } catch (error) {
      // 6. Handle errors
      Alert.alert('Creation Failed', error.message || 'An unknown error occurred.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <Text style={styles.title}>Create New Staff</Text>

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
          label="User's Hospital Email"
          style={styles.input}
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
          keyboardType="email-address"
          mode="outlined"
          theme={{ roundness: SIZES.radius }}
        />
        <TextInput
          label="Temporary Password"
          style={styles.input}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          mode="outlined"
          theme={{ roundness: SIZES.radius }}
        />

        <Text style={styles.label}>Select Role</Text>
        <SegmentedButtons
          value={role}
          onValueChange={setRole}
          buttons={[
            { value: 'doctor', label: 'Doctor', icon: 'doctor' },
            { value: 'nurse', label: 'Nurse', icon: 'account-heart' },
          ]}
          style={styles.segmentedButtons}
        />

        <Button
          mode="contained"
          onPress={handleCreateUser}
          loading={isLoading}
          disabled={isLoading}
          style={styles.button}
          labelStyle={styles.buttonLabel}
        >
          {isLoading ? "Creating..." : "Create User Account"}
        </Button>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// Styles using your theme constants
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background, // Use theme background
  },
  scrollContainer: {
    padding: SIZES.padding,
  },
  title: {
    ...FONTS.h2, // Use h2 font from theme
    color: COLORS.primary, // Use primary color
    textAlign: 'center',
    marginBottom: SIZES.paddingLarge,
  },
  input: {
    marginBottom: SIZES.padding,
  },
  label: {
    ...FONTS.h4, // Use h4 font
    color: COLORS.text,
    marginBottom: SIZES.base,
    marginTop: SIZES.base,
  },
  segmentedButtons: {
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