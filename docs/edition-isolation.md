# Edition isolation follow-up

The configured offer type is enforced on the server before checkout. Synthetic
cross-edition configurations live only in `tests/fixtures/`; `core.py` installs
them into a temporary test copy. There is no deployment-time test override.

Deferred: `api/vouchers.php` and the voucher branches in database initialization,
paid-event handling, status, mail, seller-panel queries/CSV and panel JavaScript
remain coupled. Simply deleting the helper would break every database opening
and panel order list. Removing it safely needs a coordinated edition-specific
migration plus fixtures for legacy orders, mail retries and panel export.
Estimated engineering effort: 1–2 days, then the full regression suite.

The configured shipping-only boundary rejects voucher offers. Do not import a
Vouchers database into Goods. This PR removes misleading voucher-service prose
from Goods configuration and integration/production docs, but deliberately does
not claim complete code separation. Keep this as a follow-up before treating
the editions as independent cores; no public voucher capability is promised.
