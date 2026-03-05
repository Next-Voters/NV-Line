from twilio.rest import Client 
from dotenv import load_dotenv
from os import getenv 
from ...globalStates import categories_link
import psycopg2

load_dotenv()

account_sid = getenv("TWILIO_ACCOUNT_SID")
auth_token = getenv("TWILIO_AUTH_TOKEN")
postgres_connection_string = getenv("POSTGRES_CONNECTION_STRING")

client = Client(account_sid, auth_token)

def fetchSmsSubscribers(): 
    with psycopg2.connect(postgres_connection_string) as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    contact,
                    ARRAY(SELECT jsonb_array_elements_text(topics)) AS topics
                FROM subscriptions
                WHERE type_contact = 'sms';
            """)
            subscribers = cursor.fetchall()
    return subscribers

def sendSms():
    subscribers = fetchSmsSubscribers()

    for number, preferred_topics in subscribers:
        links = []
        for topic in preferred_topics: 
            links.append(categories_link[topic])
        
        links_text = "\n".join(links)

        client.messages.create(
            body=f"""
                Hey! This is your weekly digest. 

                {links_text}
            """,
            to=number
        )