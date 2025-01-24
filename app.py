import os
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests

# Carregar as variáveis de ambiente do arquivo .env
load_dotenv()

app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    logger.info("Recebida uma solicitação GET no webhook")
    token_recebido = request.args.get("hub.verify_token")
    if token_recebido == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    else:
        logger.error("Token de verificação inválido")
        return "Token de verificação inválido", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    logger.info("Recebida uma solicitação POST no webhook")
    try:
        data = request.get_json()
        logger.info(f"Dados recebidos: {data}")
        if not data or "entry" not in data:
            logger.error("Dados inválidos recebidos")
            return "Dados inválidos", 400

        user_number = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
        user_message = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

        logger.info(f"Número do usuário: {user_number}")
        logger.info(f"Mensagem recebida: {user_message}")

        response_message = "Obrigado pela sua mensagem! Estamos processando sua solicitação."
        send_message(user_number, response_message)

        return "ok", 200
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
        return "Erro interno", 500

def send_message(to, message):
    logger.debug(f"Enviando mensagem para {to}: {message}")
    # URL correta para enviar mensagens via WhatsApp API
    url = "https://graph.facebook.com/v22.0/me/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
    else:
        logger.info("Mensagem enviada com sucesso.")
    return response.json()

