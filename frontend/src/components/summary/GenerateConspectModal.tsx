import { useState, useEffect } from "react";
import { X, ChevronRight, Loader2, FileText } from "lucide-react";
import {
  getPrograms,
  getProgramModules,
  getModuleWebinars,
  generateConspect,
  type NetologyProgram,
  type NetologyModule,
  type NetologyLessonItem,
} from "../../api/summary";

interface Props {
  onClose: () => void;
  onJobCreated: (jobId: string) => void;
}

type Step = "program" | "module" | "webinar";

const neonShadow = "0 0 15px rgba(0, 240, 255, 0.3), 0 0 5px rgba(138, 43, 226, 0.3)";

export default function GenerateConspectModal({ onClose, onJobCreated }: Props) {
  const [step, setStep] = useState<Step>("program");
  const [programs, setPrograms] = useState<NetologyProgram[]>([]);
  const [modules, setModules] = useState<NetologyModule[]>([]);
  const [webinars, setWebinars] = useState<NetologyLessonItem[]>([]);
  const [selectedProgram, setSelectedProgram] = useState<NetologyProgram | null>(null);
  const [selectedModule, setSelectedModule] = useState<NetologyModule | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getPrograms()
      .then(setPrograms)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectProgram = async (program: NetologyProgram) => {
    setSelectedProgram(program);
    setLoading(true);
    setError(null);
    try {
      const mods = await getProgramModules(program.id);
      setModules(mods);
      setStep("module");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectModule = async (mod: NetologyModule) => {
    setSelectedModule(mod);
    setLoading(true);
    setError(null);
    try {
      const items = await getModuleWebinars(mod.id);
      setWebinars(items);
      setStep("webinar");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectWebinar = async (webinar: NetologyLessonItem) => {
    setLoading(true);
    setError(null);
    try {
      const job = await generateConspect(webinar.id);
      onJobCreated(job.id);
      onClose();
    } catch (e: any) {
      setError(e.message);
      setLoading(false);
    }
  };

  const stepTitles: Record<Step, string> = {
    program: "Выберите программу",
    module: "Выберите модуль",
    webinar: "Выберите вебинар",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-sm">
      <div
        className="w-full max-w-md rounded-t-3xl p-5 flex flex-col gap-4"
        style={{
          background: "#0F172A",
          maxHeight: "85vh",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold" style={{ color: "#fff", textShadow: neonShadow }}>
            {stepTitles[step]}
          </h2>
          <button onClick={onClose} className="p-1">
            <X size={20} color="#94A3B8" />
          </button>
        </div>

        {/* Breadcrumbs */}
        <div className="flex items-center gap-2 text-xs">
          {selectedProgram && (
            <>
              <span style={{ color: "#B794F6" }}>{selectedProgram.title}</span>
              <ChevronRight size={12} color="#64748B" />
            </>
          )}
          {selectedModule && (
            <span style={{ color: "#B794F6" }}>{selectedModule.title}</span>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-xl p-3 text-sm" style={{ background: "rgba(239,68,68,0.15)", color: "#EF4444" }}>
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={24} color="#B794F6" className="animate-spin" />
          </div>
        )}

        {/* Lists */}
        {!loading && step === "program" && (
          <div className="flex flex-col gap-2 overflow-y-auto" style={{ maxHeight: "60vh" }}>
            {programs.length === 0 && (
              <p className="text-sm text-center py-8" style={{ color: "#94A3B8" }}>
                Нет программ. Сначала войдите в Netology.
              </p>
            )}
            {programs.map((p) => (
              <button
                key={p.id}
                onClick={() => handleSelectProgram(p)}
                className="text-left rounded-xl p-4 flex items-center gap-3 transition-all active:scale-[0.98]"
                style={{ background: "rgba(15,23,42,0.6)", border: "1px solid rgba(138,43,226,0.2)" }}
              >
                <FileText size={18} color="#B794F6" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium" style={{ color: "#fff" }}>
                    {p.title}
                  </p>
                  <p className="text-xs" style={{ color: "#64748B" }}>
                    {p.program_type}
                  </p>
                </div>
                <ChevronRight size={16} color="#64748B" />
              </button>
            ))}
          </div>
        )}

        {!loading && step === "module" && (
          <div className="flex flex-col gap-2 overflow-y-auto" style={{ maxHeight: "60vh" }}>
            <button
              onClick={() => setStep("program")}
              className="text-xs py-2"
              style={{ color: "#B794F6" }}
            >
              ← Назад к программам
            </button>
            {modules.map((m) => (
              <button
                key={m.id}
                onClick={() => handleSelectModule(m)}
                className="text-left rounded-xl p-4 flex items-center gap-3 transition-all active:scale-[0.98]"
                style={{ background: "rgba(15,23,42,0.6)", border: "1px solid rgba(138,43,226,0.2)" }}
              >
                <FileText size={18} color="#B794F6" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium" style={{ color: "#fff" }}>
                    {m.title}
                  </p>
                </div>
                <ChevronRight size={16} color="#64748B" />
              </button>
            ))}
          </div>
        )}

        {!loading && step === "webinar" && (
          <div className="flex flex-col gap-2 overflow-y-auto" style={{ maxHeight: "60vh" }}>
            <button
              onClick={() => setStep("module")}
              className="text-xs py-2"
              style={{ color: "#B794F6" }}
            >
              ← Назад к модулям
            </button>
            {webinars.length === 0 && (
              <p className="text-sm text-center py-8" style={{ color: "#94A3B8" }}>
                Нет вебинаров с субтитрами в этом модуле.
              </p>
            )}
            {webinars.map((w) => (
              <button
                key={w.id}
                onClick={() => handleSelectWebinar(w)}
                className="text-left rounded-xl p-4 flex items-center gap-3 transition-all active:scale-[0.98]"
                style={{ background: "rgba(15,23,42,0.6)", border: "1px solid rgba(138,43,226,0.2)" }}
              >
                <FileText size={18} color="#B794F6" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium" style={{ color: "#fff" }}>
                    {w.title}
                  </p>
                  <p className="text-xs" style={{ color: "#64748B" }}>
                    {w.item_type}
                  </p>
                </div>
                <ChevronRight size={16} color="#64748B" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
