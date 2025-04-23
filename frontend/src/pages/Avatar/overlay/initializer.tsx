import { Button } from "@/components/ui/button";
import useSessionInitializer from "@/zustand/Avatar/Initializer";

export const AvatarInitializer = () => {
  const { sessionID } = useSessionInitializer();

  if (!sessionID) {
    return <InitializeSession />;
  } else {
    return null;
  }
};

const InitializeSession = () => {
  const { initialize } = useSessionInitializer();
  return (
    <div className="flex flex-col items-center justify-center h-screen absolute top-0 left-0 w-full z-10 bg-black/50">
      <Button onClick={initialize}>Begin</Button>
    </div>
  );
};
