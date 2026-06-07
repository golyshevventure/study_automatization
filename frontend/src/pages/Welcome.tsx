import { useState } from "react";
import { useAuth } from "../contexts/AuthContext";

/**
 * Список функций приложения, отображаемых на экране приветствия.
 * Каждая функция имеет иконку, название и CSS-класс анимации.
 */
const features = [
  { icon: "📝", title: "Генерация конспектов", animClass: "icon-write" },
  { icon: "📚", title: "Систематизация знаний", animClass: "icon-stack" },
  { icon: "⏰", title: "Трекер дедлайнов", animClass: "icon-alarm" },
  { icon: "🔔", title: "Smart-уведомления", animClass: "icon-bell" },
];

/**
 * Компонент страницы приветствия (Welcome / Auth).
 *
 * Состояния:
 *  - "welcome" — экран с логотипом, функциями и кнопкой входа
 *  - "auth"    — форма ввода email/пароля
 *
 * Авторизация:
 *  При нажатии "Войти" отправляется POST-запрос на FastAPI backend
 *  (localhost:8000/api/auth/netology). В случае успеха — редирект
 *  на главную страницу "/". При ошибке — отображается текст ошибки.
 */
export default function Welcome() {
  // -------------------------------------------------------------------------
  // Состояния UI
  // -------------------------------------------------------------------------
  // mode: "welcome" | "auth" — текущий экран
  // login / password: значения полей ввода
  // error: текст ошибки (null = нет ошибки)
  // isLoading: идёт ли сейчас запрос на сервер
  // -------------------------------------------------------------------------
  const [mode, setMode] = useState<"welcome" | "auth">("welcome");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  /**
   * Проверяет, можно ли отправить форму.
   * Кнопка активна только если оба поля непустые.
   */
  const canSubmit = login.trim().length > 0 && password.trim().length > 0;

  /**
   * Обработчик нажатия кнопки "Войти".
   *
   * Отправляет POST-запрос на FastAPI backend с email и password.
   * При успехе (success: true) — редирект на "/".
   * При 401 (invalid_credentials) — показывает "Неверный логин или пароль".
   * При сетевой ошибке — показывает "Ошибка авторизации. Попробуйте ещё раз".
   */
  const { login: authLogin } = useAuth();

  const handleLogin = async () => {
    if (!canSubmit || isLoading) return;

    setError(null);
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/auth/netology", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: login, password }),
        credentials: "include",
      });

      const data = await res.json();

      if (data.success) {
        // Успешная авторизация — обновляем AuthContext, router сам редиректит
        authLogin();
      } else if (data.error === "invalid_credentials") {
        setError("Неверный логин или пароль");
      } else {
        setError("Ошибка авторизации. Попробуйте ещё раз");
      }
    } catch (e) {
      setError("Ошибка авторизации. Попробуйте ещё раз");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="min-h-full flex flex-col items-center px-6 py-10 text-center"
      style={{
        background:
          "radial-gradient(circle at 10% 10%, rgba(138, 43, 226, 0.25), transparent 50%), radial-gradient(circle at 90% 90%, rgba(138, 43, 226, 0.15), transparent 50%), #020617",
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
        style={{
          color: "#fff",
          letterSpacing: "-1px",
          textShadow:
            "0 0 10px rgba(138, 43, 226, 0.5), 0 0 20px rgba(0, 240, 255, 0.3)",
        }}
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

      {/* ================================================================== */}
      {/* Экран приветствия (mode === "welcome")                              */}
      {/* ================================================================== */}
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
                  boxShadow:
                    "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)",
                }}
              >
                <span className={`text-xl inline-block ${f.animClass}`}>
                  {f.icon}
                </span>
                <span
                  className="text-sm font-medium"
                  style={{ color: "#fff" }}
                >
                  {f.title}
                </span>
              </div>
            ))}
          </div>

          {/* Auth button — переключает на экран авторизации */}
          <button
            onClick={() => setMode("auth")}
            className="w-full max-w-[320px] py-4 rounded-2xl font-medium text-sm transition-all duration-200 hover:shadow-xl hover:brightness-110 active:scale-95"
            style={{
              background: "#8a2be2",
              color: "#fff",
              boxShadow:
                "0 0 10px rgba(138, 43, 226, 0.6), 0 0 20px rgba(138, 43, 226, 0.3), 0 0 40px rgba(0, 240, 255, 0.2)",
              textShadow: "0 0 5px rgba(255,255,255,0.5)",
            }}
          >
            Войти с помощью «Нетологии»
          </button>
        </>
      )}

      {/* ================================================================== */}
      {/* Экран авторизации (mode === "auth")                                 */}
      {/* ================================================================== */}
      {mode === "auth" && (
        <div className="w-full max-w-[320px] flex flex-col gap-4">
          {/* Заголовок формы */}
          <h2
            className="text-lg font-semibold mb-1"
            style={{ color: "#fff" }}
          >
            Вход в Нетологию
          </h2>

          {error && (
            <div
              className="text-sm text-center font-medium px-3 py-2 rounded-xl"
              style={{
                color: "#ef4444",
                background: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.3)",
              }}
            >
              {error}
            </div>
          )}

          {/* Поле email */}
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
            disabled={isLoading}
          />

          {/* Поле пароля */}
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
            disabled={isLoading}
          />

          {/* Кнопка "Войти" */}
          {/*
            Состояния:
              - disabled (!canSubmit || isLoading) — серая, неактивна
              - isLoading — показывает спиннер вместо текста
              - canSubmit && !isLoading — фиолетовая, активна
          */}
          <button
            onClick={handleLogin}
            disabled={!canSubmit || isLoading}
            className="w-full py-4 rounded-2xl font-medium text-sm transition-all duration-200 hover:shadow-xl hover:brightness-110 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            style={{
              background: canSubmit && !isLoading ? "#8a2be2" : "rgba(138, 43, 226, 0.5)",
              color: "#fff",
              boxShadow:
                canSubmit && !isLoading
                  ? "0 0 10px rgba(138, 43, 226, 0.6), 0 0 20px rgba(138, 43, 226, 0.3), 0 0 40px rgba(0, 240, 255, 0.2)"
                  : "none",
              textShadow:
                canSubmit && !isLoading
                  ? "0 0 5px rgba(255,255,255,0.5)"
                  : "none",
            }}
          >
            {isLoading ? (
              <>
                {/* CSS-спиннер (анимация вращения) */}
                <span
                  className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"
                  style={{ animationDuration: "0.8s" }}
                />
                <span>Вход...</span>
              </>
            ) : (
              "Войти"
            )}
          </button>

          {/* Кнопка "Назад" */}
          <button
            onClick={() => {
              setMode("welcome");
              setError(null);
              setLogin("");
              setPassword("");
            }}
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
