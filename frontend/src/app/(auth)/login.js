// screens/auth/LoginScreen.js
import { useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TouchableOpacity } from 'react-native';
import { Button, TextInput } from 'react-native-paper'; // Using Paper components for style
import { useAuth } from '../../context/AuthContext';

// Import theme settings if you have them
// import { COLORS, FONTS, SIZES } from '../../constants/theme';

export default function LoginScreen({ navigation }) {
    const [username, setUsername] = useState('admin@hospital.com'); // Pre-fill admin for easy testing
    const [password, setPassword] = useState('VerySecureAdminPassword123!'); // Pre-fill password
    const [isLoading, setIsLoading] = useState(false);
    const { signIn } = useAuth();

    const handleLogin = async () => {
        if (!username || !password) {
            Alert.alert("Login Failed", "Please enter both email and password.");
            return;
        }
        setIsLoading(true);
        try {
            const token = await signIn(username, password);
            if (!token) {
                // signIn function already shows an alert, but we can add another
                console.log("Login failed, token was null.");
            }
            // Navigation will happen automatically from src.js
        } catch (error) {
            console.error("Error in handleLogin:", error.message);
        } finally {
            setIsLoading(false);
        }
    };

    // This function handles the "Admin: Create User" button press
    const navigateToAdminCreate = () => {
        // This navigation assumes your AppNavigator is set up to show
        // AdminCreateUser AFTER a user with 'admin' role logs in.
        // For testing, you might need a simpler way or a separate button.
        // Let's assume for now the user *is* an admin.
        navigation.navigate('AdminCreateUser');
    };

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === "ios" ? "padding" : "height"}
            style={styles.container}
        >
            <ScrollView contentContainerStyle={styles.scrollContainer}>
                <Text style={styles.title}>HVS</Text>
                <Text style={styles.subtitle}>Hand-Off Validation System</Text>
                
                <TextInput
                    label="Email (Username)"
                    style={styles.input}
                    value={username}
                    onChangeText={setUsername}
                    autoCapitalize="none"
                    keyboardType="email-address"
                    mode="outlined"
                />
                <TextInput
                    label="Password"
                    style={styles.input}
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry
                    mode="outlined"
                />
                <Button
                    mode="contained"
                    onPress={handleLogin}
                    loading={isLoading}
                    disabled={isLoading}
                    style={styles.button}
                    labelStyle={styles.buttonLabel}
                >
                    {isLoading ? "Logging in..." : "Login"}
                </Button>

                {/* This button is for the Admin flow we discussed */}
                <TouchableOpacity 
                    style={styles.adminButton} 
                    onPress={() => Alert.alert("Admin Access", "To create users, please log in with your Admin account. The 'Create User' screen will appear on your dashboard.")}
                >
                    <Text style={styles.adminText}>Admin User Creation</Text>
                </TouchableOpacity>

            </ScrollView>
        </KeyboardAvoidingView>
    );
}

// Basic styling
const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#FFFFFF',
    },
    scrollContainer: {
        flexGrow: 1,
        justifyContent: 'center',
        padding: 20,
    },
    title: {
        fontSize: 48,
        fontWeight: 'bold',
        color: '#0067T7', // Medical Blue
        textAlign: 'center',
    },
    subtitle: {
        fontSize: 18,
        color: '#555',
        textAlign: 'center',
        marginBottom: 40,
    },
    input: {
        marginBottom: 16,
    },
    button: {
        paddingVertical: 8,
        marginTop: 10,
    },
    buttonLabel: {
        fontSize: 16,
        fontWeight: 'bold',
    },
    adminButton: {
        marginTop: 20,
    },
    adminText: {
        textAlign: 'center',
        color: '#0067T7',
        textDecorationLine: 'underline',
    }
});