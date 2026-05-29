import LiveAudioStream from 'react-native-live-audio-stream';
import { Alert } from 'react-native';

const options = {
  sampleRate: 16000,  // Required by Whisper
  channels: 1,        // Mono
  bitsPerSample: 16,  // 16-bit PCM
  audioSource: 6,     // Voice recognition source on Android
  bufferSize: 4096    // 250ms chunks
};

export const startNativeAudioStream = (websocket) => {
  LiveAudioStream.init(options);
  
  LiveAudioStream.on('data', data => {
    // data is a base64 encoded string of PCM audio
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(data);
    }
  });

  LiveAudioStream.start();
};

export const stopNativeAudioStream = () => {
  LiveAudioStream.stop();
};