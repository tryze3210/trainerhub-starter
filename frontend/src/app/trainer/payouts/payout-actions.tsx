'use client';

import { createPayoutRequest } from '@/lib/api';

export function RequestPayoutButton() {
  return (
    <button
      onClick={() => createPayoutRequest('5000.00', '**** 1234')}
    >
      Request payout
    </button>
  );
}
