# Changelog

## Unreleased

- Webhooks follow the Heartshop Vouchers contract: a TRANSACTION subscription (`PAYMOVE_TRANSACTION_SECRET`) accepts only PLN `PAYMENT` and `REFUND` events, and a completion without the merchant `externalId` is matched through the stored checkout link (`signed_completions`, retried by the mail worker, alerted by `--check`). The thank-you page shows "confirming" while PAYMOVE reports processing. The deprecated `PAYMOVE_WEBHOOK_SECRET` is optional once the TRANSACTION secret is set.
- A signed PAYMOVE `REFUND` of the payment that paid an order moves it to `refunded`: it leaves the Furgonetka export, tracking updates are refused and the seller gets an email. A refund of another transaction changes nothing.
- A Paczkomat is accepted only when InPost returns its address; the point label always comes from InPost, never the browser.
- Panel sessions are bound to the current password hash and expire at most 30 days after login. Changing the password ends every session; sessions opened before this release need one new login.
- Apache denies `.ht*` files explicitly.

## v0.1.0 — 2026-11-13

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
- Retried payment creation re-checks the current production gates; the local
  simulator supports cancel → retry → pay on the same order.
- Seller panel: dark buttons readable again (the shop theme had made `--night`
  a light surface); buyer-email lookup field no longer uppercased.
- Orders record whether they were paid in the PAYMOVE sandbox (`testPayment`
  in the status response; voucher mail labelled accordingly).
- Postcode field renamed (`postal`) so Safari no longer offers passwords on it;
  PAYMOVE methods listed without fast bank transfers.

## 2026-11-03 — standalone extraction

Initial independent MIT distribution with synthetic local simulation, isolated
private storage and CI. No merchant deployment or provider acceptance implied.
