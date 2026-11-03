<?php
// Runtime settings. Also review HTML/legal copy and the allowed hosts in .htaccess.
// Secrets (API keys, webhook secret, e-mail addresses, panel password hash) live in the private .env, never here.
// Amounts are integers in grosze: 4900 = 49,00 zł.
return [
    'shop' => [
        'name'   => 'Magiczne pudełko',
        'seller' => 'Sklep demonstracyjny Heartmade',
        // SHOP_ORIGIN in the private .env picks this environment's origin; it must be listed here.
        'origins' => getenv('HEARTSHOP_ORIGIN') ? [getenv('HEARTSHOP_ORIGIN')] : ['https://shop.example.com', 'https://staging.shop.example.com'],
        'base'   => '/heartshop',
        'order_prefix' => 'HS', // order numbers: HS-1001, HS-1002…
    ],
    // Enable only after completing docs/production.md and replacing all sample content.
    'production_ready' => false,
    'product_type' => 'shipping',
    'terms_version' => 'demo-2026-11-03', // Change only with reviewed legal document version.
    // What the shop sells. Each offer has its own pages in <base>/<path> (zamowienie.html, dziekujemy.html).
    // This distribution accepts only shipping offers.
    //   type 'voucher':  a gift voucher; each unit bought gets its own code, valid for valid_months.
    // Never reuse an offer id for a different product: historical orders keep it.
    'default_offer' => 'magic-box', // pages without data-offer and older open tabs order this one
    'offers' => [
        'magic-box' => [
            'demo'    => true,
            'type'    => 'shipping',
            'name'    => 'Magiczne pudełko',
            'variant' => 'Przykładowy zestaw: notes, ołówek i herbata',
            'price'   => 4900,
            'max_qty' => 10,
            'path'    => '',
        ],
    ],
    'delivery' => [
        'paczkomat' => ['label' => 'Paczkomat InPost', 'price' => 1399, 'eta' => '1–2 dni robocze'],
        'kurier'    => ['label' => 'Kurier InPost',    'price' => 1699, 'eta' => '1–2 dni robocze'],
    ],
    'free_shipping_from' => 15000, // null disables free shipping
    'invoice'            => true,  // show "Faktura na firmę"; Furgonetka issues invoices for shipped orders,
                                   // the seller issues them for vouchers (marked in the panel)
    'tax_rate'           => 23,    // VAT % for product and shipping; null = seller exempt from VAT
    'paymove' => [
        'trigger_payment' => null, // e.g. 'BLIK' to open that method straight away
        'autoclose_ms'    => 4000, // modal closes itself after a successful payment
    ],
    // Private .env with secrets, outside the web root.
    'env_file' => getenv('HEARTSHOP_ENV_FILE') ?: dirname(__DIR__, 3) . '/private/heartshop/.env',
];
