import json
import smtplib
import os
import time
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from supabase import create_client, Client
from prompt import summarizer, classifer

MAX_INPUT_CHARS = 80_000

load_dotenv()
openai_client = OpenAI()

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SMTP
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", 587))
SMTP_USER     = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASS")
EMAIL_FROM    = os.getenv("EMAIL_FROM", SMTP_USER)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

BASE_URL     = "https://sdcounty.legistar.com"
CALENDAR_URL = f"{BASE_URL}/Calendar.aspx"
TABLE_ID     = "ctl00_ContentPlaceHolder1_gridUpcomingMeetings_ctl00"


# ── Scraping ──────────────────────────────────────────────────────────────────

def get_agenda_links():
    print(f"Fetching calendar: {CALENDAR_URL}\n")
    response = requests.get(CALENDAR_URL, headers=HEADERS)
    response.raise_for_status()

    soup  = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"id": TABLE_ID})
    if not table:
        raise ValueError(f"Table '{TABLE_ID}' not found.")

    tbody = table.find("tbody")
    if not tbody:
        raise ValueError("No <tbody> in table.")

    rows = tbody.find_all("tr")
    print(f"Total rows: {len(rows)} — processing first 3 only.\n")

    agenda_links = []
    for i, row in enumerate(rows[:3]):
        anchor = row.find("a", id=lambda x: x and "hypAccessibleAgendaHTML" in x)
        if anchor and anchor.get("href"):
            href     = anchor["href"]
            full_url = href if href.startswith("http") else f"{BASE_URL}/{href.lstrip('/')}"
            print(f"Row {i+1}: {full_url}")
            agenda_links.append((i + 1, full_url))
        else:
            print(f"Row {i+1}: No agenda link found.")

    return agenda_links


def fetch_agenda_text(url):
    print(f"\nFetching agenda: {url}")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    lines   = [l.strip() for l in soup.get_text(separator="\n").splitlines()]
    cleaned = "\n".join(l for l in lines if l)

    if len(cleaned) > MAX_INPUT_CHARS:
        print(f"  ⚠ Text truncated from {len(cleaned):,} → {MAX_INPUT_CHARS:,} chars.")
        cleaned = cleaned[:MAX_INPUT_CHARS]

    return cleaned


# ── AI: Summarize & Classify ──────────────────────────────────────────────────

def call_openai_with_retry(messages, retries=3, wait=60):
    for attempt in range(1, retries + 1):
        try:
            return openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
        except Exception as e:
            if "429" in str(e) and attempt < retries:
                sleep_time = wait * attempt
                print(f"  ⚠ Rate limit hit. Waiting {sleep_time}s before retry {attempt}/{retries - 1}...")
                time.sleep(sleep_time)
            else:
                raise


def summarize_agenda(cleaned_text):
    print("  → Summarizing...")
    resp = call_openai_with_retry([
        {"role": "system", "content": summarizer},
        {"role": "user",   "content": cleaned_text},
    ])
    return resp.choices[0].message.content


def classify_summary(summary):
    print("  → Classifying topics...")
    resp = call_openai_with_retry([
        {"role": "system", "content": classifer},
        {"role": "user",   "content": summary},
    ])
    raw = resp.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:]).rstrip("`").strip()

    try:
        topics = json.loads(raw)
        if isinstance(topics, list):
            return topics
    except json.JSONDecodeError:
        pass

    return [t.strip().strip('"') for t in raw.strip("[]").split(",") if t.strip()]


# ── Summary Registry ──────────────────────────────────────────────────────────
#
# summaries_by_topic: dict[topic, list of {summary, url, row_num}]
# e.g. {
#   "Immigration": [{"summary": "...", "url": "...", "row_num": 1}, ...],
#   "Economy":     [{"summary": "...", "url": "...", "row_num": 2}],
# }

def build_summary_registry(agenda_links: list) -> dict:
    """
    Process all agenda links, returning a registry mapping
    each topic → list of summary records.
    """
    registry = defaultdict(list)

    for row_num, url in agenda_links:
        print(f"\n{'=' * 60}")
        print(f"Processing Row {row_num} — {url}")
        print("=" * 60)

        try:
            cleaned_text = fetch_agenda_text(url)
            summary      = summarize_agenda(cleaned_text)
            topics       = classify_summary(summary)

            print(f"  Topics classified: {topics}")
            print(f"  Summary preview: {summary[:200]}...")

            record = {"summary": summary, "url": url, "row_num": row_num, "topics": topics}

            for topic in topics:
                registry[topic].append(record)

        except Exception as e:
            print(f"  Error on row {row_num}: {e}")

    return dict(registry)


# ── Database (Supabase SDK) ───────────────────────────────────────────────────

def get_all_subscribers() -> list[dict]:
    """
    Returns all email subscribers as:
    [{"contact": "email@example.com", "topics": ["Immigration", "Economy"]}, ...]
    """
    print("\n→ Fetching all email subscribers from Supabase...")
    result = (
        supabase.table("subscriptions")
        .select("contact, topics")
        .eq("type_contact", "email")
        .execute()
    )
    print(f"  {len(result.data)} subscriber(s) found.")
    return result.data


# ── Email ─────────────────────────────────────────────────────────────────────

def build_html_email(subscriber_topics: list[str], registry: dict) -> str:
    """
    Build a single digest email for a subscriber containing all summaries
    from every topic they care about — grouped by topic section.
    """
    all_topics_html = "".join(
        f'<span style="display:inline-block;background:#e8f0fe;color:#1a56db;'
        f'border-radius:12px;padding:3px 12px;margin:3px;font-size:13px;">{t}</span>'
        for t in subscriber_topics
    )

    # Build one section per topic the subscriber cares about
    sections_html = ""
    for topic in subscriber_topics:
        records = registry.get(topic, [])
        if not records:
            continue

        # Topic header
        sections_html += f"""
        <tr>
          <td style="padding:24px 40px 8px;">
            <p style="margin:0;font-size:11px;font-weight:700;letter-spacing:1.5px;
                      text-transform:uppercase;color:#2563eb;">{topic}</p>
            <hr style="border:none;border-top:2px solid #e5eaf2;margin:8px 0 0;"/>
          </td>
        </tr>"""

        # One card per summary under this topic
        for rec in records:
            paragraphs = "".join(
                f"<p style='margin:0 0 10px;font-size:14px;color:#374151;line-height:1.65;'>{para.strip()}</p>"
                for para in rec["summary"].split("\n") if para.strip()
            )
            sections_html += f"""
        <tr>
          <td style="padding:12px 40px 20px;">
            <div style="background:#f8faff;border-left:4px solid #2563eb;
                        border-radius:6px;padding:20px 24px;">
              {paragraphs}
              <a href="{rec['url']}"
                 style="display:inline-block;margin-top:10px;font-size:13px;
                        color:#2563eb;text-decoration:none;font-weight:600;">
                View Full Agenda →
              </a>
            </div>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>SD County Meeting Digest</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:40px 0;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:10px;
                    box-shadow:0 2px 12px rgba(0,0,0,.08);overflow:hidden;">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#1a3a6b 0%,#2563eb 100%);padding:32px 40px;">
            <p style="margin:0;color:rgba(255,255,255,.7);font-size:11px;
                      letter-spacing:2px;text-transform:uppercase;">San Diego County</p>
            <h1 style="margin:8px 0 4px;color:#ffffff;font-size:26px;font-weight:700;">
              Meeting Agenda Digest
            </h1>
            <p style="margin:0;color:rgba(255,255,255,.75);font-size:13px;">
              Summaries across your subscribed topics
            </p>
          </td>
        </tr>

        <!-- Subscribed topics strip -->
        <tr>
          <td style="background:#f0f4ff;padding:14px 40px;border-bottom:1px solid #e5eaf2;">
            <p style="margin:0 0 8px;font-size:11px;color:#6b7280;
                      text-transform:uppercase;letter-spacing:1px;">Your Topics</p>
            {all_topics_html}
          </td>
        </tr>

        <!-- Dynamic topic sections -->
        {sections_html}

        <!-- Footer -->
        <tr>
          <td style="background:#f8faff;padding:20px 40px;
                     border-top:1px solid #e5eaf2;text-align:center;">
            <p style="margin:0;color:#9ca3af;font-size:12px;">
              You received this because you subscribed to SD County meeting alerts.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_digest_emails(registry: dict):
    """
    For every subscriber, collect all summaries matching their topics
    and send one combined digest email.
    """
    subscribers = get_all_subscribers()
    all_registry_topics = set(registry.keys())

    for sub in subscribers:
        email          = sub["contact"]
        sub_topics     = sub.get("topics") or []

        # Find overlap between what the subscriber wants and what we have summaries for
        relevant_topics = [t for t in sub_topics if t in all_registry_topics]

        if not relevant_topics:
            print(f"  — No matching summaries for {email}, skipping.")
            continue

        print(f"\n  → Sending digest to {email} (topics: {relevant_topics})")

        html_body = build_html_email(relevant_topics, registry)
        subject   = f"SD County Meeting Digest — {', '.join(relevant_topics)}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_FROM
        msg["To"]      = email
        msg.attach(MIMEText(html_body, "html"))

        try:
            if SMTP_PORT == 465:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(EMAIL_FROM, email, msg.as_string())
            else:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(EMAIL_FROM, email, msg.as_string())
            print(f"  ✓ Sent to {email}")
        except Exception as e:
            print(f"  ✗ Failed to send to {email}: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    agenda_links = get_agenda_links()

    if not agenda_links:
        print("\nNo agenda links found.")
        return

    # Step 1: Scrape + summarize + classify all agendas → build registry
    registry = build_summary_registry(agenda_links)

    print(f"\n\n{'=' * 60}")
    print("Summary Registry:")
    for topic, records in registry.items():
        print(f"  {topic}: {len(records)} summary(s)")
    print("=" * 60)

    if not registry:
        print("No summaries generated — nothing to send.")
        return

    # Step 2: Send one digest email per subscriber covering all their topics
    send_digest_emails(registry)

    print(f"\n{'=' * 60}")
    print("Done.")


if __name__ == "__main__":
    main()