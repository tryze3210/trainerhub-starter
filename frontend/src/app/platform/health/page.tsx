import { runtimeApi } from "@/lib/api";
import { CachePingButton } from "./ping-button";

export default async function PlatformHealthPage() {
  const [health, readiness] = await Promise.all([runtimeApi.health(), runtimeApi.readiness()]);

  return (
    <main style={{ padding: 24 }}>
      <h1>Platform health</h1>
      <p>Liveness: {health.status}</p>
      <p>Readiness: {readiness.status}</p>
      <ul>
        {readiness.checks.map((check) => (
          <li key={check.name}>{check.name}: {check.status}</li>
        ))}
      </ul>
      <CachePingButton />
    </main>
  );
}
