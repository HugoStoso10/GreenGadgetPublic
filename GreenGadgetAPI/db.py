# Bibliotecas
import psycopg
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

#Conexão à base de dados
def get_connection():
    return psycopg.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )