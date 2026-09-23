"""Classify customer emails and draft replies. Invented example project for portfolio-demo-kit."""

import csv
import json
import re
import urllib.request
from pathlib import Path

import config

TOPICS = ["refund", "late_parcel", "damaged_item", "product_question", "other"]
ORDER_RE = re.compile(r"\bPK-\d{6}\b")


def call_model(system, user, max_tokens=700):
    body = json.dumps({
        "model": config.MODEL,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "content-type": "application/json",
        "x-api-key": config.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return "".join(b["text"] for b in data["content"] if b["type"] == "text")


def load_orders():
    with open(config.ORDERS_CSV, newline="") as fh:
        return {row["order_id"]: row for row in csv.DictReader(fh)}


def classify(email):
    system = Path("prompts/classify.txt").read_text()
    user = f"Subject: {email['subject']}\n\n{email['body']}"
    result = json.loads(call_model(system, user, max_tokens=200))
    if result.get("topic") not in TOPICS:
        result["topic"] = "other"
    return result


def draft_reply(email, triage, order):
    system = Path("prompts/reply.txt").read_text()
    order_text = "No order number found." if order is None else (
        f"Order {order['order_id']}: {order['item']}, status {order['status']}, "
        f"shipped {order['shipped_on'] or 'not yet'}, value £{order['value_gbp']}"
    )
    user = (
        f"Customer first name: {email['from_name'].split()[0]}\n"
        f"Topic: {triage['topic']} (urgency {triage['urgency']})\n"
        f"{order_text}\n\n"
        f"Their email:\nSubject: {email['subject']}\n{email['body']}"
    )
    return call_model(system, user)


def main():
    orders = load_orders()
    with open(config.INBOX_CSV, newline="") as fh:
        emails = list(csv.DictReader(fh))
    rows = []
    for email in emails:
        triage = classify(email)
        match = ORDER_RE.search(email["body"] + " " + email["subject"])
        order = orders.get(match.group(0)) if match else None
        escalate = triage["urgency"] >= 3 or (order and float(order["value_gbp"]) > 150)
        rows.append({
            "message_id": email["message_id"],
            "topic": triage["topic"],
            "urgency": triage["urgency"],
            "escalate_to": config.ESCALATE_TO if escalate else "",
            "draft": draft_reply(email, triage, order),
        })
    with open(config.OUT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
