export async function getFinanceOverview(days = 30) {
  const res = await fetch(`/api/v1/finance/admin/overview/?days=${days}`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load finance overview");
  return res.json();
}

export async function refreshFinanceOverview(days = 30) {
  const res = await fetch(`/api/v1/finance/admin/refresh/`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ days }),
  });
  if (!res.ok) throw new Error("Failed to refresh finance overview");
  return res.json();
}

export async function listSettlementReports() {
  const res = await fetch(`/api/v1/finance/admin/settlements/`, { credentials: "include" });
  if (!res.ok) throw new Error("Failed to load settlement reports");
  return res.json();
}
