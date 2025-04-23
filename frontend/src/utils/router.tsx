import { AvatarOverlay } from "@/pages/Avatar/overlay/main";
import { BrowserRouter, Route, Routes } from "react-router";

export const AppRouter = () => {
    return (
     <BrowserRouter>
        <Routes>
            <Route path="/" element={<AvatarOverlay />} />
            <Route path="/avatar" element={<AvatarOverlay />} />
        </Routes>
     </BrowserRouter>
    )
}