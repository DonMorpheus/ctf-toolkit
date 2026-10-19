<?php
header('Content-Type: text/plain');
$ep = $_REQUEST['ep'] ?? '/system/about';
$m  = strtoupper($_REQUEST['m'] ?? 'GET');
$body = $_REQUEST['body'] ?? '';
$login = http_build_query(['user'=>'admin','pass'=>'ADMIN_PASS_PLACEHOLDER']);
$ch = curl_init('http://127.0.0.1:8080/api/v1/login');
curl_setopt_array($ch, [
  CURLOPT_RETURNTRANSFER=>true,
  CURLOPT_POST=>true,
  CURLOPT_POSTFIELDS=>$login,
  CURLOPT_HTTPHEADER=>['Content-Type: application/x-www-form-urlencoded'],
  CURLOPT_TIMEOUT=>15,
]);
$j = json_decode(curl_exec($ch), true);
curl_close($ch);
$jwt = $j['grommunioAuthJwt'] ?? '';
$csrf = $j['csrf'] ?? '';
echo "login jwt=".strlen($jwt)." csrf=".strlen($csrf)." keys=".implode(',', array_keys($j?:[]))."\n";
if (!$jwt) { echo "LOGIN FAIL\n"; var_export($j); exit; }
$url = 'http://127.0.0.1:8080/api/v1' . $ep;
$ch = curl_init($url);
$hdr = ["Cookie: grommunioAuthJwt=$jwt", "X-Csrf-Token: $csrf", "Accept: application/json"];
if ($m === 'POST' || $m === 'PUT' || $m === 'PATCH') {
  $hdr[] = 'Content-Type: application/json';
  curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
  curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $m);
} else {
  curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $m);
}
curl_setopt_array($ch, [
  CURLOPT_RETURNTRANSFER=>true,
  CURLOPT_HTTPHEADER=>$hdr,
  CURLOPT_TIMEOUT=>45,
]);
$resp = curl_exec($ch);
$code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
echo "HTTP $code $m $url\n$resp\n";
