import { Button } from "@/components/ui/button";
import { OrbitControls, useGLTF } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Fragment, useEffect, useRef, useState } from "react";
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { Group } from "three";

const Dictaphone = () => {
  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  if (!browserSupportsSpeechRecognition) {
    return <span>Browser doesn't support speech recognition.</span>;
  }

  return (
    <div>
      <p>Microphone: {listening ? 'on' : 'off'}</p>
      <button onClick={() => SpeechRecognition.startListening({ language: 'zh-CN' })}>Start</button>
      <button onClick={SpeechRecognition.stopListening}>Stop</button>
      <button onClick={resetTranscript}>Reset</button>
      <p>{transcript}</p>
    </div>
  );
};
export default Dictaphone;

export const AvatarOverlay = () => {
    const mp3File = "/Tests/audio1.mp3";
    const [audio, setAudio] = useState<HTMLAudioElement | null>(null);
    const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
  
    useEffect(() => {
      const audioElement = new Audio(mp3File);
      setAudio(audioElement);
    }, []);
  
    const handlePlay = () => {
      if (!audio) return;
      if (!audioContextRef.current) {
        const audioContext = new AudioContext();
        const source = audioContext.createMediaElementSource(audio);
        const analyserNode = audioContext.createAnalyser();
        analyserNode.fftSize = 512;
        source.connect(analyserNode);
        analyserNode.connect(audioContext.destination);
        audioContextRef.current = audioContext;
        setAnalyser(analyserNode);
      }
      audioContextRef.current?.resume(); // Ensure context is running
      audio.play();
    };
  
    return (
      <Fragment>
        <Canvas style={{ width: "100%", height: "80vh" }}>
          <ambientLight intensity={2} />
          <pointLight position={[10, 10, 10]} />
          <OrbitControls />
          {audio && analyser && <Avatar audio={audio} analyser={analyser} />}
        </Canvas>
        {audio && (
          <TestMediaPlayer audio={audio} onPlay={handlePlay} />
        )}
        <Dictaphone />
      </Fragment>
    );
  };
  
  const TestMediaPlayer = ({
    audio,
    onPlay,
  }: {
    audio: HTMLAudioElement;
    onPlay: () => void;
  }) => {
    const [duration, setDuration] = useState<number | null>(null);
    const [currentTime, setCurrentTime] = useState<number>(0);
  
    useEffect(() => {
      const handleLoadedMetadata = () => setDuration(audio.duration);
      const updateTime = () => setCurrentTime(audio.currentTime);
      audio.addEventListener("loadedmetadata", handleLoadedMetadata);
      audio.addEventListener("timeupdate", updateTime);
      return () => {
        audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
        audio.removeEventListener("timeupdate", updateTime);
      };
    }, [audio]);
  
    return (
      <div>
        <Button onClick={onPlay}>Play</Button>
        <Button onClick={() => audio.pause()}>Pause</Button>
        <div>Duration: {duration !== null ? `${(duration / 60).toFixed(2)} min` : "Loading..."}</div>
        <div>Current Time: {(currentTime / 60).toFixed(2)} min</div>
      </div>
    );
  };
  
  const Avatar = ({
    audio,
    analyser,
  }: {
    audio: HTMLAudioElement;
    analyser: AnalyserNode;
  }) => {
    const { scene, nodes } = useGLTF("/Tests/avatar.glb");
    const ref = useRef<Group>(null);
    const dataArrayRef = useRef<Uint8Array>(new Uint8Array(analyser.frequencyBinCount));
  
    useFrame(() => {
        if (audio.paused) return;
      
        analyser.getByteFrequencyData(dataArrayRef.current);
        const volume = dataArrayRef.current.reduce((sum, val) => sum + val, 0) / dataArrayRef.current.length;
      
        const threshold = 50;
        const maxVolume = 255;
        const mouthStrength = volume > threshold ? ((volume - threshold) * 100)  / (maxVolume - threshold) : 0;

        const morphName = "mouthOpen";
        const headInfluences = nodes.Wolf3D_Head.morphTargetInfluences;
        const teethInfluences = nodes.Wolf3D_Teeth.morphTargetInfluences;
        const dictHead = nodes.Wolf3D_Head.morphTargetDictionary;
        const dictTeeth = nodes.Wolf3D_Teeth.morphTargetDictionary;
      
        if (dictHead && dictTeeth) {
          headInfluences[dictHead[morphName]] = Math.min(mouthStrength, 1.3);  // ensure max 1
          teethInfluences[dictTeeth[morphName]] = Math.min(mouthStrength * 0.5, 0.5);
        }
      });
      
  
    return (
      <group ref={ref} position={[0, -1.5, 4.2]}>
        <primitive object={scene} />
      </group>
    );
  };
  