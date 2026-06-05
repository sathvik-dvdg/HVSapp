import React, { useState } from 'react';
import { View, StyleSheet, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { TextInput, Button, Text, Card } from 'react-native-paper';
import { useRouter } from 'expo-router';
import { useAuth } from '../../features/auth/AuthContext';

export default function LoginScreen() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const { signIn } = useAuth();
    const router = useRouter();

    const handleLogin = async () => {
        if (!username || !password) {
            Alert.alert('Error', 'Please enter both username and password.');
            return;
        }

        setLoading(true);
        try {
            await signIn(username, password);
            router.replace('/(tabs)/dashboard');
        } catch (error) {
            console.error(error);
            Alert.alert('Login Failed', error.message || 'Invalid credentials or network error.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <KeyboardAvoidingView 
            behavior={Platform.OS === "ios" ? "padding" : "height"}
            style={styles.container}
        >
            <Card style={styles.card}>
                <Card.Content>
                    <Text variant="headlineMedium" style={styles.title}>HVS Portal</Text>
                    <Text variant="bodyMedium" style={styles.subtitle}>Secure Clinical Sign-In</Text>
                    
                    <TextInput
                        label="Username"
                        value={username}
                        onChangeText={setUsername}
                        autoCapitalize="none"
                        mode="outlined"
                        style={styles.input}
                        disabled={loading}
                    />
                    <TextInput
                        label="Password"
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry
                        mode="outlined"
                        style={styles.input}
                        disabled={loading}
                    />
                    
                    <Button 
                        mode="contained" 
                        onPress={handleLogin} 
                        loading={loading} 
                        disabled={loading}
                        style={styles.button}
                    >
                        Sign In
                    </Button>
                </Card.Content>
            </Card>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: { 
        flex: 1, 
        justifyContent: 'center', 
        padding: 20,
        backgroundColor: '#F8F9FA'
    },
    card: {
        paddingVertical: 16,
    },
    title: { 
        textAlign: 'center', 
        fontWeight: 'bold',
        color: '#2196F3'
    },
    subtitle: {
        textAlign: 'center',
        marginBottom: 24,
        color: '#666'
    },
    input: { 
        marginBottom: 16 
    },
    button: { 
        marginTop: 8,
        paddingVertical: 6
    }
});