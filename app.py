from flask import Flask, request, jsonify, render_template, session, flash, redirect, url_for, Response
import psycopg2
from psycopg2.extras import RealDictCursor
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from twilio.rest import Client
import os

app = Flask(__name__)
app.secret_key = 'TU_CLAVE_SECRETA_AQUI'  # ¡CAMBIA ESTO!

# Configuración para no escapar caracteres Unicode en respuestas JSON
app.config['JSON_AS_ASCII'] = False

# Credenciales de Twilio (Cuenta de Prueba)
account_sid = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # Tu Account SID
auth_token = "tu_auth_token"  # Tu Auth Token
twilio_number = "+11234567890"  # Tu número de Twilio

# Funciones de Base de Datos
def get_db_connection():
    try:
        conn = psycopg2.connect(
            os.environ.get('DATABASE_URL'),
            cursor_factory=RealDictCursor
        )
        print("Conexión a PostgreSQL establecida correctamente.")
        return conn
    except Exception as e:
        print(f"Error al conectar con la base de datos PostgreSQL: {e}")
        raise

def crear_tablas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            password TEXT NOT NULL
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id SERIAL PRIMARY KEY,
            nombre_cliente TEXT NOT NULL,
            telefono_cliente TEXT NOT NULL,
            fecha DATE NOT NULL,
            hora TIME NOT NULL,
            tratamiento TEXT NOT NULL,
            empleado_id INTEGER,
            duracion INTEGER DEFAULT 30,
            FOREIGN KEY (empleado_id) REFERENCES usuarios(id)
        );
    ''')
    conn.commit()
    conn.close()
    print("Tablas creadas correctamente en PostgreSQL.")

crear_tablas()

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
            cursor.execute('SELECT * FROM usuarios WHERE nombre = %s', (username,))
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
        print(f"Datos recibidos para la reserva: {data}")  # Depuración

        nombre = data['nombre']
        telefono = data['telefono']
        fecha = data['fecha']
        hora = data['hora']
        tratamiento = data['tratamiento']
        empleado_id = session.get('user_id')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Validar solapamientos de reservas
        try:
            print(f"Fecha: {fecha}, Hora: {hora}, Duración: {data.get('duracion', 30)}")
            cursor.execute('''
                SELECT COUNT(*) FROM reservas
                WHERE fecha = %s
                AND (
                    (hora + (duracion * interval '1 minute')) > %s
                    AND hora < (%s + (%s * interval '1 minute'))
                )
            ''', (fecha, hora, hora, int(data.get('duracion', 30))))
            solapamientos = cursor.fetchone()[0]
        except Exception as e:
            print(f"Error en la consulta SQL: {e}")
            return jsonify({'success': False, 'message': str(e)}), 500

        if solapamientos > 0:
            return jsonify({'success': False, 'message': 'Ya existe una reserva en el horario seleccionado.'}), 400

        # Insertar nueva reserva
        cursor.execute('''
            INSERT INTO reservas (nombre_cliente, telefono_cliente, fecha, hora, tratamiento, empleado_id, duracion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (nombre, telefono, fecha, hora, tratamiento, empleado_id, data.get('duracion', 30)))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Reserva creada exitosamente.'})
    except Exception as e:
        print(f"Error al crear la reserva: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener todas las reservas
        cursor.execute('SELECT * FROM reservas')
        reservas = cursor.fetchall()

        eventos = []
        for reserva in reservas:
            # Obtener el nombre del empleado asociado a la reserva
            if reserva['empleado_id'] is None:
                nombre_empleado = 'Empleado Desconocido'
            else:
                cursor.execute("SELECT nombre FROM usuarios WHERE id = %s", (reserva['empleado_id'],))
                empleado = cursor.fetchone()
                nombre_empleado = empleado['nombre'] if empleado else 'Empleado Desconocido'

            # Calcular la fecha y hora de inicio y fin de la reserva
            fecha_hora_inicio = datetime.datetime.fromisoformat(f"{reserva['fecha']} {reserva['hora']}")
            duracion = datetime.timedelta(minutes=int(reserva['duracion']))
            fecha_hora_fin = fecha_hora_inicio + duracion

            # Crear el evento con la estructura solicitada
            eventos.append({
                'id': reserva['id'],
                'title': f"{nombre_empleado}\nHora: {fecha_hora_inicio.strftime('%H:%M')}\nCliente: {reserva['nombre_cliente']}\nMóvil: {reserva['telefono_cliente']}\nTratamiento: {reserva['tratamiento']}",
                'start': fecha_hora_inicio.isoformat(),
                'end': fecha_hora_fin.isoformat(),
                'extendedProps': {
                    'telefono': reserva['telefono_cliente'],
                    'tratamiento': reserva['tratamiento'],  # Incluye el tratamiento
                    'empleado_id': reserva['empleado_id'] if reserva['empleado_id'] is not None else 'Desconocido',
                    'duracion': reserva['duracion']
                }
            })

        conn.close()
        return jsonify(eventos)
    except Exception as e:
        print(f"Error al obtener reservas: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/eliminar_reserva', methods=['POST'])
@login_required
def eliminar_reserva():
    try:
        data = request.get_json()
        if not data or 'id' not in data:
            return jsonify({'success': False, 'message': 'Falta el campo "id" en la solicitud.'}), 400

        reserva_id = data['id']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM reservas WHERE id = %s', (reserva_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error al eliminar la reserva: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/avanzar_dia', methods=['POST'])
@login_required
def avanzar_dia():
    # Lógica para avanzar un día en el calendario
    return jsonify({'success': True})

@app.route('/retroceder_dia', methods=['POST'])
@login_required
def retroceder_dia():
    # Lógica para retroceder un día en el calendario
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
