"""Lambda handler: process a refund for an order."""
import json

def handler(event, context):
    order_id = event.get("order_id", "")
    amount = event.get("amount", 0)
    reason = event.get("reason", "customer request")

    if not order_id:
        return {"status": "error", "message": "order_id is required"}
    if amount <= 0:
        return {"status": "error", "message": "amount must be positive"}

    refund_id = f"REF-{order_id}-{abs(hash(order_id)) % 10000:04d}"
    return {
        "status": "approved",
        "refund_id": refund_id,
        "order_id": order_id,
        "amount_refunded": amount,
        "reason": reason,
        "message": f"Refund of ${amount:.2f} approved for order {order_id}",
    }
