import os
from dotenv import load_dotenv
import psycopg2

# Carregue as variáveis de ambiente do arquivo .env
load_dotenv()

# Acesse as variáveis de ambiente
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Conecte ao banco de dados
def connect_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except psycopg2.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def criar_tabelas():
    conn = connect_db()
    if conn is None:
        return

    cur = conn.cursor()

    # Cria a tabela de usuários
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            identificador VARCHAR(20) PRIMARY KEY
        );
    """)

    # Cria a tabela de mensagens
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mensagens (
            id_mensagem SERIAL PRIMARY KEY,
            identificador VARCHAR(20) REFERENCES usuarios(identificador),
            texto_mensagem TEXT NOT NULL,
            data_envio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

criar_tabelas()