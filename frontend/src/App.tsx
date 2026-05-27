import { HashRouter, Routes, Route } from "react-router-dom";
import MobileFrame from "./components/MobileFrame";
import BottomNav from "./components/BottomNav";
import Welcome from "./pages/Welcome";
import Home from "./pages/Home";
import Notes from "./pages/Notes";
import NoteDetail from "./pages/NoteDetail";
import Deadlines from "./pages/Deadlines";
import Notifications from "./pages/Notifications";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route
          path="/welcome"
          element={
            <MobileFrame outerBg="#020617" bottomPadding={false}>
              <Welcome />
            </MobileFrame>
          }
        />
        <Route
          path="*"
          element={
            <MobileFrame>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/notes" element={<Notes />} />
                <Route path="/notes/:id" element={<NoteDetail />} />
                <Route path="/deadlines" element={<Deadlines />} />
                <Route path="/notifications" element={<Notifications />} />
              </Routes>
              <BottomNav />
            </MobileFrame>
          }
        />
      </Routes>
    </HashRouter>
  );
}
