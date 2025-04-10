import { useState } from "react";

export const AvatarIcon = () => {
  const [hovered, setHovered] = useState(false);
  return (
    <div className="fixed bottom-5 right-5 flex flex-col justify-center items-center cursor-pointer">
      <div
        className="min-w-[100px] aspect-1/1 rounded-[50px] bg-white"
        onPointerEnter={() => setHovered(true)}
        onPointerLeave={() => setHovered(false)}
      />
      {!hovered && (
        <div className="absolute bottom-2 font-bold text-4xl">Adam</div>
      )}
    </div>
  );
};
