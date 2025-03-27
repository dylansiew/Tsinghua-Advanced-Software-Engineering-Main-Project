import useSelectedVideo from "@/zustand/Video/SelectedVideo";
import { VideoLoading } from "./loading";
import { VideoPlayer } from "./player";

export const VideoWatch = () => {
  const {video} = useSelectedVideo()

  if (!video) return <VideoLoading />;
  return (
    <div className="w-full">
      <VideoPlayer />
    </div>
  );
};
