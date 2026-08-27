import { useState } from "react";
import PersonalizedSetup from "./components/PersonalizedSetup";
import LearningPlanView from "./components/LearningPlanView";

type Step = "setup" | "plan";

/**
 * Standalone demo app for Module 3 + Module 4.
 *
 * In the real team app, userId/roadmapId would come from auth (Module 1)
 * and roadmap selection (Module 2), and roadmapTopics would be fetched
 * from Module 2's API. Here they're hardcoded / from mock_roadmap.json
 * for testing this module in isolation.
 */
export default function App() {
  const userId = 25;
  const roadmapId = 101;

  // Mirrors backend/mock_roadmap.json — replace with a real fetch to
  // Module 2 once it exists.
  const roadmapTopics = [
    { id: 1, title: "HTML" },
    { id: 2, title: "CSS" },
    { id: 3, title: "JavaScript" },
    { id: 4, title: "Git" },
    { id: 5, title: "React" },
    { id: 6, title: "Node.js" },
    { id: 7, title: "Express" },
    { id: 8, title: "MongoDB" },
    { id: 9, title: "Projects" },
  ];

  const [step, setStep] = useState<Step>("setup");

  return (
    <div className="mx-auto max-w-2xl px-5 py-8 pb-20">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">AI Training Platform</h1>
        <p className="mt-1 text-sm text-slate-500">
          Modules 3 &amp; 4 — Personalized Setup + Learning Plan
        </p>
      </header>

      {step === "setup" && (
        <PersonalizedSetup
          userId={userId}
          roadmapId={roadmapId}
          roadmapTopics={roadmapTopics}
          onSaved={() => setStep("plan")}
        />
      )}

      {step === "plan" && (
        <>
          <button
            type="button"
            onClick={() => setStep("setup")}
            className="mb-4 text-sm font-medium text-indigo-600 hover:text-indigo-500"
          >
            ← Edit preferences
          </button>
          <LearningPlanView userId={userId} roadmapId={roadmapId} />
        </>
      )}
    </div>
  );
}
