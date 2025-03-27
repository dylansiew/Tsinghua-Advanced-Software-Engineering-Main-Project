import { TEST_VIDEOS, Video } from "@/types/video/video";
import { useState } from "react";
import { VideoCard } from "./card";


export const VideoSelection = () => {
  const [videos, setVideos] = useState<Video[]>(TEST_VIDEOS);
  return (
    <div className="flex flex-wrap gap-3 justify-center">
      {videos.map((entry, index) => (
        <VideoCard video={entry} key={index} />
      ))}
    </div>
  );
};
