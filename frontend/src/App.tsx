import { HashRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import MobileFrame from "./components/MobileFrame";
import BottomNav from "./components/BottomNav";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import PublicOnlyRoute from "./components/auth/PublicOnlyRoute";
import Welcome from "./pages/Welcome";
import Home from "./pages/Home";
import Notes from "./pages/Notes";
import NoteDetail from "./pages/NoteDetail";
import Deadlines from "./pages/Deadlines";
import Notifications from "./pages/Notifications";

export default function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <Routes>
          {/* Страница welcome — только для неавторизованных */}
          <Route element={<PublicOnlyRoute />}>
            <Route
              path="/welcome"
              element={
                <MobileFrame outerBg="#020617" bottomPadding={false}>
                  <Welcome />
                </MobileFrame>
              }
            />
          </Route>

          {/* Все остальные страницы — только для авторизованных */}
          <Route element={<ProtectedRoute />}>
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
          </Route>
        </Routes>
      </HashRouter>
    </AuthProvider>
  );
}
