import { useQuery } from "@tanstack/react-query";

export interface CourseModule {
  title: string;
  progress: number;
  link?: string;
}

export interface Course {
  id: number;
  title: string;
  type: string;
  progress: number;
  passed: boolean;
  modules: CourseModule[];
}

const PROGRAMS_QUERY_KEY = ["programs"];

async function fetchPrograms(): Promise<Course[]> {
  const res = await fetch("http://localhost:8000/api/programs", {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function usePrograms() {
  const { data: courses, isLoading: loading, error } = useQuery({
    queryKey: PROGRAMS_QUERY_KEY,
    queryFn: fetchPrograms,
  });

  return {
    courses: courses ?? [],
    loading,
    error: error ? (error as Error).message : null,
  };
}

export { PROGRAMS_QUERY_KEY };
