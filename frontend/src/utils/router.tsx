import { AvatarOverlay } from "@/pages/Avatar/overlay/main";
import { BrowserRouter, Route, Routes } from "react-router";
import { VideoRouter } from "../pages/Video/main";

export const AppRouter = () => {
    return (
     <BrowserRouter>
        <Routes>
            <Route path="/" element={<VideoRouter />} />
            <Route path="/avatar" element={<AvatarOverlay />} />
        </Routes>
     </BrowserRouter>
    )
}