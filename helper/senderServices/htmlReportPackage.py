from ...globalStates import categories
from dotenv import load_dotenv 
from os import getenv 
from supabase import create_client
from uuid import uuid4
from datetime import date
from ...globalStates import categories_link

load_dotenv()
url = getenv("SUPABASE_URL")
key = getenv("SUPABASE_KEY")
supabase = create_client(url, key)

today = date.today();

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
                    background: linear-gradient(135deg, #4064ff 0%, #7c4dff 100%);
                    color: #fff;
                    border-radius: 16px;
                    padding: 22px 20px;
                    box-shadow: 0 12px 30px rgba(17, 24, 39, 0.12);
                  }}
                  .title {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 800;
                    letter-spacing: -0.02em;
                  }}
                  .subtitle {{
                    margin: 6px 0 0;
                    color: rgba(255, 255, 255, 0.9);
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
                    box-shadow: 0 8px 20px rgba(17, 24, 39, 0.06);
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
                    <h1 class="title">{category}</h1>
                    <p class="subtitle">{today}</p>
                  </div>
                  <div class="grid">
            """
        for bill in bills:
            sponsors = ", ".join(bill.get("sponsors", []) or [])
            html += f"""
                    <div class="card">
                      <h3 class="bill-title">{bill.get("name", "Unknown")}</h3>
                      <div class="pill">{bill.get("fileNumber", "N/A")}</div>
                      <div class="label">Summary</div>
                      <p class="summary">{bill.get("summarized", "No summary provided.")}</p>
                      <div class="label">Sponsors</div>
                      <p class="sponsors">{sponsors or "—"}</p>
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