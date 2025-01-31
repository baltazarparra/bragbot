import datetime
import os
from dotenv import load_dotenv
from flask import Flask
import psycopg2

app = Flask(__name__)

load_dotenv()

def get_connection():
    """Cria e retorna uma conexão segura com o banco de dados"""
    try:
        return psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            sslmode='require'  # Conexão segura com Render
        )
    except Exception as e:
        print(f"❌ Erro de conexão: {str(e)}")
        raise

def criar_tabelas():
    """Cria as tabelas necessárias com a nova estrutura"""
    try:
        conn = get_connection()
        cur = conn.cursor()

        # Criação da tabela messages, se não existir
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                sender_number VARCHAR(20) NOT NULL,
                message_text TEXT NOT NULL,
                received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'received'
            );
            
            CREATE INDEX IF NOT EXISTS idx_sender ON messages(sender_number);
        """)

        conn.commit()
        print("✅ Tabelas criadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def get_user_messages(phone_number):
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute('''
                SELECT 
                    TO_CHAR(received_at AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo', 'DD/MM:HH24:MI'),
                    message_text
                FROM messages 
                WHERE sender_number = %s
                ORDER BY received_at DESC
            ''', (phone_number,))
            
            messages = cur.fetchall()
            app.logger.info(f"Mensagens recuperadas para {phone_number}: {messages}")  # Log das mensagens
            return messages if messages else None
    except Exception as e:
        app.logger.error(f"Erro na busca: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()


def save_message(sender: str, text: str, received_at: datetime = None):
    """Salva uma nova mensagem no banco de dados"""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO messages (sender_number, message_text, received_at)
                VALUES (%s, %s, %s)
            ''', (
                sender, 
                text,
                received_at or datetime.datetime.now()  # Valor padrão se não fornecido
            ))
            conn.commit()
            print(f"✅ Mensagem de {sender} salva!")
            return True
    except Exception as e:
        print(f"❌ Erro ao salvar mensagem: {str(e)}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# Verificação inicial
if __name__ == "__main__":
    try:
        criar_tabelas()
        with get_connection() as test_conn:
            print("✅ Conexão testada com sucesso!")
    except Exception as e:
        print(f"🔥 Falha crítica: {str(e)}")
