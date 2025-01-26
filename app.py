from flask import Flask, request, jsonify
from database import connect_db

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

def salvar_mensagem(identificador, mensagem):
    # Crie o usuário se ele não existir
    criar_usuario(identificador)
    
    # Conecta ao banco de dados
    conn = connect_db()
    if conn is None:
        return "Erro ao conectar ao banco de dados", 500

    # Cria um cursor para executar queries
    cur = conn.cursor()

    # Salve a mensagem
    cur.execute("INSERT INTO mensagens (identificador, texto_mensagem) VALUES (%s, %s)", (identificador, mensagem))
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
                if "statuses" in value:
                    for status in value["statuses"]:
                        if "recipient_id" in status:
                            identificador = status["recipient_id"]
                            mensagem = "Mensagem de status recebida"
                            salvar_mensagem(identificador, mensagem)
                elif "messages" in value:
                    mensagem = value["messages"][0]
                    identificador = mensagem["from"]
                    mensagem = mensagem["text"]["body"]
                    salvar_mensagem(identificador, mensagem)
        return "ok", 200
    except Exception as e:
        print(f"Erro ao processar mensagem: {e}")
        return "Erro interno", 500