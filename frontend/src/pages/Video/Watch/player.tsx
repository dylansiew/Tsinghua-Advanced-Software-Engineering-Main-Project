import useSelectedVideo from "@/zustand/Video/SelectedVideo";
import { VideoLoading } from "./loading";

export const VideoPlayer = () => {
  const { video } = useSelectedVideo();

  if (!video) return <VideoLoading />;
  return (
    <div className="w-full">
      <video
        src="/Tests/vid1.mp4"
        className="w-full rounded-md"
        controls
        autoPlay
      />
      <div className="p-2 flex flex-col">
        <div className="font-bold text-3xl sm:text-4xl lg:text-5xlw">
          {video?.title}
        </div>
      </div>
    </div>
  );
};
