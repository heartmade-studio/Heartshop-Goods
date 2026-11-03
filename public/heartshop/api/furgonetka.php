<?php
declare(strict_types=1);
require __DIR__ . '/lib.php';

// Furgonetka "Własne" integration. Furgonetka calls us, with the token from the private .env
// in the Authorization header. Base URL to enter in Furgonetka: <origin><base>/api/furgonetka
//   GET  /orders?datetime=…&limit=100      paid orders changed after datetime, oldest first
//   POST /orders/{number}/tracking_number  tracking number after a label is generated
// Spec: https://furgonetka.pl/api/universal-integration-example
// One line per call (no bodies, no personal data), so a "błąd API" in Furgonetka can be traced.
register_shutdown_function(function () {
    // Hosting log rotation applies; never raw URI, query, headers or user agent.
    error_log('heartshop furgonetka response='.(int)http_response_code());
});

try {
    $token = secrets()['FURGONETKA_TOKEN'] ?? '';
    $auth = preg_replace('/^(Bearer|Token)\s+/i', '', trim($_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? ''));
    if (strlen($token) < 32 || !hash_equals($token, $auth)) jsonOut(['error' => 'Unauthorized'], 401);

    $tz = new DateTimeZone('Europe/Warsaw');
    $iso = fn(?int $ts) => $ts ? (new DateTimeImmutable('@' . $ts))->setTimezone($tz)->format('Y-m-d\TH:i:s') : null;
    $route = trim((string)($_GET['route'] ?? ''), '/');
    $method = $_SERVER['REQUEST_METHOD'];

    if ($route === 'orders' && $method === 'GET') {
        $since = 0;
        if (!empty($_GET['datetime'])) {
            try { $since = (new DateTimeImmutable((string)$_GET['datetime'], $tz))->getTimestamp(); }
            catch (Exception) { jsonOut(['error' => 'Invalid datetime'], 400); }
        }
        $limit = max(1, min(100, (int)($_GET['limit'] ?? 100)));

        // ">=" on a one-second clock: a repeated order is harmless (same sourceOrderId), a skipped one is not.
        // Vouchers have nothing to ship and never reach Furgonetka; NULL type = shipped (pre-voucher order).
        $stmt = db()->prepare("SELECT *, MAX(paid_at, COALESCE(tracking_at, 0)) AS changed FROM orders
            WHERE status = 'paid' AND COALESCE(offer_type, 'shipping') = 'shipping'
            AND COALESCE(json_extract(data, '$.snapshot.demo'), 0) = 0
            AND MAX(paid_at, COALESCE(tracking_at, 0)) >= :since
            ORDER BY changed, id LIMIT :limit");
        $stmt->bindValue(':since', $since, SQLITE3_INTEGER);
        $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
        $res = $stmt->execute();

        $out=[];
        while ($row=$res->fetchArray(SQLITE3_ASSOC)) {
            $row['data']=json_decode($row['data'],true);
            $row['number']=orderNumber((int)$row['id']);
            $out[]=furgonetkaOrder($row); // Legacy data fails closed, never repriced.
        }
        jsonOut($out);
    }

    if (preg_match('#^orders/([^/]+)/tracking_number$#', $route, $m) && $method === 'POST') {
        $prefix = cfg()['shop']['order_prefix'] . '-';
        if (!preg_match('/^'.preg_quote($prefix,'/').'([1-9][0-9]*)$/D',$m[1],$parts)) jsonOut(['error'=>'Not Found'],404);
        $id=(int)$parts[1]-1000;
        $in = json_decode(file_get_contents('php://input', false, null, 0, 65536) ?: '', true);
        $number = clean($in['tracking']['number'] ?? '', 64);
        $courier = clean($in['tracking']['courierService'] ?? '', 32);
        if ($number === '') jsonOut(['error' => 'Missing tracking.number'], 400);

        $stmt = db()->prepare("UPDATE orders SET tracking_number = :n, courier_service = :c, tracking_at = :now
            WHERE id = :id AND status = 'paid' AND COALESCE(offer_type, 'shipping') = 'shipping'
            AND COALESCE(json_extract(data, '$.snapshot.demo'), 0) = 0");
        $stmt->bindValue(':n', $number);
        $stmt->bindValue(':c', $courier);
        $stmt->bindValue(':now', time(), SQLITE3_INTEGER);
        $stmt->bindValue(':id', $id, SQLITE3_INTEGER);
        $stmt->execute();
        if (db()->changes() !== 1) jsonOut(['error' => 'Not Found'], 404);
        jsonOut(['status' => 'ok']);
    }

    jsonOut(['error' => 'Not Found'], 404);
} catch (LegacyOrderException $e) {
    jsonOut(['error'=>'Historical order needs operator reconciliation','code'=>'legacy_snapshot_missing'],409);
} catch (Throwable $e) {
    logError($e, 'furgonetka');
    if (!headers_sent()) jsonOut(['error' => 'Temporary failure'], 500);
}
