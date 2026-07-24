Suggested test matrix:
- idempotent outbox append by same idempotency key
- publish pending event to 1..N subscriptions
- failed delivery transitions event to failed
- manual dead-letter creates snapshot record
- duplicate inbound message rejected by unique(provider, external_event_key)
- replay endpoint republishes event safely
- audit log entry created from finance/payout operations with correlation_id
