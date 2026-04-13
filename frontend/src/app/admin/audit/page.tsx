import { getAdminAuditEvents } from '@/lib/api';
import { PageHeader } from '@/components/page-header';

export default async function AdminAuditPage() {
  const items = await getAdminAuditEvents();

  return (
    <div className="space-y-6">
      <PageHeader title="Audit trail" description="Immutable business-event feed for support, finance and compliance." />
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.id} className="rounded-xl border p-4">
            <div>{item.event_type}</div>
            <div>{item.entity_type} #{item.entity_id}</div>
            <div>{new Date(item.created_at).toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
