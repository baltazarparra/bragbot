from flask import Flask, request
import requests

app = Flask(__name__)

# Defina o token de verificação e o token de acesso
VERIFY_TOKEN = "meu_token_secreto_123!@#"
ACCESS_TOKEN = "seu_access_token_aqui"  # Substitua pelo seu token de acesso do Facebook

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    token_recebido = request.args.get("hub.verify_token")
    if token_recebido == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    else:
        return "Token de verificação inválido", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        if not data or "entry" not in data:
            return "Dados inválidos", 400

        user_number = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
        user_message = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

        print(f"Número do usuário: {user_number}")
        print(f"Mensagem recebida: {user_message}")

        response_message = "Obrigado pela sua mensagem! Estamos processando sua solicitação."
        send_message(user_number, response_message)

        return "ok", 200
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        return "Erro interno", 500

def send_message(to, message):
    url = f"https://graph.facebook.com/v13.0/{to}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()