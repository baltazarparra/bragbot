import os
import datetime
import aiohttp
from flask import Flask, request, jsonify
from database import get_user_messages, save_message

app = Flask(__name__)

# Configurações
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', "meu_token_secreto_123!@#")
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID', "534183026446468")

async def send_whatsapp_template(to, customer_name, customer_messages):
    """Envia uma mensagem usando um template do WhatsApp"""
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "bragfy_report",  # Certifique-se de que esse é o nome exato no WhatsApp Business Manager
            "language": { "code": "pt_BR" },
            "components": [{
                "type": "body",
                "parameters": [
                    { "type": "text", "text": customer_name },
                    { "type": "text", "text": customer_messages }
                ]
            }]
        }
    }

    app.logger.info(f"📤 Enviando template para {to}: {customer_messages}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response_text = await response.text()
                app.logger.info(f"📩 Resposta do WhatsApp API: {response_text}")

                if response.status != 200:
                    app.logger.error(f"❌ Erro ao enviar template: {response_text}")

                return response_text
    except Exception as e:
        app.logger.error(f"🔥 Falha no envio do template: {str(e)}")
        raise


@app.route("/webhook", methods=["GET", "POST"])
async def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        return challenge if token == VERIFY_TOKEN else "Token inválido", 403

    try:
        data = request.get_json()
        if not data or 'entry' not in data or not isinstance(data['entry'], list):
            return jsonify({"status": "invalid_payload"}), 400

        # Iterar sobre as entradas (pode haver múltiplas)
        for entry in data['entry']:
            if 'changes' not in entry or not isinstance(entry['changes'], list):
                continue  # Ignorar entradas inválidas

            for change in entry['changes']:
                if 'value' not in change:
                    continue  # Ignorar mudanças inválidas

                value = change['value']
                if 'messages' not in value or not isinstance(value['messages'], list):
                    continue  # Ignorar valores sem mensagens

                # Processar cada mensagem
                for message in value['messages']:
                    if message.get('type') != 'text':
                        continue  # Ignorar mensagens que não são texto

                    sender = message.get('from')
                    text_body = message.get('text', {}).get('body', '').strip().lower()
                    timestamp = int(message.get('timestamp', 0))
                    received_at = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

                    if text_body == 'bragfy':
                        messages = get_user_messages(sender)

                        if not messages:
                            response_text = "📭 Você ainda não tem mensagens armazenadas!"
                            await send_whatsapp_template(sender, sender, response_text)
                        else:
                            formatted_messages = "\n".join([f"{row[0]} - {row[1]}" for row in messages])
                            await send_whatsapp_template(sender, sender, formatted_messages)

                        return jsonify({"status": "response_sent"}), 200
                    else:
                        save_message(sender=sender, text=text_body, received_at=received_at)
                        return jsonify({"status": "message_saved"}), 200

        return jsonify({"status": "ignored"}), 200

    except Exception as e:
        app.logger.error(f"Erro no webhook: {str(e)}")
        return jsonify({"status": "error", "details": str(e)}), 500
