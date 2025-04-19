from flask import Flask, request, jsonify
import math

app = Flask(__name__)

# Weight-based cost calculator
def calculateCost(weight, distance):
    remaining = weight
    cost = 0

    if remaining <= 5:
        return distance * 10

    cost += distance * 10
    remaining -= 5

    while remaining > 0:
        chunk = min(5, remaining)
        cost += distance * 8
        remaining -= chunk

    return cost

# Product and center mappings
products = {
    "A": {"center": "C1", "weight": 3},
    "B": {"center": "C1", "weight": 2},
    "C": {"center": "C1", "weight": 8},
    "D": {"center": "C2", "weight": 12},
    "E": {"center": "C2", "weight": 25},
    "F": {"center": "C2", "weight": 15},
    "G": {"center": "C3", "weight": 0.5},
    "H": {"center": "C3", "weight": 1},
    "I": {"center": "C3", "weight": 2},
}

# Distances between centers and location L1
distances = {
    "C1": {"C2": 4, "C3": 5, "L1": 3},
    "C2": {"C1": 4, "C3": 3, "L1": 2.5},
    "C3": {"C1": 5, "C2": 3, "L1": 2},
    "L1": {"C1": 3, "C2": 2.5, "C3": 2},
}

def getDistance(from_location, to_location):
    return distances.get(from_location, {}).get(to_location, 0)

# Main cost minimization logic
def findMinimumCost(order):
    min_cost = math.inf
    initialRemainingToDeliver = {product: qty for product, qty in order.items() if product in products and qty > 0}

    if not initialRemainingToDeliver:
        return 0

    activeCenters = list(set(products[product]["center"] for product in initialRemainingToDeliver))

    memo = {}

    def solve(currentLocation, remainingToDeliver, currentCost, currentlyCarrying):
        nonlocal min_cost

        remaining_hash = tuple(sorted((p, q) for p, q in remainingToDeliver.items() if q > 0))
        carrying_hash = tuple(sorted((p, q) for p, q in currentlyCarrying.items() if q > 0))
        state = (currentLocation, remaining_hash, carrying_hash)

        if state in memo and memo[state] <= currentCost:
            return
        memo[state] = currentCost

        if not remainingToDeliver and not currentlyCarrying and currentLocation == "L1":
            min_cost = min(min_cost, currentCost)
            return

        if currentCost >= min_cost:
            return

        if currentLocation in activeCenters:
            nextCarrying = dict(currentlyCarrying)
            items_can_be_picked_up = [
                (product, qty - currentlyCarrying.get(product, 0))
                for product, qty in remainingToDeliver.items()
                if qty > 0 and products[product]["center"] == currentLocation
            ]

            if items_can_be_picked_up:
                for product, pickupQty in items_can_be_picked_up:
                    nextCarrying[product] = nextCarrying.get(product, 0) + pickupQty
                solve(currentLocation, remainingToDeliver, currentCost, nextCarrying)

        next_locations = activeCenters + ["L1"]
        for nextLocation in next_locations:
            if nextLocation == currentLocation:
                continue
            distance = getDistance(currentLocation, nextLocation)
            if distance > 0:
                weight = sum(products[p]["weight"] * q for p, q in currentlyCarrying.items() if p in products)
                nextRemaining = dict(remainingToDeliver)
                nextCarrying = dict(currentlyCarrying)

                if nextLocation == "L1":
                    for product, qty_carried in currentlyCarrying.items():
                        if product in nextRemaining:
                            nextRemaining[product] = max(0, nextRemaining[product] - qty_carried)
                    nextCarrying = {}
                    nextRemaining = {p: q for p, q in nextRemaining.items() if q > 0}

                solve(nextLocation, nextRemaining, currentCost + calculateCost(weight, distance), nextCarrying)

    for startLocation in activeCenters + ["L1"]:
        solve(startLocation, initialRemainingToDeliver, 0, {})

    return round(min_cost, 2) if min_cost != math.inf else 0

# API Endpoint
@app.route('/calculate_cost', methods=['POST'])
def calculate_cost():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input"}), 400
        result = findMinimumCost(data)
        return jsonify({"cost": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
