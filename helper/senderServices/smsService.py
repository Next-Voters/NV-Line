from twilio.rest import Client 
from dotenv import load_dotenv
from os import getenv 
from ...globalStates import categories

load_dotenv()

account_sid = getenv("TWILIO_ACCOUNT_SID")
auth_token = getenv("TWILIO_AUTH_TOKEN")

client = Client(account_sid, auth_token)

from typing import Dict, List, Any

def build_sms_messages_one_bill_each(
    categorized_updates: Dict[str, List[Dict[str, Any]]],
    max_summary_chars: int = 700,
    include_category_header: bool = True,
) -> List[str]:
    messages: List[str] = []

    for category, bills in categorized_updates.items():
        if not bills:
            continue

        for bill in bills:
            name = bill.get("name", "Unknown")
            file_num = bill.get("fileNumber", "N/A")
            sponsors_list = bill.get("sponsors", []) or []
            sponsors = ", ".join(sponsors_list) if sponsors_list else "N/A"
            summary = bill.get("summarized", "No summary provided.") or "No summary provided."

            # Single, predictable truncation
            if len(summary) > max_summary_chars:
                summary = summary[: max_summary_chars - 3].rstrip() + "..."

            parts = []
            if include_category_header:
                parts.append(category)

            parts += [
                f"{name} ({file_num})",
                f"Summary: {summary}",
                f"Sponsors: {sponsors}",
            ]

            messages.append("\n".join(parts).strip())

    # Optional batch numbering
    if len(messages) > 1:
        total = len(messages)
        messages = [f"({i+1}/{total})\n{m}" for i, m in enumerate(messages)]

    return messages
