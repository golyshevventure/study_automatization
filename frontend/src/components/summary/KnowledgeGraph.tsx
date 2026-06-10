import { useState, useEffect, useRef } from "react";
import { Loader2, Maximize2 } from "lucide-react";
import ForceGraph2D from "react-force-graph-2d";
import { getKnowledgeGraph, type GraphNode, type GraphEdge } from "../../api/summary";

interface Props {
  onNodeClick?: (node: GraphNode) => void;
}

export default function KnowledgeGraph({ onNodeClick }: Props) {
  const [data, setData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getKnowledgeGraph()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 size={20} color="#B794F6" className="animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <p className="text-xs text-center py-4" style={{ color: "#EF4444" }}>
        {error}
      </p>
    );
  }

  if (!data || data.nodes.length === 0) {
    return (
      <p className="text-xs text-center py-4" style={{ color: "#64748B" }}>
        Нет данных для графа
      </p>
    );
  }

  const graphData = {
    nodes: data.nodes.map((n) => ({
      id: n.id,
      label: n.label,
      type: n.type,
      color: n.color || "#94A3B8",
      val: n.type === "program" ? 8 : n.type === "module" ? 5 : 3,
    })),
    links: data.edges.map((e) => ({ source: e.source, target: e.target })),
  };

  const width = containerRef.current?.clientWidth || 300;
  const height = expanded ? 500 : 250;

  return (
    <div ref={containerRef} className="relative">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold" style={{ color: "#fff" }}>
          Граф знаний
        </h3>
        <button onClick={() => setExpanded(!expanded)} className="p-1">
          <Maximize2 size={14} color="#64748B" />
        </button>
      </div>
      <div
        className="rounded-xl overflow-hidden"
        style={{
          background: "rgba(15,23,42,0.6)",
          border: "1px solid rgba(138,43,226,0.2)",
        }}
      >
        <ForceGraph2D
          graphData={graphData}
          width={width}
          height={height}
          nodeAutoColorBy="type"
          nodeLabel="label"
          linkColor={() => "rgba(148,163,184,0.3)"}
          backgroundColor="transparent"
          onNodeClick={(node: any) => {
            const original = data.nodes.find((n) => n.id === node.id);
            if (original && onNodeClick) onNodeClick(original);
          }}
          nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
            const label = node.label as string;
            const fontSize = 12 / globalScale;
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.fillStyle = node.color as string;
            ctx.beginPath();
            ctx.arc(node.x!, node.y!, (node.val as number) / globalScale, 0, 2 * Math.PI);
            ctx.fill();
            ctx.fillStyle = "#fff";
            ctx.fillText(
              label.length > 20 ? label.slice(0, 20) + "…" : label,
              node.x! + (node.val as number) / globalScale + 2,
              node.y! + fontSize / 3
            );
          }}
        />
      </div>
    </div>
  );
}
