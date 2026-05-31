import { useState, useEffect } from "react";

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

export function usePrograms() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/programs", {
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
      .then((data: Course[]) => {
        setCourses(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return { courses, loading, error };
}
