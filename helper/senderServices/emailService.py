import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..storedValues import get_secret
from ...globalStates import categories

gmail_email = get_secret("gmail_email")
gmail_app_password = get_secret("gmail_app_password")
postgres_connection_string = get_secret("postgres_connection_string")

def buildEmailHtml(preferred_categories):
    preferred_categories = preferred_categories or []
    preferred_set = set(preferred_categories)

    html = """
    <html>
    <body>
        <h1>NYC Legislative Update</h1>
    """

    for category, bills in categories.items():
        if preferred_set and category not in preferred_set:
            continue

        html += f"<h2>{category}</h2>"
        if not bills:
            html += "<p>No new updates.</p>"
            continue

        for bill in bills:
            sponsors = ", ".join(bill.get("sponsors", []) or [])
            html += f"""
            <div>
                <h3>{bill.get("name", "Unknown")} ({bill.get("fileNumber", "N/A")})</h3>
                <p><b>Summary:</b> {bill.get("summarized", "No summary provided.")}</p>
                <p><b>Sponsors:</b> {sponsors}</p>
            </div>
            <hr>
            """

    html += "</body></html>"
    return html

def sendEmails():
    # Fetch subscribers
    with psycopg2.connect(postgres_connection_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    contact,
                    ARRAY(SELECT jsonb_array_elements_text(topics)) AS topics
                FROM subscriptions
                WHERE type_contact = 'email';
            """)
            subscribers = cursor.fetchall()

    # Open SMTP connection ONCE
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_email, gmail_app_password)

        for email, preferred_categories in subscribers:
            html_body = buildEmailHtml(preferred_categories)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = "TESTING"
            msg["From"] = gmail_email
            msg["To"] = email
            msg.attach(MIMEText(html_body, "html"))

            server.sendmail(gmail_email, email, msg.as_string())
            print(f"Sent to {email}")
