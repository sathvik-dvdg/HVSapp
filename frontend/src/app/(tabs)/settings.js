// app/(tabs)/settings.js
import React from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Button, Title, Card, Paragraph } from 'react-native-paper';
import { useAuth } from '../../context/AuthContext';
import { COLORS, FONTS, SIZES } from '../../constants/theme';

export default function SettingsScreen() {
  const { signOut, userRole } = useAuth(); // Get the signOut function

  const handleSignOut = () => {
    Alert.alert(
      "Sign Out",
      "Are you sure you want to sign out?",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Sign Out", style: "destructive", onPress: signOut }
      ]
    );
  };

  const handleLinkGoogle = () => {
    Alert.alert(
      "Feature Pending",
      "Linking your Google account will be available in a future update."
    );
  };

  const handleChatAssistant = () => {
    Alert.alert(
      "Feature Pending",
      "The chat assistant is not yet implemented."
    );
  };

  return (
    <View style={styles.container}>
      <Title style={styles.title}>Settings</Title>
      
      <Card style={styles.card}>
        <Card.Title title="Account" />
        <Card.Content>
          <Paragraph>You are logged in as: {userRole}</Paragraph>
          <Button 
            mode="contained" 
            onPress={handleLinkGoogle} 
            style={styles.button}
            icon="google"
          >
            Link Google Account
          </Button>
        </Card.Content>
      </Card>
      
      <Card style={styles.card}>
        <Card.Title title="Support" />
        <Card.Content>
          <Button 
            mode="outlined" 
            onPress={handleChatAssistant} 
            style={styles.button}
            icon="chat-question-outline"
          >
            Ask Chat Assistant
          </Button>
        </Card.Content>
      </Card>
      
      <Button 
        mode="contained" 
        onPress={handleSignOut} 
        style={styles.signOutButton}
        color={COLORS.danger} // Use a distinct color for sign out
        icon="logout"
      >
        Sign Out
      </Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: SIZES.padding,
    backgroundColor: COLORS.background,
  },
  title: {
    ...FONTS.h1,
    color: COLORS.primary,
    marginBottom: SIZES.paddingLarge,
  },
  card: {
    marginBottom: SIZES.padding,
    backgroundColor: COLORS.surface,
  },
  button: {
    marginTop: SIZES.base,
  },
  signOutButton: {
    marginTop: SIZES.paddingLarge,
    paddingVertical: SIZES.base,
    borderRadius: SIZES.radius,
  }
});