import { useState, useEffect } from "react";
import type { Course } from "./usePrograms";

export function useCourse(programId: string | undefined) {
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!programId) {
      setLoading(false);
      setError("ID курса не указан");
      return;
    }

    fetch(`http://localhost:8000/api/programs/${programId}`, {
      credentials: "include",
      headers: { Accept: "application/json" },
    })
      .then(async (res) => {
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || `HTTP ${res.status}`);
        }
        return res.json();
      })
      .then((data: Course) => {
        setCourse(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [programId]);

  return { course, loading, error };
}
