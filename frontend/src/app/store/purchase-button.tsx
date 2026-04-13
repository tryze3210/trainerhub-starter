'use client';

import { createOrderCheckout } from '@/lib/api';

export function PurchaseButton({ itemType, itemId }: { itemType: 'video' | 'program' | 'bundle'; itemId: string }) {
  return (
    <button
      className="rounded-xl border px-4 py-2 text-sm font-medium"
      onClick={async () => {
        const origin = window.location.origin;
        const result = await createOrderCheckout(itemType, itemId, `${origin}/payments/status?result=success`, `${origin}/payments/status?result=cancel`);
        window.location.href = result.checkout_url;
      }}
    >
      Buy now
    </button>
  );
}
