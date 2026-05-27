import { useState } from "react";
import { Bell, AlertCircle, AlertTriangle, Info, CheckCheck } from "lucide-react";
import { notifications as initialNotifications } from "../data";

type NotificationType = "important" | "warning" | "info";

const typeConfig: Record<NotificationType, { icon: typeof AlertCircle; bg: string; color: string; label: string }> = {
  important: { icon: AlertCircle, bg: "rgba(239, 68, 68, 0.15)", color: "#EF4444", label: "Важное" },
  warning: { icon: AlertTriangle, bg: "rgba(245, 158, 11, 0.15)", color: "#F59E0B", label: "Напоминание" },
  info: { icon: Info, bg: "rgba(99, 102, 241, 0.15)", color: "#6366F1", label: "Инфо" },
};

export default function Notifications() {
  const [notifs, setNotifs] = useState(initialNotifications);
  const unreadCount = notifs.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifs((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  return (
    <div className="pb-4">
      {/* Header */}
      <div className="px-5 pt-8 pb-4 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold" style={{ color: "#F1F5F9" }}>
              Уведомления
            </h1>
            {unreadCount > 0 && (
              <span
                className="px-2 py-0.5 rounded-full text-xs font-bold"
                style={{ background: "#EF4444", color: "#fff" }}
              >
                {unreadCount}
              </span>
            )}
          </div>
          <p className="text-sm mt-1" style={{ color: "#94A3B8" }}>
            {unreadCount} непрочитанных
          </p>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={markAllRead}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-opacity active:opacity-70"
            style={{ background: "#1E293B", color: "#F59E0B" }}
          >
            <CheckCheck size={16} />
            Прочитать все
          </button>
        )}
      </div>

      {/* Notification Cards */}
      <div className="px-4 flex flex-col gap-3">
        {notifs.map((n) => {
          const config = typeConfig[n.type as NotificationType];
          const Icon = config.icon;
          return (
            <div
              key={n.id}
              className="rounded-2xl p-4 flex items-start gap-3 transition-opacity"
              style={{
                background: n.read ? "rgba(30, 41, 59, 0.6)" : "#1E293B",
                opacity: n.read ? 0.7 : 1,
              }}
            >
              {/* Icon Circle */}
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                style={{ background: config.bg }}
              >
                <Icon size={18} color={config.color} />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p
                    className="text-sm font-medium"
                    style={{ color: n.read ? "#94A3B8" : "#F1F5F9" }}
                  >
                    {n.title}
                  </p>
                  <span
                    className="text-xs font-medium px-2 py-0.5 rounded-full shrink-0"
                    style={{ background: config.bg, color: config.color }}
                  >
                    {config.label}
                  </span>
                </div>
                <p className="text-xs mt-1 leading-relaxed" style={{ color: "#94A3B8" }}>
                  {n.text}
                </p>
                <p className="text-xs mt-2" style={{ color: "#64748B" }}>
                  {n.time}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {notifs.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16">
          <Bell size={48} color="#334155" />
          <p className="text-sm mt-3" style={{ color: "#94A3B8" }}>
            Уведомлений пока нет
          </p>
        </div>
      )}
    </div>
  );
}
