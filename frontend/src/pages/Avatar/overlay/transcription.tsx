import { useMicVAD } from "@ricky0123/vad-react";

function getAudioDurationFromFloat32Array(
  audioData: Float32Array,
  sampleRate = 16000
): number {
  return audioData.length / sampleRate;
}

const TranscriptionManager = ({
  onSendMessage,
  timeout,
}: {
  onSendMessage: (message: Float32Array) => void;
  timeout: number;
}) => {
  const vad = useMicVAD({
    onSpeechEnd: (audio) => {
      try {
        const duration = getAudioDurationFromFloat32Array(audio);
        if (duration > timeout) {
          onSendMessage(audio);
        }
      } catch (error) {
        console.error("Error getting audio duration:", error);
      }
    },
    positiveSpeechThreshold: 0.8,
  });

  return (
    <div className="absolute top-0 left-0 bg-green-500">
      {vad.userSpeaking && "User is speaking"}
    </div>
  );
};

export default TranscriptionManager;
