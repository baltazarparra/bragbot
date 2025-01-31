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

async def send_whatsapp_message(to, text):
    """Envia mensagens via API do WhatsApp"""
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
            "name": "hello_world",
            "language": { "code": "en_US" }
        }
    }

    app.logger.info(f"📤 Enviando mensagem para {to}: {text}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response_text = await response.text()
                app.logger.info(f"📩 Resposta do WhatsApp API: {response_text}")

                if response.status != 200:
                    app.logger.error(f"❌ Erro ao enviar mensagem: {response_text}")

                return response_text
    except Exception as e:
        app.logger.error(f"🔥 Falha no envio: {str(e)}")
        raise


@app.route("/webhook", methods=["GET", "POST"])
async def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        return challenge if token == VERIFY_TOKEN else "Token inválido", 403

    try:
        data = request.get_json()
        if not data.get('entry'):
            return jsonify({"status": "invalid_payload"}), 400

        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message = value['messages'][0]
            if message.get('type') != 'text':
                return jsonify({"status": "ignored"}), 200

            sender = message['from']
            text_body = message['text']['body'].strip().lower()
            timestamp = int(message['timestamp'])

            if text_body == 'bragfy':
                messages = get_user_messages(sender)
                
                if not messages:
                    response_text = "📭 Você ainda não tem mensagens armazenadas!"
                else:
                    table_header = "📅 Data   | 💬 Mensagem\n────────────────────────────\n"
                    table_rows = "\n".join([f"{row[0]} | {row[1]}" for row in messages])
                    response_text = f"📋 Seu histórico de mensagens:\n\n{table_header}{table_rows}"
                
                await send_whatsapp_message(sender, response_text)
                return jsonify({"status": "response_sent"}), 200
            else:
                save_message(
                    sender=sender,
                    text=text_body,
                    received_at=datetime.datetime.fromtimestamp(timestamp)
                )
                return jsonify({"status": "message_saved"}), 200

        return jsonify({"status": "ignored"}), 200

    except Exception as e:
        app.logger.error(f"Erro no webhook: {str(e)}")
        return jsonify({"status": "error", "details": str(e)}), 500