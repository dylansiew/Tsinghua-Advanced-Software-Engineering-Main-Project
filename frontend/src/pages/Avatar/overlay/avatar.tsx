import { useAnimations, useFBX, useGLTF } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useEffect, useRef } from "react";
import {
  useAvatarSpeak,
  visemeMap,
} from "src/store/student/experience/avatarSpeak";
import { degToRad } from "three/src/math/MathUtils";

export const teachers = ["mainboy"];

export const Teacher = ({  ...props }) => {
  const group = useRef();

  const { viseme, getPlaying, audio } = useAvatarSpeak();
  const { nodes, materials, scene } = useGLTF("/Tests/avatar.glb");
  // const { animations: talkingAnimation } = useFBX(
  //   `/animations/${animation}.fbx`
  // );

  // talkingAnimation[0].name = animation;

  // const { actions } = useAnimations([...talkingAnimation], group);

  // useEffect(() => {
  //   actions[animation].reset().play();
  // }, [actions, animation]);

  const lerpTarget = (target, value, speed = 0.1) => {
    if (nodes.Wolf3D_Head.morphTargetDictionary[target] !== undefined) {
      nodes.Wolf3D_Head.morphTargetInfluences[
        nodes.Wolf3D_Head.morphTargetDictionary[target]
      ] = MathUtils.lerp(
        nodes.Wolf3D_Head.morphTargetInfluences[
          nodes.Wolf3D_Head.morphTargetDictionary[target]
        ],
        value,
        speed
      );
    }
    if (nodes.Wolf3D_Teeth.morphTargetDictionary[target] !== undefined) {
      nodes.Wolf3D_Teeth.morphTargetInfluences[
        nodes.Wolf3D_Teeth.morphTargetDictionary[target]
      ] = MathUtils.lerp(
        nodes.Wolf3D_Teeth.morphTargetInfluences[
          nodes.Wolf3D_Teeth.morphTargetDictionary[target]
        ],
        value,
        speed
      );
    }
  };

  const incrementMorph = (morphName, targetValue, duration) => {
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

  const morphFunction = (morphName, value, duration = 0) => {
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

  function updateViseme(timestamp) {
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
      updateViseme(audio.currentTime.toFixed(2));
    } else {
      Object.values(visemeMap).map((e) => {
        morphFunction(e, 0, 0);
      });
    }

    group.current.getObjectByName("Head").lookAt(state.camera.position);
  });
  return (
    <group {...props} ref={group}>
      <primitive object={scene} rotation={[0, degToRad(-60), 0]} />
    </group>
  );
};

teachers.forEach((teacher) => {
  useGLTF.preload(`/models/custom/${teacher}.glb`);
});
