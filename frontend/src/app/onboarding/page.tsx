import { onboardingApi } from "@/lib/api";
import { CompleteStepButton } from "./complete-step-button";

export const metadata = {
  title: "Onboarding | TrainerHub",
  description: "Resume role-based onboarding tasks.",
};

export default async function OnboardingPage() {
  const status = await onboardingApi.status();

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-8">
      <div>
        <h1 className="text-3xl font-bold">Onboarding</h1>
        <p className="text-slate-600">
          Completion: {status.summary.completed_steps}/{status.summary.total_steps} · {status.summary.completion_percent}%
        </p>
      </div>

      <div className="space-y-4">
        {status.steps.map((step) => (
          <div key={step.code} className="rounded-2xl border p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-xs uppercase text-slate-500">{step.role_scope}</div>
                <h2 className="text-lg font-semibold">{step.title}</h2>
                <p className="text-sm text-slate-600">{step.description}</p>
                <div className="mt-2 text-sm">Status: <b>{step.is_completed ? "completed" : "pending"}</b></div>
              </div>
              {!step.is_completed ? <CompleteStepButton code={step.code} /> : null}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
