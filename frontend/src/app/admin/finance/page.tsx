"use client";

import { useEffect, useState } from "react";
import { getFinanceOverview, listSettlementReports, refreshFinanceOverview } from "@/features/finance/admin-api";

export default function AdminFinancePage() {
  const [overview, setOverview] = useState<any>(null);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [overviewData, reportsData] = await Promise.all([
        getFinanceOverview(30),
        listSettlementReports(),
      ]);
      setOverview(overviewData);
      setReports(Array.isArray(reportsData) ? reportsData : reportsData.results || []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <main className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Finance reconciliation</h1>
          <p className="text-sm text-slate-500">Settlement reports, payout reconciliation and exports.</p>
        </div>
        <button
          className="rounded-xl border px-4 py-2"
          onClick={async () => { await refreshFinanceOverview(45); await load(); }}
        >
          Refresh snapshots
        </button>
      </div>

      {overview?.latest && (
        <section className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
          <MetricCard title="Gross sales" value={overview.latest.gross_sales_amount} />
          <MetricCard title="Successful payments" value={overview.latest.successful_payment_amount} />
          <MetricCard title="Refunded" value={overview.latest.refunded_amount} />
          <MetricCard title="Trainer payouts" value={overview.latest.trainer_payout_amount} />
          <MetricCard title="Commission" value={overview.latest.recognized_commission_amount} />
          <MetricCard title="Settlement gap" value={overview.latest.settlement_gap_amount} />
        </section>
      )}

      <section className="rounded-2xl border p-4">
        <h2 className="text-lg font-medium mb-3">Settlement reports</h2>
        <div className="overflow-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">Period</th>
                <th>Status</th>
                <th>Exports</th>
                <th>Currency</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id} className="border-b last:border-b-0">
                  <td className="py-3">{report.period_start} — {report.period_end}</td>
                  <td>{report.status}</td>
                  <td>{report.export_count}</td>
                  <td>{report.currency}</td>
                  <td className="space-x-3">
                    <a className="underline" href={`/api/v1/finance/admin/settlements/${report.id}/export/csv/`}>CSV</a>
                    <a className="underline" href={`/api/v1/finance/admin/settlements/${report.id}/export/xlsx/`}>XLSX</a>
                  </td>
                </tr>
              ))}
              {!reports.length && !loading && (
                <tr><td className="py-3 text-slate-500" colSpan={5}>No settlement reports yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

function MetricCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="rounded-2xl border p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{title}</div>
      <div className="mt-2 text-xl font-semibold">{value}</div>
    </div>
  );
}
