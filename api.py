from flask import Flask, request, jsonify
import json
import math  # Import math for infinity

app = Flask(__name__)

# Same calculateCost function as in the original code
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

distances = {
    "C1": {"C2": 4, "C3": 5, "L1": 3},
    "C2": {"C1": 4, "C3": 3, "L1": 2.5},
    "C3": {"C1": 5, "C2": 3, "L1": 2},
    "L1": {"C1": 3, "C2": 2.5, "C3": 2},
}

def getDistance(from_location, to_location):
    return distances.get(from_location, {}).get(to_location, 0)

def findMinimumCost(order):
    min_cost = math.inf

    initialRemainingToDeliver = {product: qty for product, qty in order.items() if product in products and qty > 0}

    if not initialRemainingToDeliver:
        return 0

    activeCenters = list(set(products[product]["center"] for product in initialRemainingToDeliver if product in products))

    memo = {}

    def solve(currentLocation, remainingToDeliver, currentCost, currentlyCarrying):
        nonlocal min_cost

        remaining_hash_items = tuple(sorted((p, q) for p, q in remainingToDeliver.items() if q > 0))
        carrying_hash_items = tuple(sorted((p, q) for p, q in currentlyCarrying.items() if q > 0))
        state = (currentLocation, remaining_hash_items, carrying_hash_items)

        if state in memo and memo[state] <= currentCost:
            return
        memo[state] = currentCost

        if not remainingToDeliver and not currentlyCarrying and currentLocation == "L1":
            min_cost = min(min_cost, currentCost)
            return

        if currentCost >= min_cost:
            return

        if currentLocation in activeCenters:
            canPickup = False
            nextCarrying = dict(currentlyCarrying)
            items_can_be_picked_up = []
            for product, qty_needed in remainingToDeliver.items():
                if qty_needed > 0 and products.get(product, {}).get("center") == currentLocation:
                    carried_qty = currentlyCarrying.get(product, 0)
                    pickupQty = qty_needed - carried_qty
                    if pickupQty > 0:
                         items_can_be_picked_up.append((product, pickupQty))

            if items_can_be_picked_up:
                items_picked_up_this_stop = {}
                for product, qty_to_pickup in items_can_be_picked_up:
                    nextCarrying[product] = nextCarrying.get(product, 0) + qty_to_pickup
                    items_picked_up_this_stop[product] = qty_to_pickup
                    canPickup = True

                if canPickup:
                    solve(currentLocation, remainingToDeliver, currentCost, nextCarrying)

        possible_next_locations = list(activeCenters)
        if "L1" not in possible_next_locations:
            possible_next_locations.append("L1")

        for nextLocation in possible_next_locations:
            if currentLocation != nextLocation:
                distance = getDistance(currentLocation, nextLocation)
                if distance > 0:
                    current_load_weight = sum(products[p]["weight"] * currentlyCarrying[p] for p in currentlyCarrying if p in products and currentlyCarrying.get(p, 0) > 0)
                    nextRemainingToDeliver = dict(remainingToDeliver)
                    nextCarrying = dict(currentlyCarrying)

                    if nextLocation == "L1":
                        for product, qty_carried in currentlyCarrying.items():
                            if product in nextRemainingToDeliver:
                                nextRemainingToDeliver[product] = max(0, nextRemainingToDeliver[product] - qty_carried)
                        nextCarrying = {}
                        nextRemainingToDeliver = {p: q for p, q in nextRemainingToDeliver.items() if q > 0}

                    solve(nextLocation, nextRemainingToDeliver, currentCost + calculateCost(current_load_weight, distance), nextCarrying)

    starting_points = list(activeCenters)
    if "L1" not in starting_points:
        starting_points.append("L1")

    for startLocation in starting_points:
         solve(startLocation, initialRemainingToDeliver, 0, {})

    return round(min_cost, 2) if min_cost != math.inf else 0

@app.route('/calculate_cost', methods=['POST'])
def calculate_cost():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400
    
    try:
        # The input is a flat dictionary like: {"A": 1, "B": 2, "C": 1, "D": 5, "E": 1, "F": 1, "G": 2, "H": 1, "I": 1}
        order = data
        result = findMinimumCost(order)
        return jsonify({"cost": result}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
