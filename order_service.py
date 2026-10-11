import os
import uuid

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

INVENTORY_URL = os.getenv("INVENTORY_URL", "http://127.0.0.1:5101")
INVENTORY_TIMEOUT_SECONDS = 0.5


@app.get("/health")
def health():
    return jsonify({"service": "order", "status": "ok"})


@app.post("/orders")
def create_order():
    body = request.get_json(silent=True) or {}
    item_id = body.get("item_id")
    quantity = body.get("quantity")

    if not isinstance(item_id, str) or not item_id.strip():
        return jsonify({"error": "item_id is required"}), 400
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
        return jsonify({"error": "quantity must be a positive integer"}), 400

    try:
        inventory_response = requests.get(
            f"{INVENTORY_URL}/inventory/{item_id}",
            params={"quantity": quantity},
            timeout=INVENTORY_TIMEOUT_SECONDS,
        )
        inventory_response.raise_for_status()
        availability = inventory_response.json()
    except requests.exceptions.Timeout:
        return jsonify({"error": "inventory_timeout"}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "inventory_unavailable"}), 503
    except requests.exceptions.RequestException:
        return jsonify({"error": "inventory_request_failed"}), 502

    if not availability.get("available", False):
        return (
            jsonify(
                {
                    "error": "item_unavailable",
                    "item_id": item_id,
                    "quantity": quantity,
                    "available_quantity": availability.get("available_quantity", 0),
                }
            ),
            409,
        )

    order = {
        "order_id": str(uuid.uuid4()),
        "item_id": item_id,
        "quantity": quantity,
        "status": "created",
    }
    return jsonify(order), 201


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5100)
