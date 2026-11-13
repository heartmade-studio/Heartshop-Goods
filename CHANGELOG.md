# Changelog

## Unreleased — proposed v0.1.0

- Standalone Heartshop Goods with local simulation, PAYMOVE checkout and seller panel.
- One documented merchant indexing switch; generated canonical, OG, visible
  offer facts, structured data, sitemap and robots. Demo/private routes noindex.
- Config-generated price fallbacks with checkout parity and build-drift checks.
- Root redirect, hosting comparison and production HSTS guidance.
- PHP 8.2–8.5 CI matrix passed; documented minimum lowered to 8.2.
  Checkout uses Node 24; pinned setup-php already uses Node 24.
- Polish introduction, contributor guide and local simulation screenshot.
- PL/EN invoice FAQ describes the merchant's Furgonetka invoice module.
- README preview of the Furgonetka client panel, where paid orders are processed and invoices are issued.
- Misleading voucher-service docs removed; coupled core cleanup documented.
- Payment recovery: a lost PAYMOVE create response is resumed under the same
  `externalId` with the frozen order; resumed checkouts read the payment status
  first, signed failed transactions are audited and diagnostics stay data-free.
- Hosted sandbox PAY links; buyers choose the payment method in PAYMOVE Checkout;
  checkout links the previous order's status after an error.
- Buyer text hardening: control and bidi-override characters removed; names reject
  links so shop mail cannot carry phishing text.
- Mail envelope sender (`-f`) aligned with `MAIL_FROM`.

No tag or release has been published for this proposal. Provider acceptance and
merchant deployment are separate from offline regression results.

## 2026-11-03 — standalone extraction

Initial independent MIT distribution with synthetic local simulation, isolated
private storage and CI. No merchant deployment or provider acceptance implied.
