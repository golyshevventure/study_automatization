import type { ReactNode } from "react";

export default function MobileFrame({
  children,
  outerBg = "#0B1120",
  bottomPadding = true,
}: {
  children: ReactNode;
  outerBg?: string;
  bottomPadding?: boolean;
}) {
  return (
    <div
      className="min-h-screen w-full flex justify-center items-start pt-4 pb-4"
      style={{ background: outerBg }}
    >
      <div
        className="w-full max-w-[420px] rounded-[40px] overflow-hidden shadow-2xl relative flex flex-col"
        style={{ background: "var(--bg-primary)", height: "812px", maxHeight: "95vh" }}
      >
        <div className={bottomPadding ? "flex-1 overflow-y-auto hide-scrollbar pb-20" : "flex-1 overflow-y-auto hide-scrollbar"}>
          {children}
        </div>
      </div>
    </div>
  );
}
