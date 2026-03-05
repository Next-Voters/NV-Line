from ...globalStates import categories
from dotenv import load_dotenv 
from os import getenv 
from supabase import create_client
from uuid import uuid4
from datetime import date
import html as _html
from ...globalStates import categories_link

load_dotenv()
url = getenv("SUPABASE_URL")
key = getenv("SUPABASE_KEY")
supabase = create_client(url, key)

today = date.today()


def format_summary_html(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return "<p class=\"summary\">No summary provided.</p>"

    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    bullet_lines = [ln for ln in lines if ln.startswith("*")]

    if bullet_lines and len(bullet_lines) == len(lines):
        lis = []
        for ln in bullet_lines:
            item = ln.lstrip("*").strip()
            if item:
                lis.append(f"<li>{_html.escape(item)}</li>")
        if not lis:
            return f"<p class=\"summary\">{_html.escape(raw)}</p>"
        return "<ul class=\"summary-list\">" + "".join(lis) + "</ul>"

    return "".join(f"<p class=\"summary\">{_html.escape(ln)}</p>" for ln in lines)

def buildHTMLReport(): 
    for category, bills in categories.items():
        html = f"""
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <title>{category} - {today}</title>
                <style>
                  :root {{
                    --bg: #f6f7fb;
                    --card: #ffffff;
                    --text: #111827;
                    --muted: #6b7280;
                    --border: #e5e7eb;
                    --accent: #4064ff;
                  }}
                  * {{ box-sizing: border-box; }}
                  body {{
                    margin: 0;
                    background: var(--bg);
                    color: var(--text);
                    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
                    line-height: 1.5;
                  }}
                  .container {{
                    max-width: 920px;
                    margin: 0 auto;
                    padding: 28px 16px 48px;
                  }}
                  .header {{
                    background: var(--card);
                    color: var(--text);
                    border: 1px solid var(--border);
                    border-radius: 16px;
                    padding: 18px 18px;
                  }}
                  .title {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 800;
                    letter-spacing: -0.02em;
                  }}
                  .subtitle {{
                    margin: 6px 0 0;
                    color: var(--muted);
                    font-size: 14px;
                    font-weight: 600;
                  }}
                  .grid {{
                    display: grid;
                    grid-template-columns: 1fr;
                    gap: 12px;
                    margin-top: 16px;
                  }}
                  .card {{
                    background: var(--card);
                    border: 1px solid var(--border);
                    border-radius: 14px;
                    padding: 16px;
                  }}
                  .bill-title {{
                    margin: 0;
                    font-size: 16px;
                    font-weight: 800;
                    letter-spacing: -0.01em;
                  }}
                  .pill {{
                    display: inline-block;
                    margin-top: 8px;
                    padding: 4px 10px;
                    border-radius: 999px;
                    background: rgba(64, 100, 255, 0.10);
                    color: var(--accent);
                    border: 1px solid rgba(64, 100, 255, 0.20);
                    font-size: 12px;
                    font-weight: 800;
                  }}
                  .label {{
                    margin: 12px 0 6px;
                    font-size: 12px;
                    font-weight: 900;
                    text-transform: uppercase;
                    letter-spacing: 0.06em;
                    color: var(--muted);
                  }}
                  p {{ margin: 0; }}
                  .summary {{ color: var(--text); }}
                  .summary-list {{
                    margin: 8px 0 0;
                    padding-left: 18px;
                    color: var(--text);
                  }}
                  .summary-list li {{ margin: 6px 0; }}
                  .sponsors {{ color: var(--muted); }}
                  .empty {{
                    background: var(--card);
                    border: 1px dashed var(--border);
                    border-radius: 14px;
                    padding: 18px;
                    color: var(--muted);
                  }}
                  @media (min-width: 860px) {{
                    .grid {{ grid-template-columns: 1fr 1fr; }}
                  }}
                </style>
              </head>
              <body>
                <div class="container">
                  <div class="header">
                    <h1 class="title">{_html.escape(str(category))}</h1>
                    <p class="subtitle">{today}</p>
                  </div>
                  <div class="grid">
            """
        for bill in bills:
            sponsors = ", ".join(bill.get("sponsors", []) or [])
            summary_html = format_summary_html(bill.get("summarized", ""))
            html += f"""
                    <div class="card">
                      <h3 class="bill-title">{_html.escape(str(bill.get("name", "Unknown")))}</h3>
                      <div class="pill">{_html.escape(str(bill.get("fileNumber", "N/A")))}</div>
                      <div class="label">Summary</div>
                      {summary_html}
                      <div class="label">Sponsors</div>
                      <p class="sponsors">{_html.escape(sponsors) if sponsors else "—"}</p>
                    </div>
            """
        if not bills:
            html += """
                    <div class=\"empty\">No legislation found for this category.</div>
            """

        html += """
                  </div>
                </div>
              </body>
            </html>
        """

        fileId = str(uuid4())

        with open(fileId, 'w', encoding='utf-8') as file: 
            file.write(html)
        
        with open(fileId, 'rb') as file:
            supabase.storage.from_("next-voters-summaries").upload(
                file=file,
                path=f"public/{today}/{category}.html",
                file_options={
                    "content-type": "text/html",
                    "cache-control": "3600", 
                    "upsert": False
                }                        
            )
            categories_link[category] = f"https://nextvoters.com/api/render?path={today}/{category}.html"