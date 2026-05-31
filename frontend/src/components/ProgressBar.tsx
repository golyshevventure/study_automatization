interface ProgressBarProps {
  progress: number;
  height?: number;
  showGlow?: boolean;
}

export default function ProgressBar({
  progress,
  height = 8,
  showGlow = true,
}: ProgressBarProps) {
  return (
    <div
      className="w-full rounded-full"
      style={{ background: "#334155", height }}
    >
      <div
        className="rounded-full transition-all"
        style={{
          width: `${progress}%`,
          height,
          background: "#8a2be2",
          boxShadow:
            showGlow && progress > 0
              ? "0 0 6px rgba(138, 43, 226, 0.5)"
              : "none",
        }}
      />
    </div>
  );
}
