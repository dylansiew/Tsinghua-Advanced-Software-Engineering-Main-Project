import useWebsocket from "@/zustand/Avatar/Websocket";
import { useSpeechRecognition } from "react-speech-recognition";

const RedDot = () => {
  return <div className="w-2 h-2 bg-red-500 rounded-full" />;
};

const GreenDot = () => {
  return <div className="w-2 h-2 bg-green-500 rounded-full" />;
};

const StatusDot = ({
  isConnected,
  name,
}: {
  isConnected: boolean;
  name: string;
}) => {
  return (
    <div className="flex flex-col items-center gap-2">
      <span className="text-sm">{name}</span>
      {isConnected ? <GreenDot /> : <RedDot />}
    </div>
  );
};

export const Status = () => {
  const { isConnected } = useWebsocket();
  const { listening } = useSpeechRecognition();
  return (
    <div className="absolute top-5 left-5 grid grid-cols-2 gap-2">
      <StatusDot isConnected={isConnected} name="Websocket" />
      <StatusDot isConnected={listening} name="STT" />
    </div>
  );
};
