import { useEffect, useState } from "react";

export default function AdminFinanceDocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([]);

  useEffect(() => {
    fetch("/api/v1/finance-documents/admin/documents/")
      .then((r) => r.json())
      .then((data) => setDocuments(data.results || data));
  }, []);

  async function queueArtifact(id: string) {
    await fetch(`/api/v1/finance-documents/admin/documents/${id}/generate-artifact/`, { method: "POST" });
    alert("Artifact generation queued");
  }

  async function sendEmail(id: string) {
    await fetch(`/api/v1/finance-documents/admin/documents/${id}/deliver-email/`, { method: "POST" });
    alert("Email delivery queued");
  }

  async function openDownloadUrl(id: string) {
    const res = await fetch(`/api/v1/finance-documents/admin/documents/${id}/download-url/`);
    const data = await res.json();
    window.open(data.download_url, "_blank", "noopener,noreferrer");
  }

  return (
    <main style={{ padding: 24 }}>
      <h1>Admin Finance Documents</h1>
      <table>
        <thead>
          <tr>
            <th>Trainer</th>
            <th>Type</th>
            <th>Status</th>
            <th>Artifact</th>
            <th>Email</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((item) => (
            <tr key={item.id}>
              <td>{item.trainer_email || item.trainer_id}</td>
              <td>{item.document_type}</td>
              <td>{item.status}</td>
              <td>
                <button onClick={() => queueArtifact(item.id)}>Generate PDF</button>
                <button onClick={() => openDownloadUrl(item.id)}>Signed URL</button>
              </td>
              <td>
                <button onClick={() => sendEmail(item.id)}>Send</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
