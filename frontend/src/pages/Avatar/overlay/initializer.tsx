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
      <div className="bg-white p-8 rounded-xl shadow-lg max-w-md text-center space-y-6">
        <h1 className="text-2xl font-bold text-primary mb-2">Welcome to Your Virtual Shopping Assistant!</h1>
        
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <h2 className="font-semibold text-lg mb-2">How it works:</h2>
            <ol className="text-left list-decimal pl-5 space-y-2">
              <li>Click the <span className="font-medium text-primary">Begin</span> button below</li>
              <li>Tell our virtual staff what you're looking for</li>
              <li>They'll help find perfect items just for you</li>
              <li>Get personalized recommendations based on your preferences</li>
            </ol>
          </div>
          
          <div className="text-sm text-gray-600 italic">
            Our AI assistant is ready to make your shopping experience amazing!
          </div>
        </div>
        
        <Button 
          onClick={initialize}
          className="px-8 py-2 text-lg hover:scale-105 transition-transform"
        >
          Begin Your Shopping Adventure
        </Button>
      </div>
    </div>
  );
};
