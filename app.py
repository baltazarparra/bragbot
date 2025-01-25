from flask import Flask, request

app = Flask(__name__)

# Defina o token de verificação
VERIFY_TOKEN = "meu_token_secreto_123!@#"

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    """
    Rota para verificar o webhook com o Facebook.
    """
    # O Facebook envia um parâmetro 'hub.verify_token' na requisição GET
    token_recebido = request.args.get("hub.verify_token")

    # Verifica se o token recebido é igual ao token definido
    if token_recebido == VERIFY_TOKEN:
        # Retorna o desafio (challenge) enviado pelo Facebook
        return request.args.get("hub.challenge"), 200
    else:
        # Retorna um erro se o token for inválido
        return "Token de verificação inválido", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Rota para receber as mensagens do WhatsApp.
    """
    try:
        # Recebe os dados do WhatsApp
        data = request.get_json()

        # Verifica se a mensagem é válida
        if not data or "entry" not in data:
            return "Dados inválidos", 400

        # Extrai o número do remetente e o conteúdo da mensagem
        user_number = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
        user_message = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

        # Exibe os dados no terminal (para depuração)
        print(f"Número do usuário: {user_number}")
        print(f"Mensagem recebida: {user_message}")

        # Responde ao WhatsApp com status 200 (sucesso)
        return "ok", 200
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        return "Erro interno", 500