'use client';

import { approvePayout, processPayout, markPayoutPaid } from '@/lib/api';

export function PayoutApproveButton({ id }: { id: string }) {
  return <button onClick={() => approvePayout(id)}>Approve</button>;
}

export function PayoutProcessButton({ id }: { id: string }) {
  return <button onClick={() => processPayout(id)}>Process</button>;
}

export function PayoutPaidButton({ id }: { id: string }) {
  return <button onClick={() => markPayoutPaid(id)}>Mark paid</button>;
}
