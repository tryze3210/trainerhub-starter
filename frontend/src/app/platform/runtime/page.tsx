import { runtimeApi } from "@/lib/api";

export default async function RuntimePage() {
  const [health, readiness, config] = await Promise.all([
    runtimeApi.health(),
    runtimeApi.readiness(),
    runtimeApi.config(),
  ]);

  return (
    <main style={{ padding: 24 }}>
      <h1>Runtime</h1>
      <p>Health: {health.status}</p>
      <p>Service: {health.service}</p>
      <p>Readiness: {readiness.status}</p>
      <h2>Checks</h2>
      <ul>
        {readiness.checks.map((check) => (
          <li key={check.name}>{check.name}: {check.status} — {check.details}</li>
        ))}
      </ul>
      <h2>Config snapshot</h2>
      <pre>{JSON.stringify(config, null, 2)}</pre>
    </main>
  );
}
