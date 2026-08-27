/**
 * Typed API client for Module 3 + Module 4 backend.
 * Base URL comes from an env var so it's easy to point at a different
 * host once this merges into the team's shared backend.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// ---- Shared types (mirror backend/app/schemas/*.py) ---------------------

export type SkillLevel = "beginner" | "intermediate" | "advanced";

export interface PersonalizationPayload {
  user_id: number;
  roadmap_id: number;
  learning_goal: string;
  hours_per_day: number;
  available_days: string[];
  target_date: string; // YYYY-MM-DD
  skill_level: SkillLevel;
  known_topic_ids: number[];
}

export interface PersonalizationResponse extends PersonalizationPayload {
  id: number;
  created_at: string;
  updated_at: string;
}

export type TaskType = "learning" | "practice" | "quiz" | "revision" | "project";
export type TaskStatus = "pending" | "in_progress" | "completed" | "missed";

export interface TaskOut {
  id: number;
  day_number: number;
  date: string;
  topic_title: string;
  task_title: string;
  description: string | null;
  estimated_minutes: number;
  task_type: TaskType;
  status: TaskStatus;
}

export interface DayOut {
  day: number;
  date: string;
  tasks: TaskOut[];
  total_minutes: number;
}

export interface LearningPlanResponse {
  plan_id: number;
  user_id: number;
  roadmap_id: number;
  start_date: string;
  target_date: string;
  status: string;
  days: DayOut[];
}

export interface ApiErrorBody {
  detail?: string | { msg: string }[] | unknown;
}

export class ApiError extends Error {}

// ---- Internal request helper -------------------------------------------

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    let detail: unknown;
    try {
      detail = ((await res.json()) as ApiErrorBody).detail;
    } catch {
      detail = res.statusText;
    }
    const message =
      typeof detail === "string" ? detail : JSON.stringify(detail ?? res.statusText);
    throw new ApiError(message);
  }

  return res.json() as Promise<T>;
}

// ---- Module 3: Personalization ----------------------------------------

export function savePreferences(
  payload: Omit<PersonalizationPayload, "known_topic_ids"> & {
    known_topic_ids?: number[];
  }
): Promise<PersonalizationResponse> {
  return request("/api/personalization", {
    method: "POST",
    body: JSON.stringify({ known_topic_ids: [], ...payload }),
  });
}

export function getPreferences(
  userId: number,
  roadmapId: number
): Promise<PersonalizationResponse> {
  return request(`/api/personalization/${userId}/${roadmapId}`);
}

// ---- Module 4: Learning Plan --------------------------------------------

export function generatePlan(params: {
  userId: number;
  roadmapId: number;
  useAi?: boolean;
}): Promise<LearningPlanResponse> {
  const { userId, roadmapId, useAi = false } = params;
  return request("/api/learning-plans/generate", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, roadmap_id: roadmapId, use_ai: useAi }),
  });
}

export function getPlan(planId: number): Promise<LearningPlanResponse> {
  return request(`/api/learning-plans/${planId}`);
}

export function getTodayTasks(userId: number): Promise<DayOut> {
  return request(`/api/learning-plans/today/${userId}`);
}

export function adaptPlan(
  planId: number,
  taskUpdates: { task_id: number; status: TaskStatus }[]
): Promise<LearningPlanResponse> {
  return request(`/api/learning-plans/${planId}/adapt`, {
    method: "POST",
    body: JSON.stringify({ task_updates: taskUpdates }),
  });
}
