import requests

import inventory_service
import order_service


def test_inventory_reports_available_quantity():
    client = inventory_service.app.test_client()
    response = client.get("/inventory/sku-123?quantity=2")

    assert response.status_code == 200
    assert response.get_json() == {
        "item_id": "sku-123",
        "quantity": 2,
        "available": True,
        "available_quantity": 7,
    }


def test_order_creates_order_when_inventory_is_available(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"available": True, "available_quantity": 7}

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse())
    client = order_service.app.test_client()
    response = client.post("/orders", json={"item_id": "sku-123", "quantity": 2})

    assert response.status_code == 201
    assert response.get_json()["status"] == "created"


def test_order_returns_conflict_when_item_is_unavailable(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"available": False, "available_quantity": 0}

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: FakeResponse())
    client = order_service.app.test_client()
    response = client.post("/orders", json={"item_id": "sku-456", "quantity": 1})

    assert response.status_code == 409
    assert response.get_json()["error"] == "item_unavailable"


def test_order_handles_inventory_connection_failure(monkeypatch):
    def unavailable(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Inventory is stopped")

    monkeypatch.setattr(requests, "get", unavailable)
    client = order_service.app.test_client()
    response = client.post("/orders", json={"item_id": "sku-123", "quantity": 1})

    assert response.status_code == 503
    assert response.get_json() == {"error": "inventory_unavailable"}


def test_order_handles_inventory_timeout(monkeypatch):
    def slow(*args, **kwargs):
        raise requests.exceptions.Timeout("Inventory timed out")

    monkeypatch.setattr(requests, "get", slow)
    client = order_service.app.test_client()
    response = client.post("/orders", json={"item_id": "sku-123", "quantity": 1})

    assert response.status_code == 504
    assert response.get_json() == {"error": "inventory_timeout"}
