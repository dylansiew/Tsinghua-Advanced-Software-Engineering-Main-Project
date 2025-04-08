import { AudioMessage, ConversationMessage, ConversationMessageType } from "@/types/avatar/conversation";
import WebsocketManager from "@/utils/websocket";
import { useAvatarSpeak } from "@/zustand/Avatar/Speak";
import useWebsocket from "@/zustand/Avatar/Websocket";
import { useGLTF } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useRef } from "react";
import { Group } from "three";
import { Status } from "./status";
import TranscriptionManager from "./transcription";
import { TalkingAvatar } from "./avatar";

const USER_ID = import.meta.env.VITE_USER_ID;
const TIMEOUT_SECONDS = 2;

export const AvatarOverlay = () => {
  const { setIsConnected, isConnected, websocket, setwebsocket } =
    useWebsocket();

  const { setAudio, setViseme, setWordOffset } = useAvatarSpeak();
  function onMessage(event: MessageEvent) {
    const data: ConversationMessage = JSON.parse(event.data);
    switch (data.type) {
      case ConversationMessageType.AUDIO_RESPONSE:
        try {
          console.log(data);
          const AudioMessage: AudioMessage = data.data;
          console.log(AudioMessage);
          setAudio(AudioMessage.base64_audio);
          setViseme(AudioMessage.viseme);
          setWordOffset(AudioMessage.word_boundary);
        } catch (error) {
          console.error("Error parsing audio response:", error);
        }
        break;
      }
  }

  function onSendMessage(message: string) {
    if (message.length == 0 || !websocket) return;
    const data: ConversationMessage = {
      type: ConversationMessageType.QUERY,
      data: { query: message },
    };
    websocket.send(JSON.stringify(data));
  }
  return (
    <div className="flex flex-col items-center justify-center h-full w-full">
      <Canvas style={{ height: "95vh", width: "90vw" }}>
        <ambientLight intensity={2} />
        <pointLight position={[10, 10, 10]} />
        {/* <OrbitControls /> */}
        <TalkingAvatar />
      </Canvas>
      <WebsocketManager
        url={`conversation/ws?user_id=${USER_ID}`}
        setIsConnected={setIsConnected}
        isConnected={isConnected}
        websocket={websocket}
        setwebsocket={setwebsocket}
        onMessage={onMessage}
      />
      <Status />
      <TranscriptionManager
        onSendMessage={onSendMessage}
        timeout={TIMEOUT_SECONDS}
      />
    </div>
  );
};

const Avatar = () => {
  const { scene, nodes } = useGLTF("/Tests/avatar.glb");
  const ref = useRef<Group>(null);

  return (
    <group ref={ref} position={[0, -1.5, 3.9]}>
      <primitive object={scene} />
    </group>
  );
};
