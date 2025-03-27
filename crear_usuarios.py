import sqlite3
from werkzeug.security import generate_password_hash

def get_db_connection():
    conn = sqlite3.connect('reservas.db')
    conn.row_factory = sqlite3.Row
    return conn

def crear_usuario(nombre, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed_password = generate_password_hash(password)
    cursor.execute('''
        INSERT INTO usuarios (nombre, password)
        VALUES (?, ?)
    ''', (nombre, hashed_password))
    conn.commit()
    conn.close()
    print(f"Usuario '{nombre}' creado con éxito.")

if __name__ == '__main__':
    usuarios = [
        ('empleado1', 'empleado1'),
        ('empleado2', 'empleado2')
    ]
    for nombre, password in usuarios:
        crear_usuario(nombre, password)