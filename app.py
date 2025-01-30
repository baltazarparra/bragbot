import os
import datetime
import aiohttp
import json
from flask import Flask, request, jsonify
from database import get_user_messages, save_message

app = Flask(__name__)

# Configurações
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', "meu_token_secreto_123!@#")
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID', "534183026446468")

@app.route("/webhook", methods=["GET", "POST"])
async def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        return challenge if token == VERIFY_TOKEN else "Token inválido", 403

    try:
        data = await request.get_json()
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message = value['messages'][0]
            sender = message['from']
            text_body = message['text']['body'].strip().lower()
            timestamp = int(message['timestamp'])

            # Comando Bragfy
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

            # Salvar mensagem normal
            save_message(
                sender=sender,
                text=text_body,
                received_at=datetime.datetime.fromtimestamp(timestamp)
            )
            return jsonify({"status": "message_saved"}), 200

        elif 'statuses' in value:
            for status in value['statuses']:
                if 'recipient_id' in status:
                    save_message(
                        sender=status['recipient_id'],
                        text="Status update",
                        received_at=datetime.datetime.fromtimestamp(int(status['timestamp']))
                    )
            return jsonify({"status": "status_processed"}), 200

        return jsonify({"status": "ignored"}), 200

    except Exception as e:
        app.logger.error(f"Erro no webhook: {str(e)}")
        return jsonify({"status": "error", "details": str(e)}), 500

async def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    error = await response.text()
                    app.logger.error(f"Erro ao enviar: {error}")
                return await response.json()
                
    except Exception as e:
        app.logger.error(f"Falha no envio: {str(e)}")
        raise