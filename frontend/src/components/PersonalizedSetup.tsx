import { useState, FormEvent } from "react";
import { savePreferences, SkillLevel, PersonalizationResponse } from "../api/client";

const ALL_DAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
] as const;

const SKILL_LEVELS: SkillLevel[] = ["beginner", "intermediate", "advanced"];

interface RoadmapTopicOption {
  id: number;
  title: string;
}

interface PersonalizedSetupProps {
  userId: number;
  roadmapId: number;
  /** Topics from Module 2's roadmap, so the user can mark ones they already know. */
  roadmapTopics?: RoadmapTopicOption[];
  onSaved?: (saved: PersonalizationResponse) => void;
}

interface FormState {
  learning_goal: string;
  hours_per_day: number;
  available_days: string[];
  target_date: string;
  skill_level: SkillLevel;
  known_topic_ids: number[];
}

const initialForm: FormState = {
  learning_goal: "",
  hours_per_day: 2,
  available_days: [],
  target_date: "",
  skill_level: "intermediate",
  known_topic_ids: [],
};

/**
 * Module 3 — Personalized Setup form.
 *
 * userId/roadmapId are passed in from wherever the app is in its flow
 * (e.g. after Module 2's roadmap selection screen). roadmapTopics is
 * optional — when provided, the user can check off topics they already
 * know so Module 4 skips them in the generated plan.
 */
export default function PersonalizedSetup({
  userId,
  roadmapId,
  roadmapTopics = [],
  onSaved,
}: PersonalizedSetupProps) {
  const [form, setForm] = useState<FormState>(initialForm);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function toggleDay(day: string) {
    setForm((f) => ({
      ...f,
      available_days: f.available_days.includes(day)
        ? f.available_days.filter((d) => d !== day)
        : [...f.available_days, day],
    }));
  }

  function toggleKnownTopic(topicId: number) {
    setForm((f) => ({
      ...f,
      known_topic_ids: f.known_topic_ids.includes(topicId)
        ? f.known_topic_ids.filter((id) => id !== topicId)
        : [...f.known_topic_ids, topicId],
    }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (form.available_days.length === 0) {
      setError("Select at least one available study day.");
      return;
    }
    if (!form.target_date) {
      setError("Pick a target completion date.");
      return;
    }

    setSaving(true);
    try {
      const saved = await savePreferences({
        user_id: userId,
        roadmap_id: roadmapId,
        ...form,
        hours_per_day: Number(form.hours_per_day),
      });
      onSaved?.(saved);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-5 rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
    >
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Personalize your plan</h2>
        <p className="mt-1 text-sm text-slate-500">
          Tell us how you want to study and we'll build your day-by-day plan.
        </p>
      </div>

      <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
        Learning goal
        <input
          type="text"
          value={form.learning_goal}
          onChange={(e) => setForm({ ...form, learning_goal: e.target.value })}
          placeholder="e.g. Become job ready"
          required
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </label>

      <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
        Study hours per day
        <select
          value={form.hours_per_day}
          onChange={(e) => setForm({ ...form, hours_per_day: Number(e.target.value) })}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          {[1, 2, 3, 4, 5, 6, 8].map((h) => (
            <option key={h} value={h}>
              {h} hour{h > 1 ? "s" : ""}
            </option>
          ))}
        </select>
      </label>

      <fieldset className="rounded-lg border border-slate-200 p-3">
        <legend className="px-1 text-xs font-semibold text-slate-600">
          Available study days
        </legend>
        <div className="flex flex-wrap gap-x-4 gap-y-2 pt-1">
          {ALL_DAYS.map((day) => (
            <label
              key={day}
              className="inline-flex items-center gap-1.5 text-sm text-slate-700"
            >
              <input
                type="checkbox"
                checked={form.available_days.includes(day)}
                onChange={() => toggleDay(day)}
                className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              {day}
            </label>
          ))}
        </div>
      </fieldset>

      <label className="flex flex-col gap-1.5 text-sm font-medium text-slate-700">
        Target completion date
        <input
          type="date"
          value={form.target_date}
          onChange={(e) => setForm({ ...form, target_date: e.target.value })}
          required
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-normal text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
      </label>

      <fieldset className="rounded-lg border border-slate-200 p-3">
        <legend className="px-1 text-xs font-semibold text-slate-600">
          Current skill level
        </legend>
        <div className="flex gap-4 pt-1">
          {SKILL_LEVELS.map((level) => (
            <label
              key={level}
              className="inline-flex items-center gap-1.5 text-sm capitalize text-slate-700"
            >
              <input
                type="radio"
                name="skill_level"
                value={level}
                checked={form.skill_level === level}
                onChange={(e) => setForm({ ...form, skill_level: e.target.value as SkillLevel })}
                className="h-4 w-4 border-slate-300 text-indigo-600 focus:ring-indigo-500"
              />
              {level}
            </label>
          ))}
        </div>
      </fieldset>

      {roadmapTopics.length > 0 && (
        <fieldset className="rounded-lg border border-slate-200 p-3">
          <legend className="px-1 text-xs font-semibold text-slate-600">
            Topics you already know (optional — we'll skip these)
          </legend>
          <div className="flex flex-wrap gap-x-4 gap-y-2 pt-1">
            {roadmapTopics.map((topic) => (
              <label
                key={topic.id}
                className="inline-flex items-center gap-1.5 text-sm text-slate-700"
              >
                <input
                  type="checkbox"
                  checked={form.known_topic_ids.includes(topic.id)}
                  onChange={() => toggleKnownTopic(topic.id)}
                  className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                />
                {topic.title}
              </label>
            ))}
          </div>
        </fieldset>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={saving}
        className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {saving ? "Saving..." : "Create my plan"}
      </button>
    </form>
  );
}
