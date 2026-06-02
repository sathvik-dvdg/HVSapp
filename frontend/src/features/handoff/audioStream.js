import LiveAudioStream from 'react-native-live-audio-stream';
import { Buffer } from 'buffer';

const AUDIO_OPTIONS = {
  sampleRate: 16000,  // Required by Whisper
  channels: 1,        // Mono
  bitsPerSample: 16,  // 16-bit PCM
  audioSource: 6,     // Voice Recognition source
  bufferSize: 4096,    // Buffer size for audio chunks
};

export const startAudioStream = (onChunk) => {
  LiveAudioStream.init(AUDIO_OPTIONS);
  
    LiveAudioStream.on('data', (data) => {
    // data is base64-encoded PCM; decode to binary before sending
    const binary = Buffer.from(data, 'base64');
    onChunk(binary);
  });

  LiveAudioStream.start();
};

export const stopAudioStream = () => {
  LiveAudioStream.stop();
};