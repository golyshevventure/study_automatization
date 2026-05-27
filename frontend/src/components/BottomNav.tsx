import { Home, BookOpen, Clock, Bell } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { notifications } from "../data";

const tabs = [
  { icon: Home, label: "Главная", path: "/" },
  { icon: BookOpen, label: "Конспекты", path: "/notes" },
  { icon: Clock, label: "Дедлайны", path: "/deadlines" },
  { icon: Bell, label: "Уведомления", path: "/notifications" },
];

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <nav
      className="absolute bottom-0 left-0 right-0 flex justify-around items-center py-3 px-2 z-50"
      style={{
        background: "#1E293B",
        borderTop: "1px solid #334155",
      }}
    >
      {tabs.map((tab) => {
        const isActive = location.pathname === tab.path;
        const Icon = tab.icon;
        return (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className="flex flex-col items-center gap-1 relative px-3 py-1 transition-colors"
          >
            <div className="relative">
              <Icon
                size={24}
                color={isActive ? "#B794F6" : "#94A3B8"}
                strokeWidth={isActive ? 2.5 : 2}
                style={isActive ? { filter: "drop-shadow(0 0 4px rgba(183, 148, 246, 0.5))" } : undefined}
              />
              {tab.path === "/notifications" && unreadCount > 0 && (
                <span
                  className="absolute -top-2 -right-3 text-xs font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1"
                  style={{ background: "#EF4444", color: "#fff", fontSize: "10px" }}
                >
                  {unreadCount}
                </span>
              )}
            </div>
            <span
              className="text-xs font-medium"
              style={isActive ? { color: "#B794F6", textShadow: "0 0 5px rgba(183, 148, 246, 0.5)" } : { color: "#94A3B8" }}
            >
              {tab.label}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
