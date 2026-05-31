import { useQuery } from "@tanstack/react-query";
import type { Course } from "./usePrograms";

async function fetchCourse(programId: string): Promise<Course> {
  const res = await fetch(`http://localhost:8000/api/programs/${programId}`, {
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export function useCourse(programId: string | undefined, initialData?: Course) {
  const { data: course, isLoading: loading, error } = useQuery({
    queryKey: ["course", programId],
    queryFn: () => fetchCourse(programId!),
    enabled: !!programId,
    initialData,
  });

  return {
    course: course ?? null,
    loading,
    error: error ? (error as Error).message : null,
  };
}
