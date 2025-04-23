import {
  AudioMessage,
  ConversationMessage,
  ConversationMessageType,
} from "@/types/avatar/conversation";
import WebsocketManager from "@/utils/websocket";
import useSessionInitializer from "@/zustand/Avatar/Initializer";
import useQuerySent from "@/zustand/Avatar/QuerySent";
import { useAvatarSpeak } from "@/zustand/Avatar/Speak";
import useWebsocket from "@/zustand/Avatar/Websocket";
import { Canvas } from "@react-three/fiber";
import { TalkingAvatar } from "./avatar";
import { AvatarInitializer } from "./initializer";
import { Status } from "./status";
import TranscriptionManager from "./transcription";

const MIN_SPEECH_DURATION = 1;

export const AvatarOverlay = () => {
  const { setIsConnected, isConnected, websocket, setwebsocket } =
    useWebsocket();
  const { setAudio, setViseme, setWordOffset, isPlaying } = useAvatarSpeak();
  const { querySent, setQuerySent } = useQuerySent();
  const { sessionID } = useSessionInitializer();

  function onMessage(event: MessageEvent) {
    const data: ConversationMessage = JSON.parse(event.data);
    setQuerySent(false);
    switch (data.type) {
      case ConversationMessageType.AUDIO_RESPONSE:
        try {
          const AudioMessage: AudioMessage = data.data;
          setAudio(AudioMessage.base64_audio);
          setViseme(AudioMessage.viseme);
          setWordOffset(AudioMessage.word_boundary);
        } catch (error) {
          console.error("Error parsing audio response:", error);
        }
        break;
    }
  }

  function onSendMessage(message: Float32Array) {
    if (message.length == 0 || !websocket || !sessionID || isPlaying) return;
    const data: ConversationMessage = {
      type: ConversationMessageType.QUERY,
      data: { query: message },
    };
    setQuerySent(true);
    websocket.send(JSON.stringify(data));
  }
  return (
    <div className="flex flex-col items-center justify-center h-full w-full">
      <AvatarInitializer />
      <Canvas style={{ height: "95vh", width: "90vw" }}>
        <ambientLight intensity={2} />
        <pointLight position={[10, 10, 10]} />
        {/* <OrbitControls /> */}
        <TalkingAvatar />
      </Canvas>
      {sessionID && (
        <WebsocketManager
          url={`conversation/ws?user_id=${sessionID}`}
          setIsConnected={setIsConnected}
          isConnected={isConnected}
          websocket={websocket}
          setwebsocket={setwebsocket}
          onMessage={onMessage}
        />
      )}
      <Status />
      <TranscriptionManager
        onSendMessage={onSendMessage}
        timeout={MIN_SPEECH_DURATION}
      />
    </div>
  );
};
