import useSessionInitializer from "@/zustand/Avatar/Initializer";
import useQuerySent from "@/zustand/Avatar/QuerySent";
import { useAvatarSpeak } from "@/zustand/Avatar/Speak";
import useSTT from "@/zustand/Avatar/STT";
import { useEffect, useRef } from "react";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";

const TranscriptionManager = ({
  onSendMessage,
  timeout,
}: {
  onSendMessage: (message: string) => void;
  timeout: number;
}) => {
  const { listening, browserSupportsSpeechRecognition, transcript } =
    useSpeechRecognition();
  const { spokenChunk, setTranscript, chunkConsumed } = useSTT();
  const { getPlaying } = useAvatarSpeak();
  const { sessionID } = useSessionInitializer();
  const { querySent } = useQuerySent();

  const playing = getPlaying();
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  function startListening() {
    SpeechRecognition.startListening({
      language: "en-US",
      continuous: true,
    });
  }

  function stopListening() {
    SpeechRecognition.stopListening();
  }
  if (!browserSupportsSpeechRecognition) {
    return <span>Browser doesn't support speech recognition.</span>;
  }

  useEffect(() => {
    if (playing || !sessionID || querySent) {
      stopListening();
    } else if (!listening) {
      startListening();
    }
  }, [playing, sessionID, querySent]);

  useEffect(() => {
    setTranscript(transcript);

    // Clear existing timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Set new timer
    timerRef.current = setTimeout(() => {
      onSendMessage(spokenChunk);
      chunkConsumed();
    }, timeout * 1000);

    // Cleanup timer on unmount
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [transcript, chunkConsumed]);

  return (
    <div className="absolute bottom-5 left-0 p-2 w-full flex flex-col items-center justify-center">
      {spokenChunk.length > 0 && (
        <div className="bg-gray-800 p-2 rounded-sm text-center text-white">
          {spokenChunk}
        </div>
      )}
    </div>
  );
};

export default TranscriptionManager;
