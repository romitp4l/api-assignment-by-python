<?php
require 'deliveryService.php';

header('Content-Type: application/json');
$data = json_decode(file_get_contents("php://input"), true);

if (!$data) {
    echo json_encode(["error" => "Invalid JSON"]);
    exit;
}

$result = calculateMinimumDeliveryCost($data);
echo json_encode($result);
