import { useAvatarSpeak, visemeMap } from "@/zustand/Avatar/Speak";
import { useAnimations, useFBX, useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useEffect, useRef } from "react";


export const TalkingAvatar = () => {
  const group = useRef(null);

  const { viseme, getPlaying, audio } = useAvatarSpeak();
  const { nodes, scene } = useGLTF("/Tests/avatar.glb");
  const animation = "Happy Idle"
  const { animations: talkingAnimation } = useFBX(
    `/Tests/${animation}.fbx`
  );

  talkingAnimation[0].name = animation;

  const { actions } = useAnimations([...talkingAnimation], group);

  useEffect(() => {
    if (actions && actions[animation]) {  
      actions[animation].reset().play();
    }
  }, [actions, animation]);

  // const lerpTarget = (target, value, speed = 0.1) => {
  //   if (nodes.Wolf3D_Head.morphTargetDictionary[target] !== undefined) {
  //     nodes.Wolf3D_Head.morphTargetInfluences[
  //       nodes.Wolf3D_Head.morphTargetDictionary[target]
  //     ] = MathUtils.lerp(
  //       nodes.Wolf3D_Head.morphTargetInfluences[
  //         nodes.Wolf3D_Head.morphTargetDictionary[target]
  //       ],
  //       value,
  //       speed
  //     );
  //   }
  //   if (nodes.Wolf3D_Teeth.morphTargetDictionary[target] !== undefined) {
  //     nodes.Wolf3D_Teeth.morphTargetInfluences[
  //       nodes.Wolf3D_Teeth.morphTargetDictionary[target]
  //     ] = MathUtils.lerp(
  //       nodes.Wolf3D_Teeth.morphTargetInfluences[
  //         nodes.Wolf3D_Teeth.morphTargetDictionary[target]
  //       ],
  //       value,
  //       speed
  //     );
  //   }
  // };

  const incrementMorph = (morphName: string, targetValue: number, duration: number) => {
    const stepTime = 5;
    const steps = duration / stepTime;
    const increment = targetValue / steps;

    let currentValue = 0;

    const incrementStep = () => {
      if (currentValue < targetValue) {
        currentValue += increment;
        if (currentValue > targetValue) {
          currentValue = targetValue;
        }
        if (nodes.Wolf3D_Head.morphTargetDictionary[morphName] !== undefined) {
          nodes.Wolf3D_Head.morphTargetInfluences[
            nodes.Wolf3D_Head.morphTargetDictionary[morphName]
          ] = currentValue;
        }
        if (nodes.Wolf3D_Teeth.morphTargetDictionary[morphName] !== undefined) {
          nodes.Wolf3D_Teeth.morphTargetInfluences[
            nodes.Wolf3D_Teeth.morphTargetDictionary[morphName]
          ] = currentValue;
        }
        setTimeout(incrementStep, stepTime);
      }
    };
    incrementStep();
  };

  const morphFunction = (morphName: string, value: number, duration = 0) => {
    if (duration > 0) {
      incrementMorph(morphName, value, duration);
    } else {
      if (nodes.Wolf3D_Head.morphTargetDictionary[morphName] !== undefined) {
        nodes.Wolf3D_Head.morphTargetInfluences[
          nodes.Wolf3D_Head.morphTargetDictionary[morphName]
        ] = value;
      }
      if (nodes.Wolf3D_Teeth.morphTargetDictionary[morphName] !== undefined) {
        nodes.Wolf3D_Teeth.morphTargetInfluences[
          nodes.Wolf3D_Teeth.morphTargetDictionary[morphName]
        ] = value;
      }
    }
  };

  function updateViseme(timestamp: number) {
    if (!viseme) return;
    Object.values(visemeMap).map((e) => {
      morphFunction(e, 0, 0);
    });
    for (let i = viseme.length - 1; i >= 0; i--) {
      if (timestamp * 1000 >= viseme[i].stopTime) {
        morphFunction(viseme[i].readyPlayerMeViseme, 1, 0);
        break;
      }
    }
  }

  useFrame((state) => {
    if (getPlaying() && audio) {
      updateViseme(Number(audio.currentTime.toFixed(2)));
    } else {
      Object.values(visemeMap).map((e) => {
        morphFunction(e, 0, 0);
      });
    }
    if (group.current) {
      group.current.getObjectByName("Head").lookAt(state.camera.position);
    }
  });
  return (
    <group ref={group} position={[0, -1.5, 3.9]}>
      <primitive object={scene} />
    </group>
  );
};

