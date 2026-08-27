import { useEffect, useState } from "react";
import {
  generatePlan,
  adaptPlan,
  LearningPlanResponse,
  TaskStatus,
  TaskType,
} from "../api/client";

const TASK_TYPE_STYLES: Record<TaskType, string> = {
  learning: "bg-blue-500",
  practice: "bg-emerald-500",
  quiz: "bg-amber-500",
  revision: "bg-purple-500",
  project: "bg-red-500",
};

interface LearningPlanViewProps {
  userId: number;
  roadmapId: number;
}

/**
 * Module 4 — displays the generated day-by-day learning plan and lets
 * the user mark tasks complete/missed, triggering adaptive re-planning.
 */
export default function LearningPlanView({ userId, roadmapId }: LearningPlanViewProps) {
  const [plan, setPlan] = useState<LearningPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedDay, setExpandedDay] = useState<number | null>(1);

  useEffect(() => {
    handleGenerate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, roadmapId]);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const result = await generatePlan({ userId, roadmapId, useAi: false });
      setPlan(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate plan.");
    } finally {
      setLoading(false);
    }
  }

  async function handleTaskStatusChange(taskId: number, status: TaskStatus) {
    if (!plan) return;
    try {
      const updated = await adaptPlan(plan.plan_id, [{ task_id: taskId, status }]);
      setPlan(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update task.");
    }
  }

  if (loading) {
    return <p className="text-sm text-slate-500">Generating your personalized plan...</p>;
  }
  if (error) {
    return <p className="text-sm text-red-600">Error: {error}</p>;
  }
  if (!plan) return null;

  return (
    <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h2 className="text-lg font-semibold text-slate-900">Your learning plan</h2>
      <p className="mt-1 text-sm text-slate-500">
        {plan.start_date} → {plan.target_date} · {plan.days.length} study days · status:{" "}
        {plan.status}
      </p>

      <div className="mt-4 flex flex-col gap-2.5">
        {plan.days.map((day) => (
          <div key={day.day} className="overflow-hidden rounded-lg border border-slate-200">
            <button
              type="button"
              onClick={() => setExpandedDay(expandedDay === day.day ? null : day.day)}
              className="w-full bg-slate-50 px-4 py-3 text-left text-sm text-slate-800 transition hover:bg-slate-100"
            >
              <span className="font-semibold">Day {day.day}</span> — {day.date} (
              {day.total_minutes} min)
            </button>

            {expandedDay === day.day && (
              <ul className="flex flex-col gap-3 px-4 py-3">
                {day.tasks.map((task) => (
                  <li key={task.id} className="flex items-start gap-2.5">
                    <span
                      className={`mt-1.5 h-2.5 w-2.5 flex-shrink-0 rounded-full ${
                        TASK_TYPE_STYLES[task.task_type] ?? "bg-slate-400"
                      }`}
                    />
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-slate-800">
                        {task.task_title}{" "}
                        <span className="font-normal text-slate-500">
                          ({task.estimated_minutes} min)
                        </span>
                      </div>
                      {task.description && (
                        <div className="mt-0.5 text-sm text-slate-500">{task.description}</div>
                      )}
                    </div>
                    <select
                      value={task.status}
                      onChange={(e) =>
                        handleTaskStatusChange(task.id, e.target.value as TaskStatus)
                      }
                      className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="pending">Pending</option>
                      <option value="in_progress">In progress</option>
                      <option value="completed">Completed</option>
                      <option value="missed">Missed</option>
                    </select>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
