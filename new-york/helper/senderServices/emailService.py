import psycopg2
import smtplib
from os import getenv
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ...globalStates import categories_link

load_dotenv()

gmail_email = getenv("GMAIL_SECRET")
gmail_app_password = getenv("GMAIL_APP_PASSWORD")
postgres_connection_string = getenv("POSTGRES_CONNECTION_STRING")


def buildEmailHtml(buttons_html: str) -> str:
    html = f"""\
<!DOCTYPE html>
<html xmlns:v="urn:schemas-microsoft-com:vml"
      xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <!--[if !mso]><!-- -->
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <!--<![endif]-->
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="format-detection" content="telephone=no, date=no, address=no, email=no" />
  <meta name="x-apple-disable-message-reformatting" />

  <link href="https://fonts.googleapis.com/css?family=Manrope:ital,wght@0,400;0,600;0,700" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/css?family=Lato:ital,wght@0,400" rel="stylesheet" />

  <title>Weekly Digest</title>

  <style>
    html, body {{
      margin: 0 !important;
      padding: 0 !important;
      min-height: 100% !important;
      width: 100% !important;
      -webkit-font-smoothing: antialiased;
    }}
    * {{ -ms-text-size-adjust: 100%; }}
    #outlook a {{ padding: 0; }}
    .ReadMsgBody, .ExternalClass {{ width: 100%; }}
    .ExternalClass, .ExternalClass p, .ExternalClass td, .ExternalClass div,
    .ExternalClass span, .ExternalClass font {{ line-height: 100%; }}
    table, td, th {{
      mso-table-lspace: 0 !important;
      mso-table-rspace: 0 !important;
      border-collapse: collapse;
    }}
    body, td, th, p, div, li, a, span {{
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
      mso-line-height-rule: exactly;
    }}
    img {{
      border: 0;
      outline: 0;
      line-height: 100%;
      text-decoration: none;
      -ms-interpolation-mode: bicubic;
    }}
    a[x-apple-data-detectors] {{
      color: inherit !important;
      text-decoration: none !important;
    }}
    @media (min-width: 621px) {{
      .pc-lg-hide {{ display: none; }}
    }}
  </style>

  <!--[if mso]>
  <style>
    .pc-font-alt {{ font-family: Arial, Helvetica, sans-serif !important; }}
  </style>
  <![endif]-->
</head>

<body class="body pc-font-alt"
      bgcolor="#ffffff"
      style="width:100% !important; min-height:100% !important; margin:0 !important; padding:0 !important; background-color:#ffffff;">

  <table class="pc-project-body"
         width="100%"
         bgcolor="#ffffff"
         cellpadding="0"
         cellspacing="0"
         role="presentation">
    <tr>
      <td align="center">

        <table class="pc-project-container" width="600" cellpadding="0" cellspacing="0" role="presentation">

          <tr>
            <td bgcolor="#ffffff">
              <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                <tr>
                  <td background="https://cloudfilesdm.com/postcards/gradient-0e542413.png"
                      style="background-size:cover; padding:32px 0;">

                    <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                      <tr>
                        <td align="center" style="padding:0 40px;">
                          <span style="font-family:'Manrope', Arial, sans-serif; font-size:68px; font-weight:600; color:#ffffff; letter-spacing:-0.03em;">
                            Weekly Digest
                          </span>
                        </td>
                      </tr>

                      <tr>
                        <td align="center" style="padding-top:20px;">
                          <span style="font-family:'Lato', Arial, sans-serif; font-size:18px; color:#ffffff;">
                            Brought to you by Next Voters
                          </span>
                        </td>
                      </tr>
                    </table>

                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td bgcolor="#FFFFFF" style="padding:32px;">

              <img src="https://cloudfilesdm.com/postcards/Next_Voters_Logo__200x200__2-ba68a2ec.png"
                   width="60"
                   alt="Next Voters"
                   style="display:block; margin-bottom:20px;" />

              <p style="font-family:'Manrope', Arial, sans-serif; font-size:24px; font-weight:700; margin:0 0 12px 0;">
                Hello 👋
              </p>

              <p style="font-family:'Lato', Arial, sans-serif; font-size:20px; color:#6d6e73; margin:0;">
                Welcome to this week’s newsletter. We’ve curated the latest political updates and insights for you to enjoy!
              </p>

            </td>
          </tr>

          <tr>
            <td bgcolor="#f7f7f7" style="padding:24px;">

              <table width="100%" bgcolor="#ffffff"
                     cellpadding="0" cellspacing="0" role="presentation"
                     style="border-radius:16px; padding:40px 24px;">

                <tr>
                  <td align="center">
                    <span style="font-family:'Manrope', Arial, sans-serif; font-size:40px; font-weight:600; letter-spacing:-0.03em;">
                      Your summary
                    </span>
                  </td>
                </tr>

                <tr>
                  <td style="padding-top:32px;">
                    <p style="font-family:'Manrope', Arial, sans-serif; font-size:18px; font-weight:600; margin:0 0 8px 0;">
                      Check it out!
                    </p>

                    <p style="font-family:'Lato', Arial, sans-serif; font-size:16px; color:#6d6e73; margin:0;">
                      These buttons will take you to the summary for all legislation and meetings in your chosen categories.
                    </p>
                  </td>
                </tr>

                <!-- BUTTONS INSERTED HERE -->
                <tr>
                  <td align="center" style="padding-top:28px;">
                    {buttons_html}
                  </td>
                </tr>

              </table>

            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>

</body>
</html>
"""
    return html



def buildCategoryBtns(preferred_topics) -> str:
    chunks = []
    for topic in (preferred_topics or []):
        url = categories_link.get(topic)
        if not url:
            continue

        chunks.append(f"""
          <a href="{url}"
             target="_blank"
             style="
               display:inline-block;
               background-color:#4064ff;
               color:#ffffff;
               padding:14px 20px;
               border-radius:8px;
               font-family:'Manrope', Arial, sans-serif;
               font-weight:700;
               text-decoration:none;
               margin:6px;
             ">
            View {topic} →
          </a>
        """.strip())

    if not chunks:
        return """
          <p style="font-family:'Lato', Arial, sans-serif; font-size:16px; color:#6d6e73; margin:0;">
            No categories selected this week.
          </p>
        """.strip()

    return "\n".join(chunks)
    
def fetchEmailSubscribers():
    with psycopg2.connect(postgres_connection_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    contact,
                    topics
                FROM subscriptions
                WHERE type_contact = 'email';
            """)
            return cursor.fetchall()



def sendEmails():
    subscribers = fetchEmailSubscribers()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_email, gmail_app_password)

        for email, preferred_topics in subscribers:
            buttons_html = buildCategoryBtns(preferred_topics)
            html_body = buildEmailHtml(buttons_html)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = "NYC Legislation Update - Civic Line"
            msg["From"] = gmail_email
            msg["To"] = email
            msg.attach(MIMEText(html_body, "html"))

            server.sendmail(gmail_email, email, msg.as_string())
            print(f"Sent to {email}")
