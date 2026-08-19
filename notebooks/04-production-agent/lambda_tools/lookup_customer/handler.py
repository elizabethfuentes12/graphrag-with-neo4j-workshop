"""Lambda handler: look up a customer by ID."""
import json

CUSTOMERS = {
    "C001": {"customer_id": "C001", "name": "Alice Chen", "email": "alice@example.com", "tier": "Gold", "loyalty_points": 12500},
    "C002": {"customer_id": "C002", "name": "Bob Johnson", "email": "bob@example.com", "tier": "Silver", "loyalty_points": 4800},
    "C003": {"customer_id": "C003", "name": "Carol Smith", "email": "carol@example.com", "tier": "Platinum", "loyalty_points": 32000},
}

def handler(event, context):
    customer_id = event.get("customer_id", "")
    if customer_id in CUSTOMERS:
        return {"status": "found", "customer": CUSTOMERS[customer_id]}
    return {"status": "not_found", "customer_id": customer_id, "message": f"No customer with ID {customer_id}"}
