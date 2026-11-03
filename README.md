# Heartshop Goods

A small, self-hosted shop for physical products, by [Heartmade Studio](https://heartmade.pl/). Plain HTML/CSS/JavaScript, PHP and SQLite.

**Built for real transactions with PAYMOVE.io and Furgonetka.pl.** PAYMOVE is the intentionally chosen agent-oriented payment gateway; Heartshop currently connects through its server-side REST API, browser checkout and signed webhooks. Furgonetka provides the merchant interface for shipment booking, labels and sales invoices. Heartshop exports paid physical orders and invoice data to its custom-store integration. It does not issue invoices itself or include an autonomous payment agent.

This initial standalone distribution starts in **local simulation**. Live selling requires your merchant accounts, real product/seller/legal content, configuration and the acceptance checks in [production setup](docs/production.md). Automated tests do not establish that a merchant account is ready to take money.

## Run locally

Requirements: **PHP 8.5** with `curl`, `sqlite3` and `mbstring`. macOS and Linux are supported; on Windows use WSL. No Composer, npm install or database server is required.

```sh
git clone https://github.com/heartmade-studio/Heartshop-Goods.git
cd Heartshop-Goods
php scripts/dev/start.php
```

Open **http://localhost:8080/heartshop/**. Use `localhost`, not the numeric IP, because the origin is checked. To change the port: `php scripts/dev/start.php 8081`.

- Physical product: `/heartshop/` (PL and EN).
- Orders panel: `/heartshop/panel/`; local-only password: `local-heartshop-only`.
- Place an order using made-up details and courier delivery. The **local simulation** dialog lets you complete or cancel it.
- No real payment, email or shipment is made. Paczkomat lookup is disabled in local simulation to avoid provider calls. Demo orders are excluded from Furgonetka export.
- Ctrl-C stops the server. Local data persists in ignored `var/local/`; deleting that directory resets synthetic orders. The launcher regenerates only its dedicated local configuration, never your merchant `.env`.

The local simulator is not PAYMOVE sandbox. It checks the application flow without credentials; provider acceptance uses the real sandbox on an HTTPS staging host.

## What is included

- Server-priced PLN checkout, physical product example.
- PAYMOVE hosted checkout, HMAC-verified webhooks, immutable order snapshots and retry protection.
- Furgonetka authenticated order export and tracking-number callback.
- Seller panel: orders, notes, CSV, manual invoice/fulfillment markers.
- Durable email outbox with a separate CLI worker.
- Polish and English storefront; the panel is currently Polish.

No inventory reservation, variant selector, combined multi-product cart, automatic refunds or automatic reconciliation of uncertain payments. Voucher sales are in the separate [Heartshop Vouchers](https://github.com/heartmade-studio/Heartshop-Vouchers) repository. PAYMOVE account fees and Furgonetka services are separate from this code.

## Deploy for real transactions

Follow [production setup](docs/production.md) and [integration contracts](docs/integrations.md). Only `public/` is the web root. `private/`, `scripts/`, `tests/` and the rest of the repository must stay outside it. Apache 2.4 with direct HTTPS is the documented runtime; a PHP development server is never a production deployment.

The storefront is an editable sample. Pricing and offers live in `public/heartshop/api/config.php`; seller and product copy lives in the HTML. Do not enable production payments until both describe your actual offer. The supplied offer has `demo: true`, and `production_ready` is false by default.

## Verify changes

Additional test requirements: Node.js 22+, Python 3, Apache 2.4 and OpenSSL.

```sh
bash scripts/heartshop/check.sh
```

Tests run with synthetic credentials and isolated temporary databases. They cover backend behavior, the frontend, real HTTP endpoints, Apache HTTPS boundaries, production-mode configuration and the local simulation. GitHub Actions runs the same suite; there is no deployment workflow.

## Documentation and license

- [Architecture and extraction boundaries](docs/architecture.md)
- [Production setup](docs/production.md)
- [PAYMOVE and Furgonetka contracts](docs/integrations.md)
- [Security reporting](SECURITY.md)
- [MIT license](LICENSE), with separate [third-party notices](THIRD_PARTY_NOTICES.md).

The included product images are labeled AI illustrations, not photographs of goods or services for sale. Heartmade Studio provides project authorship and implementation services; operating a deployed shop remains the merchant's responsibility.
