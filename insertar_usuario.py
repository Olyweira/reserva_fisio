import sqlite3
from werkzeug.security import generate_password_hash

def insertar_usuario():
    conn = sqlite3.connect('reservas.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO usuarios (nombre, password) VALUES (?, ?)
    ''', ('empleado1', generate_password_hash('empleado1')))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    insertar_usuario()