'use client';

import { refundAdminPayment } from '@/lib/api';

export function RefundPaymentButton({ id }: { id: string }) {
  return <button onClick={() => refundAdminPayment(id)}>Refund</button>;
}
