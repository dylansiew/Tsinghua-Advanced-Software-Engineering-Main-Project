// zustand/sample.ts
import { Video } from "@/types/video/video";
import { create } from "zustand";

type SelectedVideo = {
  video: Video | null;
  setSelectedVideo: (newVideo: Video | null) => void;
  //   removeAllBears: () => void;
};

const useSelectedVideo = create<SelectedVideo>((set) => ({
  video: null,
  setSelectedVideo: (newVideo) => set(() => ({ video: newVideo })),
}));

export default useSelectedVideo;
