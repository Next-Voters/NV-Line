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
            <html>
            <body>
                <h1>{category} - {today}</h1>
            """
        for bill in bills:
            fileId = str(uuid4())
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
        
        with open(fileId, 'w', encoding='utf-8') as file: 
            file.write(html)
        
        with open(fileId, 'rb') as file:
            response = (
                supabase.storage
                .from_("")
                .upload(
                    file=file,
                    path=f"public/{today}/{category}.html",
                    file_options={
                        "content-type": "text/html",
                        "cache-control": "3600", 
                        "upsert": False
                    }                        
                )
            )

            categories_link[category] = response.fullPath