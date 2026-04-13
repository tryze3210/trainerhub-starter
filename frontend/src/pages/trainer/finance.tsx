import { useEffect, useState } from "react";

export default function TrainerFinancePage() {
  const [documents, setDocuments] = useState<any[]>([]);

  useEffect(() => {
    fetch("/api/v1/finance-documents/me/documents/")
      .then((r) => r.json())
      .then((data) => setDocuments(data.results || data));
  }, []);

  async function openDownloadUrl(id: string) {
    const res = await fetch(`/api/v1/finance-documents/me/documents/${id}/download-url/`);
    const data = await res.json();
    window.open(data.download_url, "_blank", "noopener,noreferrer");
  }

  return (
    <main style={{ padding: 24 }}>
      <h1>Trainer Finance</h1>
      <p>Statements, invoices and payout acts.</p>
      <table>
        <thead>
          <tr>
            <th>Type</th>
            <th>Status</th>
            <th>Period</th>
            <th>Artifact</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((item) => (
            <tr key={item.id}>
              <td>{item.document_type}</td>
              <td>{item.status}</td>
              <td>{item.period_start} — {item.period_end}</td>
              <td>
                <button onClick={() => openDownloadUrl(item.id)}>Download</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
