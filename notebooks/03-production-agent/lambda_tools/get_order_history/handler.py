"""Lambda handler: get order history for a customer."""
import json

ORDER_HISTORY = {
    "C001": [
        {"order_id": "ORD-1001", "date": "2026-07-15", "amount": 299.99, "status": "delivered", "item": "Hotel booking - NYC"},
        {"order_id": "ORD-1002", "date": "2026-08-01", "amount": 149.00, "status": "delivered", "item": "Hotel booking - Miami"},
    ],
    "C002": [
        {"order_id": "ORD-2001", "date": "2026-06-20", "amount": 89.50, "status": "delivered", "item": "Hotel booking - Chicago"},
    ],
    "C003": [
        {"order_id": "ORD-3001", "date": "2026-08-10", "amount": 599.00, "status": "pending", "item": "Hotel booking - Paris"},
    ],
}

def handler(event, context):
    customer_id = event.get("customer_id", "")
    orders = ORDER_HISTORY.get(customer_id, [])
    return {"customer_id": customer_id, "order_count": len(orders), "orders": orders}
