import requests

import config

def send_message_to_fb_messenger(recipient_id: str, message_text: str) -> None:
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={config.FB_PAGE_ACCESS_TOKEN}"
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("Message sent successfully.")
    else:
        print("Failed to sent message. Status code:", response.status_code)

def send_text_message(recipient_id: str, message_text: str):
    send_message_to_fb_messenger(recipient_id, message_text)


def send_quick_reply(recipient_id: str, text: str, quick_replies: list[str]):
    quick_reply_items = [{
        "content_type": "text",
        "title": item,
        "payload": item
    } for item in quick_replies]

    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={config.FB_PAGE_ACCESS_TOKEN}"
    data = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": text,
            "quick_replies": quick_reply_items
        }
    }
    response = requests.post(url, json=data)
    if response.status_code != 200:
        print("❌ Failed to send quick reply:", response.status_code)


def send_button_message(recipient_id: str, text: str, zalo_url: str, hotline: str, extra_button=None):
    buttons = [
        {
            "type": "web_url",
            "url": zalo_url,
            "title": "💬 Nhắn qua Zalo"
        },
        {
            "type": "phone_number",
            "title": "📞 Gọi Hotline",
            "payload": hotline
        }
    ]
    if extra_button:
        buttons.append(extra_button)

    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={config.FB_PAGE_ACCESS_TOKEN}"
    data = {
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": text,
                    "buttons": buttons
                }
            }
        }
    }
    response = requests.post(url, json=data)
    if response.status_code != 200:
        print("❌ Failed to send button message:", response.status_code)
