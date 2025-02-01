import os
import datetime
import aiohttp
from flask import Flask, request, jsonify
from database import get_user_messages, save_message

app = Flask(__name__)

# Configurações
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', "my_secret_token")
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID', "534183026446468")

async def send_whatsapp_text(to, text):
    """
    Envia uma mensagem de texto personalizada para o número `to`.
    """
    if not to or not text:
        app.logger.error("Invalid parameters for sending text message.")
        raise ValueError("Invalid parameters for sending text message.")

    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    app.logger.info(f"Sending text message to {to}: {text}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response_text = await response.text()
                app.logger.info(f"WhatsApp API response: {response_text}")
                if response.status != 200:
                    app.logger.error(f"Error sending text message: {response_text}")
                return response_text
    except Exception as e:
        app.logger.error(f"Failed to send text message: {str(e)}")
        raise

@app.route("/webhook", methods=["GET", "POST"])
async def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        return challenge if token == VERIFY_TOKEN else "Invalid token", 403

    try:
        data = request.get_json()
        app.logger.info(f"Received data: {data}")

        if not data or 'entry' not in data or not isinstance(data['entry'], list):
            app.logger.error("Invalid payload")
            return jsonify({"status": "invalid_payload"}), 400

        # Processa todas as entradas e mudanças
        for entry in data['entry']:
            if 'changes' not in entry or not isinstance(entry['changes'], list):
                continue

            for change in entry['changes']:
                if 'value' not in change:
                    continue

                value = change['value']
                if 'messages' not in value or not isinstance(value['messages'], list):
                    continue

                for message in value['messages']:
                    if message.get('type') != 'text':
                        continue

                    sender = message.get('from')
                    text_body = message.get('text', {}).get('body', '').strip().lower()
                    timestamp = int(message.get('timestamp', 0))
                    received_at = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

                    app.logger.info(f"Message received from {sender}: {text_body}")

                    if text_body == 'bragfy':
                        # Recupera as mensagens armazenadas para o remetente
                        messages = get_user_messages(sender)
                        app.logger.info(f"Retrieved messages for {sender}: {messages}")

                        if not messages:
                            response_text = "📭 You have no stored messages yet!"
                        else:
                            # Formata as mensagens em uma única string
                            formatted_messages = "\n".join([f"{row[0]} - {row[1]}" for row in messages])
                            response_text = formatted_messages

                        # Envia a mensagem de texto personalizada
                        await send_whatsapp_text(sender, response_text)
                        return jsonify({"status": "response_sent"}), 200
                    else:
                        # Salva qualquer outra mensagem no banco de dados
                        save_message(sender=sender, text=text_body, received_at=received_at)
                        return jsonify({"status": "message_saved"}), 200

        return jsonify({"status": "ignored"}), 200

    except Exception as e:
        app.logger.error(f"Error in webhook: {str(e)}")
        return jsonify({"status": "error", "details": str(e)}), 500
