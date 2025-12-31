# app/services/whatsapp_client.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")        # from Meta
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")  # from Meta
WHATSAPP_API_URL = f"https://graph.facebook.com/v21.0/{WHATSAPP_PHONE_ID}/messages"


def send_whatsapp_text(to: str, body: str):
    """
    Send a WhatsApp text message using WhatsApp Cloud API.
    `to` is a phone number in international format (e.g. '447398460844').
    """
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": body
        }
    }

    resp = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
    print("WhatsApp send response:", resp.status_code, resp.text)
    return resp

def send_whatsapp_text(to: str, body: str):
    print(f"📲 WhatsApp → {to}: {body}")

# app/services/whatsapp_client.py
def send_whatsapp_text(to: str, body: str):
    print(f"[WhatsApp → {to}] {body}")
