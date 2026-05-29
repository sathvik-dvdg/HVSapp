// context/AuthContext.js
import 'core-js/stable/atob'; // Polyfill for base64 decoding
import * as SecureStore from 'expo-secure-store';
import { jwtDecode } from 'jwt-decode'; // Import the decoder
import { createContext, useContext, useEffect, useState } from 'react';
import { Alert } from 'react-native';
import { apiLogin } from '../api/api.js'; // Use our api.js

// Define a key for storing the token
const KEY_USER_TOKEN = 'userToken';

// --- CRITICAL: EXPORT THE CONTEXT ---
export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [userToken, setUserToken] = useState(null);
    const [userRole, setUserRole] = useState(null); // 'admin', 'doctor', 'nurse'
    const [isLoading, setIsLoading] = useState(true); // Start loading

    // --- 1. Load Token on App Start ---
    useEffect(() => {
        const bootstrapAsync = async () => {
            let token = null;
            try {
                token = await SecureStore.getItemAsync(KEY_USER_TOKEN);
            } catch (e) {
                console.error('Failed to load token from storage', e);
            }

            if (token) {
                try {
                    // Check if token is expired
                    const decoded = jwtDecode(token);
                    if (decoded.exp * 1000 > Date.now()) {
                        setUserToken(token);
                        // Decode the 'sub' (subject) to get the role
                        // Our backend sets the 'sub' to the username (e.g., "admin@hospital.com")
                        setUserRole(getRoleFromUsername(decoded.sub));
                        console.log('Token loaded from storage.');
                    } else {
                        console.log('Token found, but expired. Clearing.');
                        await SecureStore.deleteItemAsync(KEY_USER_TOKEN);
                    }
                } catch (e) {
                    console.error('Failed to decode token', e);
                    await SecureStore.deleteItemAsync(KEY_USER_TOKEN); // Corrupt token
                }
            }
            setIsLoading(false);
        };
        bootstrapAsync();
    }, []);

    // --- 2. Sign In ---
    const signIn = async (username, password) => {
        setIsLoading(true);
        const token = await apiLogin(username, password);
        
        if (token) {
            setUserToken(token);
            try {
                // Decode token to find role
                const decoded = jwtDecode(token);
                const role = getRoleFromUsername(decoded.sub);
                setUserRole(role);
                
                await SecureStore.setItemAsync(KEY_USER_TOKEN, token);
                console.log(`Token saved. User logged in with role: ${role}`);
            } catch (e) {
                console.error('Failed to save or decode token', e);
                Alert.alert('Error', 'Could not save login session.');
            }
        }
        setIsLoading(false);
        return token; // Return token so login screen can navigate
    };

    // --- 3. Sign Out ---
    const signOut = async () => {
        setUserToken(null);
        setUserRole(null);
        await SecureStore.deleteItemAsync(KEY_USER_TOKEN);
        console.log('Token deleted from storage.');
    };

    // --- 4. Role Helper ---
    // This is a temporary helper. In a real app, the backend
    // should include the role in the JWT 'claims'.
    const getRoleFromUsername = (username) => {
        if (username.includes('admin')) return 'admin';
        if (username.includes('doctor')) return 'doctor';
        if (username.includes('nurse')) return 'nurse';
        return null; // Default
    };

    return (
        <AuthContext.Provider
            value={{ 
                userToken, 
                userRole, // Now components can check the role
                isLoading, 
                signIn, 
                signOut 
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

// --- 5. Helper hook to use the auth context ---
export const useAuth = () => {
    return useContext(AuthContext);
};