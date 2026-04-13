import { workflowApi } from "@/lib/api";

export default async function WorkflowsPage() {
  const [definitions, runs] = await Promise.all([workflowApi.definitions(), workflowApi.runs()]);

  return (
    <main className="p-8 space-y-8"> 
      <section>
        <h1 className="text-2xl font-semibold">Workflow engine</h1>
        <p className="text-sm text-gray-600">Domain orchestration and async process boundaries.</p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-medium">Definitions</h2>
        <div className="grid gap-4">
          {definitions.map((item) => (
            <div key={item.workflow_key} className="rounded-2xl border p-4">
              <div className="font-medium">{item.workflow_key}</div>
              <div className="text-sm text-gray-600">Trigger: {item.trigger_event}</div>
              <div className="text-sm">Steps: {item.steps.join(" → ")}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-medium">Runs</h2>
        <div className="grid gap-4">
          {runs.map((item) => (
            <div key={item.id} className="rounded-2xl border p-4">
              <div className="font-medium">{item.workflow_key}</div>
              <div className="text-sm">Subject: {item.subject_type}:{item.subject_id}</div>
              <div className="text-sm">Status: {item.status}</div>
              <div className="text-sm">Current step: {item.current_step}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
