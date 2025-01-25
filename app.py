import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify

# Configuração inicial
load_dotenv()  # Carrega variáveis do .env
app = Flask(__name__)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('WhatsApp-Bot')

# Variáveis de ambiente
VERIFY_TOKEN = "meu_token_secreto_123!@#"
ACCESS_TOKEN = "EAAI0zpTDkWcBO8na42qhaSMRG6rWPq5fPIXx35moKFeeiUQefuN6p8p1lZAScaFCqSu5cdoYPaF4yyPn0Ca5xKCA9oASefjgii2NWWA2XzvzPczcwTC2TpZCPsDuteNfmJjh2BGsiaNMbsxQkZCPfl6aiO83k7Tor8ai717kb0LCqBr25ZAN52XVwdubTmZA7N84sYCRwCJ1m83lR5xgED4srCWHjo6DvbjTTdUCW6P68uEO2UVEZD"

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Endpoint de verificação do webhook exigido pelo WhatsApp
    """
    try:
        # Recebe parâmetros da requisição
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        logger.info(f"Tentativa de verificação - Mode: {mode}, Token: {token}")

        # Verifica o token e o modo
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Verificação bem-sucedida!")
            return challenge, 200
        else:
            logger.warning("Falha na verificação - Token ou modo inválido")
            return "Verificação falhou", 403

    except Exception as e:
        logger.error(f"Erro na verificação: {str(e)}")
        return "Erro no servidor", 500

@app.route('/webhook', methods=['POST'])
def handle_messages():
    """
    Endpoint principal para receber mensagens do WhatsApp
    """
    try:
        # Processa a notificação
        data = request.get_json()
        logger.info(f"Payload recebido: {data}")

        # Verifica estrutura básica do payload
        if not data or 'entry' not in data:
            logger.error("Estrutura de dados inválida")
            return jsonify({"status": "error", "message": "Invalid payload"}), 400

        # Extrai informações básicas
        entry = data['entry'][0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        contacts = value.get('contacts', [{}])[0]
        
        # Dados da mensagem
        user_number = contacts.get('wa_id', 'N/A')
        message_data = value.get('messages', [{}])[0]
        
        if message_data.get('type') != 'text':
            logger.info("Mensagem não textual recebida, ignorando")
            return jsonify({"status": "ignored"}), 200

        # Mensagem de texto
        message_body = message_data.get('text', {}).get('body', '')
        logger.info(f"Nova mensagem de {user_number}: {message_body}")

        # Aqui você pode adicionar lógica de processamento posteriormente

        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)