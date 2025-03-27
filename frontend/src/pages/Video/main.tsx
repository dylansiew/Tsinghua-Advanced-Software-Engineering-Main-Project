import useSelectedVideo from "@/zustand/Video/SelectedVideo";
import { Fragment } from "react/jsx-runtime";
import { AppAvatar } from "../Avatar/main";
import { SearchBar } from "../SearchBar/main";
import { VideoSelection } from "./Selection/main";
import { VideoWatch } from "./Watch/main";

export const VideoRouter = () => {
  const { video } = useSelectedVideo();

  return (
    <Fragment>
      <SearchBar />
      {video ? <VideoWatch /> : <VideoSelection />}
      <AppAvatar />
    </Fragment>
  );
};
