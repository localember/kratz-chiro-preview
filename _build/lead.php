<?php
/**
 * Kratz Family Chiropractic lead mail.
 * Sends from noreply@localember.com through Brevo. The recipient list and the
 * API key live in /home/kratz/lead-config.php, outside the docroot.
 * A honeypot or a too-fast submit is still delivered, marked POSSIBLE SPAM.
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

function out(bool $ok, string $message, int $code): void {
    http_response_code($code);
    echo json_encode(['ok' => $ok, 'message' => $message], JSON_UNESCAPED_SLASHES);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    out(false, 'Please use the form on the site.', 405);
}

$cfgPath = '/home/kratz/lead-config.php';
if (!is_file($cfgPath)) {
    out(false, 'This form is not configured yet. Please call the office at (608) 291-1037.', 500);
}
$CFG = require $cfgPath;
if (!is_array($CFG) || empty($CFG['brevo_api_key']) || empty($CFG['to']) || empty($CFG['from_email'])) {
    out(false, 'This form is not configured yet. Please call the office at (608) 291-1037.', 500);
}

$host = strtolower((string)preg_replace('/:\d+$/', '', (string)($_SERVER['HTTP_HOST'] ?? '')));
$allowed = $CFG['expected_hosts'] ?? ['www.kratzfamilychiro.com'];
if (!in_array($host, $allowed, true)) {
    out(false, 'Please use the form on the site.', 403);
}
$origin = (string)($_SERVER['HTTP_ORIGIN'] ?? '');
if ($origin !== '') {
    $originHost = strtolower((string)parse_url($origin, PHP_URL_HOST));
    if (!in_array($originHost, $allowed, true)) {
        out(false, 'Please use the form on the site.', 403);
    }
}

$form = (string)($_POST['form'] ?? '');
if ($form !== 'contact' && $form !== 'request-appointment') {
    out(false, 'Please use the form on the site.', 400);
}

function one_line(string $name, int $max): string {
    $value = trim((string)($_POST[$name] ?? ''));
    $value = str_replace(array("\r", "\n"), ' ', $value);
    if (strlen($value) > $max) {
        $value = substr($value, 0, $max);
    }
    return $value;
}

function block(string $name, int $max): string {
    $value = trim((string)($_POST[$name] ?? ''));
    $value = str_replace("\r\n", "\n", $value);
    $value = str_replace("\r", "\n", $value);
    if (strlen($value) > $max) {
        $value = substr($value, 0, $max);
    }
    return $value;
}

$name = one_line('name', 120);
$phone = one_line('phone', 40);
$email = one_line('email', 160);
$note = block($form === 'contact' ? 'message' : 'reason', 2000);
$honey = trim((string)($_POST['website_url'] ?? ''));
$loaded = trim((string)($_POST['loaded'] ?? ''));

if ($name === '') {
    out(false, 'Please enter your name.', 400);
}
if ($form === 'contact') {
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        out(false, 'Please enter a valid email address.', 400);
    }
} else {
    $digits = preg_match_all('/\d/', $phone);
    if ($digits < 10) {
        out(false, 'Please enter a phone number including the area code.', 400);
    }
    if ($email !== '' && !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        out(false, 'That email address does not look right.', 400);
    }
}

$spam = false;
$reasons = array();
if ($honey !== '') {
    $spam = true;
    $reasons[] = 'honeypot';
}
$nowMs = (int)round(microtime(true) * 1000);
if (!preg_match('/^\d{13}$/', $loaded)) {
    $spam = true;
    $reasons[] = 'timing-missing';
} else {
    $delta = $nowMs - (int)$loaded;
    if ($delta < 3000 || $delta > 86400000) {
        $spam = true;
        $reasons[] = 'timing';
    }
}

$logDir = rtrim((string)($CFG['log_dir'] ?? '/home/kratz/lead-logs'), '/');
if ($logDir === '' || strpos($logDir, '/home/kratz/public_html') === 0) {
    out(false, 'Something went wrong sending that. Please call the office at (608) 291-1037.', 500);
}
if (!is_dir($logDir) && !@mkdir($logDir, 0700, true) && !is_dir($logDir)) {
    out(false, 'Something went wrong sending that. Please call the office at (608) 291-1037.', 500);
}

$ip = (string)($_SERVER['REMOTE_ADDR'] ?? '');
$logFile = $logDir . '/leads-' . gmdate('Y-m') . '.jsonl';
$recent = 0;
if (is_file($logFile)) {
    $lines = @file($logFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    if (is_array($lines)) {
        $cut = time() - 3600;
        $slice = array_slice($lines, -200);
        foreach ($slice as $line) {
            $row = json_decode($line, true);
            if (!is_array($row) || ($row['ip'] ?? '') !== $ip) {
                continue;
            }
            $at = strtotime((string)($row['at'] ?? ''));
            if ($at !== false && $at >= $cut) {
                $recent++;
            }
        }
    }
}
if ($recent >= 12) {
    out(false, 'Please call the office at (608) 291-1037.', 429);
}

$label = $form === 'contact' ? 'New contact message' : 'New appointment request';
if ($spam) {
    $label = 'POSSIBLE SPAM: ' . $label;
}
$subject = $label . ' from ' . $name;
$bodyLines = array(
    $spam ? 'POSSIBLE SPAM: this submission tripped a check and was still delivered.' : 'A visitor submitted the website form.',
    '',
    'Form: ' . ($form === 'contact' ? 'Contact' : 'Request appointment'),
    'Name: ' . $name,
    'Phone: ' . ($phone !== '' ? $phone : '(not given)'),
    'Email: ' . ($email !== '' ? $email : '(not given)'),
    '',
    ($form === 'contact' ? 'Message:' : 'Reason for visit:'),
    $note !== '' ? $note : '(none)',
    '',
    'This does not book a time. Contact them to set up the visit.',
    'The office phone is for calls only.',
);
$text = implode("\n", $bodyLines);

$to = array();
foreach ($CFG['to'] as $addr) {
    if (is_string($addr) && filter_var($addr, FILTER_VALIDATE_EMAIL)) {
        $to[] = array('email' => $addr);
    }
}
if (!$to) {
    out(false, 'Something went wrong sending that. Please call the office at (608) 291-1037.', 500);
}

$payload = array(
    'sender' => array(
        'name' => (string)($CFG['from_name'] ?? 'Kratz Family Chiropractic'),
        'email' => (string)$CFG['from_email'],
    ),
    'to' => $to,
    'subject' => $subject,
    'textContent' => $text,
);
if ($email !== '' && filter_var($email, FILTER_VALIDATE_EMAIL)) {
    $payload['replyTo'] = array('email' => $email, 'name' => $name);
}

$sent = false;
$status = 0;
$error = '';
$raw = '';
if (function_exists('curl_init')) {
    $ch = curl_init('https://api.brevo.com/v3/smtp/email');
    curl_setopt_array($ch, array(
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode($payload, JSON_UNESCAPED_SLASHES),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_HTTPHEADER => array(
            'Content-Type: application/json',
            'accept: application/json',
            'api-key: ' . $CFG['brevo_api_key'],
        ),
    ));
    $result = curl_exec($ch);
    $status = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    $error = (string)curl_error($ch);
    if ($result !== false) {
        $raw = substr((string)$result, 0, 300);
    }
    $sent = $result !== false && $status >= 200 && $status < 300;
} else {
    $error = 'curl missing';
}

$record = array(
    'at' => gmdate('c'),
    'form' => $form,
    'name' => $name,
    'phone' => $phone,
    'email' => $email,
    'message' => $note,
    'spam' => $spam,
    'spam_reasons' => $reasons,
    'ip' => $ip,
    'brevo_status' => $status,
    'sent' => $sent,
);
if (!$sent) {
    $record['brevo_error'] = $error !== '' ? $error : $raw;
}
@file_put_contents($logFile, json_encode($record, JSON_UNESCAPED_SLASHES) . "\n", FILE_APPEND | LOCK_EX);
@chmod($logFile, 0600);

if (!$sent) {
    out(false, 'Something went wrong sending that. Please call the office at (608) 291-1037.', 502);
}
out(true, 'Sent. The office will contact you.', 200);
