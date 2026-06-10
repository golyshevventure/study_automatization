/**
 * API-клиент для модуля «Генерация конспектов».
 */

const API_BASE = "http://localhost:8000/api";

async function fetchWithAuth(path: string, options: RequestInit = {}): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res;
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface NetologyProgram {
  id: string;
  netology_id: string;
  title: string;
  program_type: string;
}

export interface NetologyModule {
  id: string;
  netology_id: string;
  title: string;
  program_id: string;
}

export interface NetologyLessonItem {
  id: string;
  netology_id: string;
  title: string;
  item_type: string;
  has_vtt: boolean;
}

export interface ConspectJob {
  id: string;
  status: string;
  error_message: string | null;
  retry_count: number;
  conspect_id: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface DefinitionItem {
  term: string;
  definition: string;
}

export interface Conspect {
  id: string;
  title: string;
  topic: string | null;
  summary: string | null;
  key_points: string[] | null;
  definitions: DefinitionItem[] | null;
  difficulty: number | null;
  raw_vtt_length: number | null;
  is_edited: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConspectListResponse {
  items: Conspect[];
  total: number;
}

// ---------------------------------------------------------------------------
// Programs / Modules / Webinars
// ---------------------------------------------------------------------------

export async function getPrograms(): Promise<NetologyProgram[]> {
  const res = await fetchWithAuth("/summary/programs");
  return res.json();
}

export async function syncPrograms(): Promise<NetologyProgram[]> {
  const res = await fetchWithAuth("/summary/programs/sync", { method: "POST" });
  return res.json();
}

export async function getProgramModules(programId: string): Promise<NetologyModule[]> {
  const res = await fetchWithAuth(`/summary/programs/${programId}/modules`);
  return res.json();
}

export async function getModuleWebinars(moduleId: string): Promise<NetologyLessonItem[]> {
  const res = await fetchWithAuth(`/summary/modules/${moduleId}/webinars`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Conspect Generation
// ---------------------------------------------------------------------------

export async function generateConspect(lessonItemId: string): Promise<ConspectJob> {
  const res = await fetchWithAuth("/summary/conspects/generate", {
    method: "POST",
    body: JSON.stringify({ lesson_item_id: lessonItemId }),
  });
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<ConspectJob> {
  const res = await fetchWithAuth(`/summary/conspects/jobs/${jobId}`);
  return res.json();
}

// ---------------------------------------------------------------------------
// Conspect CRUD
// ---------------------------------------------------------------------------

export async function getConspects(
  q?: string,
  programId?: string,
  moduleId?: string,
  limit = 20,
  offset = 0
): Promise<ConspectListResponse> {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (q) params.set("q", q);
  if (programId) params.set("program_id", programId);
  if (moduleId) params.set("module_id", moduleId);
  const res = await fetchWithAuth(`/summary/conspects?${params}`);
  return res.json();
}

export async function getConspect(id: string): Promise<Conspect> {
  const res = await fetchWithAuth(`/summary/conspects/${id}`);
  return res.json();
}

export async function updateConspect(
  id: string,
  data: Partial<Pick<Conspect, "title" | "summary" | "key_points" | "definitions">>
): Promise<Conspect> {
  const res = await fetchWithAuth(`/summary/conspects/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteConspect(id: string): Promise<void> {
  await fetchWithAuth(`/summary/conspects/${id}`, { method: "DELETE" });
}

export async function getRecentConspects(): Promise<Conspect[]> {
  const res = await fetchWithAuth("/summary/conspects/recent");
  return res.json();
}

// ---------------------------------------------------------------------------
// Knowledge Graph
// ---------------------------------------------------------------------------

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  color: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
}

export interface KnowledgeGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export async function getKnowledgeGraph(): Promise<KnowledgeGraphData> {
  const res = await fetchWithAuth("/summary/knowledge-graph");
  return res.json();
}
