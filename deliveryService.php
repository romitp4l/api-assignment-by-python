<?php
header('Content-Type: application/json');

function calculateCost($weight, $distance) {
    $remaining = $weight;
    $cost = 0;

    if ($remaining <= 5) {
        return $distance * 10;
    }

    $cost += $distance * 10;
    $remaining -= 5;

    while ($remaining > 0) {
        $chunk = min(5, $remaining);
        $cost += $distance * 8;
        $remaining -= $chunk;
    }

    return $cost;
}

$products = [
    "A" => ["center" => "C1", "weight" => 3],
    "B" => ["center" => "C1", "weight" => 2],
    "C" => ["center" => "C1", "weight" => 8],
    "D" => ["center" => "C2", "weight" => 12],
    "E" => ["center" => "C2", "weight" => 25],
    "F" => ["center" => "C2", "weight" => 15],
    "G" => ["center" => "C3", "weight" => 0.5],
    "H" => ["center" => "C3", "weight" => 1],
    "I" => ["center" => "C3", "weight" => 2],
];

$distances = [
    "C1" => ["C2" => 4, "C3" => 5, "L1" => 3],
    "C2" => ["C1" => 4, "C3" => 3, "L1" => 2.5],
    "C3" => ["C1" => 5, "C2" => 3, "L1" => 2],
    "L1" => ["C1" => 3, "C2" => 2.5, "C3" => 2],
];

function getDistance($from, $to) {
    global $distances;
    return $distances[$from][$to] ?? 0;
}

function findMinimumCost($order) {
    global $products, $distances;
    $minCost = PHP_INT_MAX;

    $activeCenters = [];
    foreach ($order as $product => $qty) {
        if (isset($products[$product]) && $qty > 0 && !in_array($products[$product]["center"], $activeCenters)) {
            $activeCenters[] = $products[$product]["center"];
        }
    }

    if (empty($activeCenters)) {
        return 0;
    }

    $memo = [];

    // Define $solve *before* it's used
    $solve = function ($currentLocation, $remainingOrder, $currentCost, $currentlyCarrying) use (&$minCost, &$memo, $activeCenters, $products, $distances, $order, &$solve) {
        $orderHash = md5(serialize($remainingOrder));
        $carryingHash = md5(serialize($currentlyCarrying));
        $state = $currentLocation . "-" . $orderHash . "-" . $carryingHash;

        if (isset($memo[$state]) && $memo[$state] <= $currentCost) {
            return;
        }
        $memo[$state] = $currentCost;

        if (empty(array_filter($remainingOrder))) {
            $minCost = min($minCost, $currentCost);
            return;
        }

        // Option 1: Deliver to L1
        if ($currentLocation !== "L1" && !empty($currentlyCarrying)) {
            $weightToL1 = 0;
            $nextCarrying = [];
            $nextRemainingOrder = $remainingOrder;
            foreach ($currentlyCarrying as $product => $qty) {
                if (isset($products[$product])) {
                    $weightToL1 += $products[$product]["weight"] * $qty;
                    $nextRemainingOrder[$product] -= $qty;
                    if ($nextRemainingOrder[$product] < 0) $nextRemainingOrder[$product] = 0;
                }
            }
            $distanceToL1 = getDistance($currentLocation, "L1");
            $solve("L1", $nextRemainingOrder, $currentCost + calculateCost($weightToL1, $distanceToL1), []);
        }

        // Option 2: Pick up from a center
        foreach ($activeCenters as $center) {
            if ($currentLocation !== $center) {
                $canPickup = false;
                $nextCarrying = $currentlyCarrying;
                $nextRemainingOrder = $remainingOrder;
                foreach ($order as $product => $qtyNeeded) {
                    if (isset($products[$product]) && $products[$product]["center"] === $center && $remainingOrder[$product] > 0) {
                        $pickupQty = min($remainingOrder[$product], $qtyNeeded);
                        $nextCarrying = array_merge($nextCarrying, [$product => ($nextCarrying[$product] ?? 0) + $pickupQty]);
                        $nextRemainingOrder[$product] -= $pickupQty;
                        if ($nextRemainingOrder[$product] < 0) $nextRemainingOrder[$product] = 0;
                        $canPickup = true;
                    }
                }
                if ($canPickup) {
                    $distanceToCenter = getDistance($currentLocation, $center);
                    $solve($center, $nextRemainingOrder, $currentCost + calculateCost(0, $distanceToCenter), $nextCarrying);
                }
            }
        }

        // Option 3: Move between centers and L1
        if ($currentLocation !== "L1") {
            foreach ($activeCenters as $nextCenter) {
                if ($currentLocation !== $nextCenter) {
                    $distance = getDistance($currentLocation, $nextCenter);
                    $solve($nextCenter, $remainingOrder, $currentCost + calculateCost(0, $distance), $currentlyCarrying);
                }
            }
            $distanceToL1 = getDistance($currentLocation, "L1");
            $solve("L1", $remainingOrder, $currentCost + calculateCost(0, $distanceToL1), $currentlyCarrying);
        } else { // If at L1, can still go to centers
            foreach ($activeCenters as $nextCenter) {
                $distance = getDistance($currentLocation, $nextCenter);
                $solve($nextCenter, $remainingOrder, $currentCost + calculateCost(0, $distance), $currentlyCarrying);
            }
        }
    };

    $initialRemainingOrder = $order;
    foreach ($activeCenters as $startCenter) {
        $solve($startCenter, $initialRemainingOrder, 0, []);
    }
    $solve("L1", $initialRemainingOrder, 0, []);


    return $minCost === PHP_INT_MAX ? 0 : round($minCost, 2);
}

$input = json_decode(file_get_contents("php://input"), true);
if (!$input || !is_array($input)) {
    echo json_encode(["error" => "Invalid input"]);
    exit;
}

$minDeliveryCost = findMinimumCost($input);

echo json_encode(["minimum_cost" => $minDeliveryCost]);

// Test cases (for direct execution)
$testCases = [
    ["input" => ["A" => 1, "G" => 1, "H" => 1, "I" => 3], "expected" => 86],
    ["input" => ["A" => 1, "B" => 1, "C" => 1, "G" => 1, "H" => 1, "I" => 1], "expected" => 118],
    ["input" => ["A" => 1, "B" => 1, "C" => 1], "expected" => 78],
    ["input" => ["A" => 1, "B" => 1, "C" => 1, "D" => 1], "expected" => 168],
];

echo "\n--- Local Test Results ---\n";
foreach ($testCases as $test) {
    $result = findMinimumCost($test["input"]);
    echo "Input: " . json_encode($test["input"]) . ", Expected: " . $test["expected"] . ", Result: " . $result . ($result === $test["expected"] ? " (PASS)" : " (FAIL)") . "\n";
}

?>