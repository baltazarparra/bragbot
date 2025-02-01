import datetime
import os
from dotenv import load_dotenv
import psycopg2
from flask import Flask

app = Flask(__name__)
load_dotenv()

def get_connection():
    """Cria e retorna uma conexão segura com o banco de dados."""
    try:
        return psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            sslmode='require'  # Conexão segura
        )
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        raise

def criar_tabelas():
    """Cria a tabela necessária se ela não existir."""
    try:
        conn = get_connection()
        cur = conn.cursor()
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
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def get_user_messages(phone_number):
    """Recupera e formata as mensagens armazenadas para um determinado número."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute('''
                SELECT TO_CHAR(received_at AT TIME ZONE 'UTC' AT TIME ZONE 'America/Sao_Paulo', 'DD/MM:HH24:MI'),
                       message_text
                FROM messages
                WHERE sender_number = %s
                ORDER BY received_at DESC
            ''', (phone_number,))
            messages = cur.fetchall()
            app.logger.info(f"Retrieved messages for {phone_number}: {messages}")
            return messages if messages else None
    except Exception as e:
        app.logger.error(f"Error retrieving messages: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def save_message(sender: str, text: str, received_at: datetime = None):
    """Salva uma nova mensagem no banco de dados."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO messages (sender_number, message_text, received_at)
                VALUES (%s, %s, %s)
            ''', (sender, text, received_at or datetime.datetime.now()))
            conn.commit()
            print(f"✅ Message from {sender} saved!")
            return True
    except Exception as e:
        print(f"❌ Error saving message: {str(e)}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        criar_tabelas()
        with get_connection() as test_conn:
            print("✅ Connection tested successfully!")
    except Exception as e:
        print(f"🔥 Critical failure: {str(e)}")
