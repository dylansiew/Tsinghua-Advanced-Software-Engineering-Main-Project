import { AspectRatio } from "@/components/ui/aspect-ratio";
import { Video } from "@/types/video/video";
import useSelectedVideo from "@/zustand/Video/SelectedVideo";

interface VideoCardProps {
  video: Video;
}
export const VideoCard: React.FC<VideoCardProps> = ({ video }) => {
  const { setSelectedVideo } = useSelectedVideo();
  function handleSelectVideo() {
    setSelectedVideo(video);
  }
  return (
    <div
      className="p-3 w-[350px] cursor-pointer gap-2 flex flex-col"
      onClick={handleSelectVideo}
    >
      <AspectRatio ratio={16 / 9} className="">
        <img src={`/Tests/img1.png`} className="rounded-xl object-cover" />
      </AspectRatio>
      <div className="font-bold text-2xl sm:text-3xl">{video.title}</div>
    </div>
  );
};
