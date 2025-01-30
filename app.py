import datetime
import aiohttp
from flask import Flask, Request, request, jsonify
from database import connect_db, get_user_messages, save_message

app = Flask(__name__)

# Defina o token de verificação
VERIFY_TOKEN = "meu_token_secreto_123!@#"

def criar_usuario(identificador):
    # Conecta ao banco de dados
    conn = connect_db()
    if conn is None:
        return "Erro ao conectar ao banco de dados", 500

    # Cria um cursor para executar queries
    cur = conn.cursor()

    # Verifique se o usuário já existe
    cur.execute("SELECT * FROM usuarios WHERE identificador = %s", (identificador,))
    if cur.fetchone() is None:
        # Crie o usuário
        cur.execute("INSERT INTO usuarios (identificador) VALUES (%s)", (identificador,))
        conn.commit()
        print(f"Usuário {identificador} criado com sucesso!")
    else:
        print(f"Usuário {identificador} já existe.")

    # Fecha o cursor e a conexão
    cur.close()
    conn.close()

def salvar_mensagem(identificador, texto_mensagem, data_envio):
    # Crie o usuário se ele não existir
    criar_usuario(identificador)
    
    # Conecta ao banco de dados
    conn = connect_db()
    if conn is None:
        return

    # Cria um cursor para executar queries
    cur = conn.cursor()

    # Salve a mensagem
    cur.execute("INSERT INTO mensagens (identificador, texto_mensagem, data_envio) VALUES (%s, %s, %s)", (identificador, texto_mensagem, data_envio))
    conn.commit()
    print(f"Mensagem de {identificador} salva com sucesso!")

    # Fecha o cursor e a conexão
    cur.close()
    conn.close()

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
    try:
        data = request.get_json()
        if "entry" in data and "changes" in data["entry"][0]:
            if "value" in data["entry"][0]["changes"][0]:
                value = data["entry"][0]["changes"][0]["value"]
                if "messages" in value:
                    mensagem = value["messages"][0]
                    identificador = mensagem["from"]
                    texto_mensagem = mensagem["text"]["body"]
                    data_envio = int(mensagem["timestamp"])
                    data_envio = datetime.datetime.fromtimestamp(data_envio).strftime("%Y-%m-%d")  # altera o formato da data
                    salvar_mensagem(identificador, texto_mensagem, data_envio)
                elif "statuses" in value:
                    for status in value["statuses"]:
                        if "recipient_id" in status:
                            identificador = status["recipient_id"]
                            texto_mensagem = "Mensagem de status recebida"
                            data_envio = int(status["timestamp"])
                            data_envio = datetime.datetime.fromtimestamp(data_envio).strftime("%Y-%m-%d")  # altera o formato da data
                            salvar_mensagem(identificador, texto_mensagem, data_envio)
        return "ok", 200
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        return "Erro interno", 500
    
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    
    try:
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message = value['messages'][0]
            sender = message['from']
            text = message['text']['body'].lower()

            if text == 'bragfy':
                # Buscar mensagens do usuário
                messages = get_user_messages(sender)
                
                if not messages:
                    response_text = "📭 Você ainda não tem mensagens armazenadas!"
                else:
                    # Formatar tabela
                    table_header = "📅 Data   | 💬 Mensagem\n────────────────────────────\n"
                    table_rows = "\n".join([f"{row[0]} | {row[1]}" for row in messages])
                    response_text = f"📋 Seu histórico de mensagens:\n\n{table_header}{table_rows}"

                # Enviar resposta via WhatsApp
                headers = {
                    "Authorization": f"Bearer {os.getenv('WHATSAPP_TOKEN')}",
                    "Content-Type": "application/json"
                }
                
                response_data = {
                    "messaging_product": "whatsapp",
                    "to": sender,
                    "text": {"body": response_text}
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"https://graph.facebook.com/v16.0/{os.getenv('PHONE_NUMBER_ID')}/messages",
                        headers=headers,
                        json=response_data
                    ) as response:
                        if response.status != 200:
                            print(f"Erro ao enviar resposta: {await response.text()}")
                
                return {"status": "ok"}

            else:
                # Processamento normal de mensagem
                save_message(sender, text)
                return {"status": "ok"}

    except Exception as e:
        print(f"Erro geral: {str(e)}")
        return {"status": "error"}, 500