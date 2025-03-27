import psycopg2
from werkzeug.security import generate_password_hash
import os

def get_db_connection():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    return conn

def insertar_usuario():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO usuarios (nombre, password) VALUES (%s, %s)
    ''', ('empleado1', generate_password_hash('empleado1')))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    insertar_usuario()