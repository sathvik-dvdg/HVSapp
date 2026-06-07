import LiveAudioStream from 'react-native-live-audio-stream';

const AUDIO_OPTIONS = {
  sampleRate: 16000,
  bitsPerSample: 16,
  channels: 1,
  audioSource: 6,
  bufferSize: 4096,
};

let audioListener = null;

export const startAudioStream = async (onChunk) => {
  LiveAudioStream.init(AUDIO_OPTIONS);
  audioListener = (chunk) => {
    onChunk(chunk);
  };
  LiveAudioStream.on('data', audioListener);
  await LiveAudioStream.start();
};

export const stopAudioStream = async () => {
  if (audioListener) {
    LiveAudioStream.removeListener('data', audioListener);
    audioListener = null;
  }
  await LiveAudioStream.stop();
};
