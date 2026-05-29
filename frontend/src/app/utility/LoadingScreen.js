// screens/utility/LoadingScreen.js
import { ActivityIndicator, StyleSheet, View } from 'react-native';

// Optional: Import your theme colors if you have them
// import { COLORS } from '../../constants/theme';

const LoadingScreen = () => {
    return (
        <View style={styles.container}>
            {/* Use your theme's primary color if available */}
            <ActivityIndicator size="large" color={"#0067T7"} /> 
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#FFFFFF', // Or your theme's background color
    }
});

export default LoadingScreen;