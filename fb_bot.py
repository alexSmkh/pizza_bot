import os

import requests
from flask import Flask, request

from fb_tools import get_menu
from dotenv import load_dotenv

from redis_db import get_database_connection

app = Flask(__name__)
database = None
FACEBOOK_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")


def handle_start(sender_id, user_reply):
    menu = get_menu(user_reply) if user_reply in PIZZA_CATEGORIES.keys() \
        else get_menu()

    params = {"access_token": FACEBOOK_TOKEN}
    headers = {"Content-Type": "application/json"}
    request_content = {
        "recipient": {
            "id": sender_id,
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": menu
                }
            }
        }
    }

    response = requests.post(
        "https://graph.facebook.com/v5.0/me/messages",
        params=params, headers=headers, json=request_content
    )
    # response.raise_for_status()
    return 'MENU'


def handle_menu(sender_id, user_reply):
    if user_reply in PIZZA_CATEGORIES:
        return handle_start(sender_id, user_reply)


def handle_users_reply(sender_id, user_reply):
    global database
    database = get_database_connection(database)

    states_functions = {
        'START': handle_start,
        'MENU': handle_menu,
    }
    formatted_sender_id = f'fb:user_{sender_id}'
    recorded_state = database.get(formatted_sender_id)
    if not recorded_state or recorded_state.decode(
            "utf-8") not in states_functions.keys():
        user_state = "START"
    else:
        user_state = recorded_state.decode("utf-8")
    if user_reply == "/start":
        user_state = "START"
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(sender_id, user_reply)
        database.set(formatted_sender_id, next_state)
    except Exception as err:
        print(err)


@app.route('/', methods=['GET'])
def verify():
    """
    При верификации вебхука у Facebook он отправит запрос на этот адрес. На него нужно ответить VERIFY_TOKEN.
    """
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():
    """
    Основной вебхук, на который будут приходить сообщения от Facebook.
    """
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                    user_reply = messaging_event["message"]["text"]
                    handle_users_reply(sender_id, user_reply)
                elif messaging_event.get("postback"):
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                    user_reply = messaging_event['postback']['payload']
                    handle_users_reply(sender_id, user_reply)
    return "OK", 200


if __name__ == '__main__':
    load_dotenv()
    app.run(debug=True)