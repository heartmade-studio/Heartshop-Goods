# Deliberately chosen integrations

## PAYMOVE.io

[PAYMOVE](https://www.paymove.io/) offers agent-oriented payments as well as REST and embedded checkout. This implementation uses **REST + browser widget + signed webhooks**, not MCP or an autonomous agent. Merchant onboarding, product setup and live/sandbox credentials are separate.

- [REST contract](https://docs.paymove.io/en/rest-api): POST `/api/pay/product/{productId}/subproduct/pricing`; `X-API-KEY`; integer `price` in grosze; unique merchant `externalId`; `details.returnUrl`. PLN only.
- Sandbox base: `https://gateway-api.sandbox.paymove.io`; production: `https://api.paymove.io`.
- A successful create returns HTTP 200 and `redirectUrl`. The query parameter called `externalId` in that URL is PAYMOVE's payment hash, not Heartshop's external ID. Heartshop stores the full URL.
- [Payment events](https://docs.paymove.io/en/payment-status): flat `externalId`, `orderId`, `price`, `status`, `paymentMethod`. Configure the webhook to preserve these fields; template prices can be strings containing integer grosze.
- [Signature](https://docs.paymove.io/en/webhook-signature): `X-Paymove-Signature`, HMAC-SHA256 of timestamp + `.` + raw body, base64 signature, checked within five minutes.
- Webhook URL: `https://YOUR-HOST/heartshop/api/webhook.php`. Expected response is 200; configure retries. Do not fulfill based on the return URL or browser callback.

The initial provider identity binding comes from the first verified webhook, because the create response does not contain provider `orderId`. Conflicts and amount mismatches become `review`. Timeouts leave an uncertain payment requiring merchant reconciliation; do not erase the attempt to force another charge. Automatic refunds are not implemented.

## Furgonetka.pl

[Furgonetka](https://furgonetka.pl/) is the shipment and invoice workspace. Paid orders land in the Furgonetka client panel, under E-commerce → Sales, where the merchant processes shipments and issues invoices. Preview: [Furgonetka panel](screenshots/furgonetka-panel.jpg). Add a custom-store integration using the base URL `https://YOUR-HOST/heartshop/api/furgonetka` and the shared random `FURGONETKA_TOKEN`. This is an inbound integration: Furgonetka calls Heartshop; no Furgonetka OAuth client is required by this adapter.

[Custom-store API contract](https://furgonetka.pl/api/universal-integration-example):

- `GET /orders?datetime=...&limit=100` exports paid physical orders, with customer/address, frozen prices, delivery and optional invoice data. Non-demo snapshots only. Keep order prefix and offer IDs stable after launch.
- `POST /orders/{number}/tracking_number` stores `tracking.number` and `tracking.courierService` for an eligible paid order.
- Both require `Authorization: <token>`; the adapter also accepts `Bearer <token>` and `Token <token>`. Apache must forward this header to PHP.

Invoice issuance happens in Furgonetka's invoice module after its configuration, not automatically in Heartshop. See [Furgonetka invoice instructions](https://c.furgonetka.pl/public.furgonetka.pl/media_help/Faktury_KSeF_od_Furgonetka.pl_Instrukcja.pdf). Only physical orders are supported by this edition. Test actual field mapping, order import, a shipment label and invoice workflow on your account before launch.

The pull adapter uses an inclusive timestamp and a 100-order maximum. For high-volume bursts, confirm the consumer's pagination behavior; this small-store adapter does not offer a cursor. Provider contract/documentation review is not live account acceptance.

## InPost and email

Optional InPost Geowidget tokens are public and domain-bound. The backend validates selected points through the InPost points endpoint. Configure the widget environment separately from PAYMOVE; the offline simulator offers courier only.

Email uses PHP `mail()` via the host's mail transport. Configure SPF/DKIM/DMARC and delivery monitoring for your domain. A worker's `sent` state means the local transport accepted a message, not proof of inbox delivery. Worker delivery is at least once: a crash after handing off a message can cause a duplicate.
