# v50.2 Referral register hard fix

The v50.1 script could be skipped or fail silently in partially-applied trees when the expected source shape differed. v50.2 is intentionally narrow and forceful:

- locates the repository root from either project root or `backend/`;
- parses `backend/apps/authn/services.py` before modification;
- patches the real `register_user` signature;
- inserts signup attribution binding after account settings creation;
- parses the patched file again;
- prints the final signature so the fix is visible before running pytest.

No database migration is required.
