import { useState } from "react";
import { useNavigate } from "react-router-dom";

const features = [
  { icon: "📝", title: "Генерация конспектов", animClass: "icon-write" },
  { icon: "📚", title: "Систематизация знаний", animClass: "icon-stack" },
  { icon: "⏰", title: "Трекер дедлайнов", animClass: "icon-alarm" },
  { icon: "🔔", title: "Smart-уведомления", animClass: "icon-bell" },
];

export default function Welcome() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"welcome" | "auth">("welcome");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");

  const canSubmit = login.trim().length > 0 && password.trim().length > 0;

  const handleLogin = () => {
    if (canSubmit) {
      navigate("/");
    }
  };

  return (
    <div
      className="min-h-full flex flex-col items-center px-6 py-10 text-center"
      style={{
        background: "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
      }}
    >
      {/* Logo */}
      <img
        src="/logo.png"
        alt="StudyCore"
        className="w-[200px] h-[200px] object-contain mb-[-40px]"
      />

      {/* Title */}
      <h1
        className="text-5xl font-bold mb-2"
        style={{ color: "#fff", letterSpacing: "-1px", textShadow: "0 0 10px rgba(138, 43, 226, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)" }}
      >
        StudyCore
      </h1>

      {/* Subtitle */}
      <p
        className="text-base mb-8 max-w-[300px] leading-relaxed"
        style={{ color: "#fff" }}
      >
        Ваш персональный помощник в обучении
      </p>

      {mode === "welcome" && (
        <>
          {/* Features */}
          <div className="w-full max-w-[320px] flex flex-col gap-[17px] mb-8">
            {features.map((f) => (
              <div
                key={f.title}
                className="feature-card flex items-center gap-3 rounded-2xl p-3.5 text-left transition-transform duration-150 active:scale-[0.98] cursor-pointer"
                style={{
                  background: "rgba(15, 23, 42, 0.6)",
                  boxShadow: "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)",
                }}
              >
                <span className={`text-xl inline-block ${f.animClass}`}>{f.icon}</span>
                <span
                  className="text-sm font-medium"
                  style={{ color: "#fff" }}
                >
                  {f.title}
                </span>
              </div>
            ))}
          </div>

          {/* Auth button */}
          <button
            onClick={() => setMode("auth")}
            className="w-full max-w-[320px] py-4 rounded-2xl font-medium text-sm transition-all duration-200 hover:shadow-xl hover:brightness-110 active:scale-95"
            style={{
              background: "#8a2be2",
              color: "#fff",
              boxShadow: "0 0 10px rgba(138, 43, 226, 0.6), 0 0 20px rgba(138, 43, 226, 0.3), 0 0 40px rgba(0, 240, 255, 0.2)",
              textShadow: "0 0 5px rgba(255,255,255,0.5)",
            }}
          >
            Войти с помощью «Нетологии»
          </button>
        </>
      )}

      {mode === "auth" && (
        <div className="w-full max-w-[320px] flex flex-col gap-4">
          <h2
            className="text-lg font-semibold mb-1"
            style={{ color: "#fff" }}
          >
            Вход в Нетологию
          </h2>

          <input
            type="text"
            placeholder="Email / Логин"
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            className="w-full px-4 py-3.5 rounded-2xl text-sm outline-none transition-all focus:ring-2"
            style={{
              background: "rgba(255,255,255,0.15)",
              color: "#fff",
              border: "1px solid rgba(255,255,255,0.2)",
            }}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
          />

          <input
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-3.5 rounded-2xl text-sm outline-none transition-all focus:ring-2"
            style={{
              background: "rgba(255,255,255,0.15)",
              color: "#fff",
              border: "1px solid rgba(255,255,255,0.2)",
            }}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
          />

          <button
            onClick={handleLogin}
            disabled={!canSubmit}
            className="w-full py-4 rounded-2xl font-medium text-sm transition-all duration-200 hover:shadow-xl hover:brightness-110 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{
              background: canSubmit ? "#8a2be2" : "rgba(138, 43, 226, 0.5)",
              color: "#fff",
              boxShadow: canSubmit
                ? "0 0 10px rgba(138, 43, 226, 0.6), 0 0 20px rgba(138, 43, 226, 0.3), 0 0 40px rgba(0, 240, 255, 0.2)"
                : "none",
              textShadow: canSubmit ? "0 0 5px rgba(255,255,255,0.5)" : "none",
            }}
          >
            Войти
          </button>

          <button
            onClick={() => setMode("welcome")}
            className="text-sm mt-1 transition-opacity hover:opacity-80"
            style={{ color: "rgba(255,255,255,0.6)" }}
          >
            ← Назад
          </button>

          {/* Security text */}
          <div className="flex items-center justify-center gap-1.5 text-xs mt-3 whitespace-nowrap">
            <span>🔒</span>
            <span style={{ color: "rgba(255,255,255,0.5)" }}>
              Ваши данные под надежной защитой.
            </span>
            <a
              href="#"
              className="underline transition-opacity hover:opacity-80"
              style={{ color: "rgba(255,255,255,0.6)" }}
            >
              Подробнее
            </a>
          </div>
        </div>
      )}

      {/* Version */}
      <p
        className="mt-auto pt-8 text-sm"
        style={{ color: "rgba(255,255,255,0.4)" }}
      >
        v1.0 MODEST
      </p>
    </div>
  );
}
