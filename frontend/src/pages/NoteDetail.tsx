import { ArrowLeft, Tag } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { noteContent } from "../data";

export default function NoteDetail() {
  const navigate = useNavigate();

  return (
    <div className="pb-6">
      {/* Gradient Header */}
      <div
        className="px-5 pt-8 pb-6"
        style={{ background: "linear-gradient(135deg, #6366F1, #8B5CF6)" }}
      >
        <button
          onClick={() => navigate("/notes")}
          className="flex items-center gap-2 mb-4"
          style={{ color: "rgba(255,255,255,0.8)" }}
        >
          <ArrowLeft size={20} />
          <span className="text-sm">Назад</span>
        </button>

        <div
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium mb-3"
          style={{ background: "rgba(255,255,255,0.2)", color: "#fff" }}
        >
          <Tag size={12} />
          {noteContent.subject}
        </div>

        <h1 className="text-xl font-bold leading-tight" style={{ color: "#fff" }}>
          {noteContent.title}
        </h1>

        <p className="text-sm mt-2" style={{ color: "rgba(255,255,255,0.6)" }}>
          {noteContent.date}
        </p>
      </div>

      {/* Tags */}
      <div className="px-4 mt-4 flex gap-2">
        {noteContent.tags.map((tag) => (
          <span
            key={tag}
            className="px-3 py-1.5 rounded-full text-xs font-medium"
            style={{ background: "#1E293B", color: "#F59E0B" }}
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Content */}
      <div className="px-4 mt-4">
        <div
          className="rounded-2xl p-5"
          style={{ background: "#1E293B" }}
        >
          {noteContent.sections.map((section, idx) => (
            <div key={idx} className={idx > 0 ? "mt-5 pt-5" : ""} style={idx > 0 ? { borderTop: "1px solid #334155" } : {}}>
              <h3
                className="text-sm font-semibold mb-2"
                style={{ color: "#F59E0B" }}
              >
                {section.heading}
              </h3>
              {section.text && (
                <p className="text-sm leading-relaxed" style={{ color: "#F1F5F9" }}>
                  {section.text}
                </p>
              )}
              {section.items && (
                <ul className="flex flex-col gap-1.5">
                  {section.items.map((item, i) => (
                    <li
                      key={i}
                      className="text-sm flex items-start gap-2"
                      style={{ color: "#F1F5F9" }}
                    >
                      <span style={{ color: "#F59E0B" }}>•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="px-4 mt-4 flex gap-3">
        <button
          className="flex-1 py-3 rounded-xl text-sm font-medium transition-opacity active:opacity-80"
          style={{ background: "#F59E0B", color: "#1E293B" }}
        >
          Редактировать
        </button>
        <button
          className="flex-1 py-3 rounded-xl text-sm font-medium transition-opacity active:opacity-80"
          style={{ background: "#334155", color: "#F1F5F9" }}
        >
          Поделиться
        </button>
      </div>
    </div>
  );
}
