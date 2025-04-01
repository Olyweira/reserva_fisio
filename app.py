from flask import Flask, request, jsonify, render_template, session, flash, redirect, url_for, Response
import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from twilio.rest import Client
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_key')  # Usar variable de entorno

# Configuración para no escapar caracteres Unicode en respuestas JSON
app.config['JSON_AS_ASCII'] = False

# --- Credenciales de Twilio ---
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')

# --- Funciones de Base de Datos ---

def get_db_connection():
    conn = sqlite3.connect('reservas.db')
    conn.row_factory = sqlite3.Row
    return conn

def crear_tablas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_cliente TEXT NOT NULL,
            telefono_cliente TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            tratamiento TEXT NOT NULL,
            empleado_id INTEGER,
            duracion INTEGER DEFAULT 30,
            FOREIGN KEY (empleado_id) REFERENCES usuarios(id)
        )
    ''')
    conn.commit()
    conn.close()  # ¡IMPORTANTE! Cierra la conexión.


# --- Decorador para proteger rutas ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Función para enviar SMS ---
def enviar_sms_twilio(destino, mensaje):
    enviar_sms = os.environ.get('ENVIAR_SMS', 'true').lower() == 'true'

    if enviar_sms:
        try:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                to=destino,
                from_=twilio_number,
                body=mensaje
            )
            print(f"SMS enviado con SID: {message.sid}")
            return True
        except Exception as e:
            print(f"Error al enviar SMS: {e}")
            flash(f"Error al enviar SMS: {e}", "danger")
            return False
    else:
        print("Envío de SMS desactivado (variable de entorno ENVIAR_SMS)")
        flash("Reserva creada. El envío de SMS está desactivado temporalmente.", "info")
        return True

# --- Rutas ---

@app.route('/')
def index():
    response = app.response_class(
        response=render_template('index.html', logged_in=session.get('logged_in'), username=session.get('username')),
        status=200,
        mimetype='text/html'
    )
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/calendario')
@login_required
def calendario():
    response = app.response_class(
        response=render_template('calendario.html', logged_in=session.get('logged_in'), username=session.get('username')),
        status=200,
        mimetype='text/html'
    )
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            print(f"Datos recibidos: username={username}, password={password}")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM usuarios WHERE nombre = ?', (username,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user['password'], password):
                session['logged_in'] = True
                session['username'] = user['nombre']
                session['user_id'] = user['id']
                flash('¡Inicio de sesión exitoso!', 'success')
                return redirect(url_for('index'))  # Redirige a la página principal
            else:
                return jsonify({'success': False, 'message': 'Usuario o contraseña incorrectos.'}), 401
        except Exception as e:
            print(f"Error en el inicio de sesión: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

    return render_template('login.html')  # Renderiza para GET

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('user_id', None)
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('index'))

@app.route('/reservar', methods=['POST'])
@login_required
def reservar():
    try:
        data = request.get_json()
        nombre = data['nombre']
        telefono = data['telefono']
        fecha = data['fecha']
        hora = data['hora']
        tratamiento = data['tratamiento']
        empleado_id = session.get('user_id')  # Usa el user_id de la sesión

        duracion = int(data['duracion'])  # ¡Importante! Convertir a entero

        conn = get_db_connection()
        cursor = conn.cursor()

        # --- VALIDACIÓN DE INDIBA ---
        if (tratamiento == 'indiba'):
            fecha_hora_inicio_reserva = datetime.datetime.fromisoformat(f"{fecha} {hora}")
            fecha_hora_fin_reserva = fecha_hora_inicio_reserva + datetime.timedelta(minutes=int(duracion))

            cursor.execute('''
                SELECT * FROM reservas
                WHERE tratamiento = 'indiba'
                AND fecha = ?
                AND (
                    (hora >= ? AND hora < ?)
                    OR (datetime(fecha || ' ' || hora, '+' || ? || ' minutes') > datetime(? || ' ' || ?)
                        AND datetime(fecha || ' ' || hora) < datetime(? || ' ' || ?, '+' || ? || ' minutes')
                    )
                )
            ''', (fecha, hora, fecha_hora_fin_reserva.time().isoformat(), duracion, fecha, hora, fecha, hora, duracion))

            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Ya hay una reserva de Indiba en ese horario.'})
        # --- FIN VALIDACIÓN INDIBA ---

        cursor.execute('''
            INSERT INTO reservas (nombre_cliente, telefono_cliente, fecha, hora, tratamiento, empleado_id, duracion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nombre, telefono, fecha, hora, tratamiento, empleado_id, duracion))  # Inserta la duración y el empleado_id
        conn.commit()
        print(f"Reserva insertada: {nombre, telefono, fecha, hora, tratamiento, empleado_id, duracion}")
        conn.close()

        # --- Envío de SMS usando la función auxiliar ---
        mensaje = f"Hola {nombre}! Tu reserva de {tratamiento} para el {fecha} a las {hora} ha sido confirmada."
        if not enviar_sms_twilio(telefono, mensaje):
            # Manejar el caso en que el envío falle (opcional)
            pass

        return jsonify({'success': True})

    except Exception as e:
        print(str(e))
        return jsonify({'success': False, 'message': str(e)})

@app.route('/obtener_empleados')
@login_required
def obtener_empleados():
    conn = get_db_connection()
    cursor = conn.cursor()
    empleados = cursor.execute('SELECT id, nombre FROM usuarios').fetchall()
    conn.close()
    return jsonify([{'id': row['id'], 'nombre': row['nombre']} for row in empleados])


@app.route('/obtener_reservas', methods=['GET'])
@login_required
def obtener_reservas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reservas')
    reservas = cursor.fetchall()
    print(f"Reservas obtenidas: {reservas}")

    eventos = []
    for reserva in reservas:
        # Obtener el nombre del empleado (usando un nuevo cursor)
        nombre_cursor = conn.cursor()  # Crea un NUEVO cursor
        nombre_cursor.execute("SELECT nombre FROM usuarios WHERE id = ?", (reserva['empleado_id'],))
        empleado = nombre_cursor.fetchone()
        nombre_empleado = empleado['nombre'] if empleado else 'Desconocido'
        nombre_cursor.close()  # Cierra el cursor *inmediatamente*

        fecha_hora_inicio = datetime.datetime.fromisoformat(f"{reserva['fecha']} {reserva['hora']}")
        duracion = datetime.timedelta(minutes=int(reserva['duracion']))  # Usamos la duración de la reserva
        fecha_hora_fin = fecha_hora_inicio + duracion
        end_time = fecha_hora_fin.isoformat()

        eventos.append({
            'id': reserva['id'],  # Incluir el ID de la reserva
            'title': f"{nombre_empleado}: {reserva['nombre_cliente']} - {reserva['tratamiento']}",
            'start': f"{reserva['fecha']}T{reserva['hora']}",
            'end': end_time,
            'extendedProps': {
                'telefono': reserva['telefono_cliente'],
                'tratamiento': reserva['tratamiento'],
                'empleado_id': reserva['empleado_id'],
                'duracion': reserva['duracion']
            }
        })

    conn.close()
    print(f"Eventos generados: {eventos}")
    return jsonify(eventos)

@app.route('/eliminar_reserva/<int:reserva_id>', methods=['DELETE'])
@login_required
def eliminar_reserva(reserva_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reservas WHERE id = ?', (reserva_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Error al eliminar la reserva: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    crear_tablas()
    app.run(debug=True)