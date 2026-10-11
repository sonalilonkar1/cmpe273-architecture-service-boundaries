from flask import Flask, jsonify, request

app = Flask(__name__)

# Inventory owns this data. Order never reads or modifies it directly.
INVENTORY = {
    "sku-123": 7,
    "sku-456": 0,
    "sku-789": 12,
}


@app.get("/health")
def health():
    return jsonify({"service": "inventory", "status": "ok"})


@app.get("/inventory/<item_id>")
def check_inventory(item_id: str):
    try:
        quantity = int(request.args.get("quantity", "1"))
    except ValueError:
        return jsonify({"error": "quantity must be an integer"}), 400

    if quantity <= 0:
        return jsonify({"error": "quantity must be greater than zero"}), 400

    available_quantity = INVENTORY.get(item_id, 0)
    return jsonify(
        {
            "item_id": item_id,
            "quantity": quantity,
            "available": available_quantity >= quantity,
            "available_quantity": available_quantity,
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5101)
