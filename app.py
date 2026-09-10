from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import sqlite3
from datetime import datetime, timedelta
import hashlib
import re
from functools import wraps

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_sesiones_12345'

# ---------- DECORADORES ----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor, inicia sesión primero', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session or session.get('rol') != 'admin':
            flash('Acceso denegado. Se requieren permisos de administrador', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ---------- FUNCIONES DE DÍAS HÁBILES ----------
def es_dia_habil(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        return fecha.weekday() < 5
    except:
        return False

def obtener_siguiente_dia_habil(fecha_str):
    fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
    while not es_dia_habil(fecha.strftime('%Y-%m-%d')):
        fecha += timedelta(days=1)
    return fecha.strftime('%Y-%m-%d')

def obtener_dias_semana():
    return ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

# ---------- BASE DE DATOS ----------
def init_db():
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    # Tabla de usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nombre TEXT NOT NULL,
                 email TEXT UNIQUE NOT NULL,
                 telefono TEXT,
                 password TEXT NOT NULL,
                 rol TEXT DEFAULT 'usuario')''')
    
    # Tabla de salas (con capacidad)
    c.execute('''CREATE TABLE IF NOT EXISTS salas (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nombre TEXT UNIQUE NOT NULL,
                 descripcion TEXT,
                 capacidad INTEGER DEFAULT 25)''')
    
    # Tabla de reservas (con num_alumnos y comentarios)
    c.execute('''CREATE TABLE IF NOT EXISTS reservas (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 sala_id INTEGER,
                 usuario_id INTEGER,
                 fecha TEXT,
                 hora_inicio TEXT,
                 hora_fin TEXT,
                 recurrente TEXT DEFAULT 'no',
                 estado TEXT DEFAULT 'pendiente',
                 mensaje_rechazo TEXT,
                 num_alumnos INTEGER DEFAULT 0,
                 comentarios TEXT,
                 FOREIGN KEY(sala_id) REFERENCES salas(id),
                 FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    # Tabla de clases fijas
    c.execute('''CREATE TABLE IF NOT EXISTS clases_fijas (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 sala_id INTEGER,
                 materia TEXT NOT NULL,
                 profesor TEXT NOT NULL,
                 num_alumnos INTEGER DEFAULT 0,
                 dia_semana TEXT NOT NULL,
                 hora_inicio TEXT NOT NULL,
                 hora_fin TEXT NOT NULL,
                 activo INTEGER DEFAULT 1,
                 FOREIGN KEY(sala_id) REFERENCES salas(id))''')
    
    # Insertar salas iniciales con capacidad
    salas_default = [
        ('CC1', 'Sala de cómputo 1 - 20 equipos', 25),
        ('CC2', 'Sala de cómputo 2 - 25 equipos', 25),
        ('CC3', 'Sala de cómputo 3 - 30 equipos', 64),
        ('CC4', 'Sala de cómputo 4 - 15 equipos', 64),
        ('CC5', 'Sala de cómputo 5 - 64 equipos (SOLO ADMIN)', 64)
    ]
    for nombre, desc, cap in salas_default:
        c.execute('INSERT OR IGNORE INTO salas (nombre, descripcion, capacidad) VALUES (?, ?, ?)', (nombre, desc, cap))
    
    # Crear usuario admin
    admin_pass = hashlib.sha256('admin123'.encode()).hexdigest()
    c.execute('''INSERT OR IGNORE INTO usuarios (nombre, email, password, rol) 
                 VALUES ('Administrador', 'admin@salas.com', ?, 'admin')''', (admin_pass,))
    
    conn.commit()
    conn.close()

init_db()

# ---------- RUTAS DE AUTENTICACIÓN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        conn = sqlite3.connect('salas.db')
        c = conn.cursor()
        usuario = c.execute('SELECT id, nombre, email, rol FROM usuarios WHERE email = ? AND password = ?', 
                           (email, password)).fetchone()
        conn.close()
        
        if usuario:
            session['usuario_id'] = usuario[0]
            session['usuario_nombre'] = usuario[1]
            session['usuario_email'] = usuario[2]
            session['rol'] = usuario[3]
            flash(f'¡Bienvenido Profesor@ {usuario[1]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        telefono = request.form.get('telefono', '')
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Email inválido', 'danger')
            return render_template('registro.html')
        
        try:
            conn = sqlite3.connect('salas.db')
            c = conn.cursor()
            c.execute('INSERT INTO usuarios (nombre, email, telefono, password, rol) VALUES (?, ?, ?, ?, "usuario")',
                     (nombre, email, telefono, password))
            conn.commit()
            conn.close()
            flash('Usuario registrado exitosamente. Inicia sesión.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('El email ya está registrado', 'danger')
    
    return render_template('registro.html')

# ---------- RUTAS PRINCIPALES ----------
@app.route('/')
@login_required
def index():
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    if session['rol'] == 'admin':
        salas = c.execute('SELECT * FROM salas').fetchall()
    else:
        salas = c.execute('SELECT * FROM salas WHERE nombre != "CC5"').fetchall()
    
    conn.close()
    
    hoy = datetime.now().strftime('%Y-%m-%d')
    if not es_dia_habil(hoy):
        hoy = obtener_siguiente_dia_habil(hoy)
    
    solicitudes_pendientes = 0
    if session['rol'] == 'admin':
        conn = sqlite3.connect('salas.db')
        c = conn.cursor()
        solicitudes_pendientes = c.execute('SELECT COUNT(*) FROM reservas WHERE estado = "pendiente"').fetchone()[0]
        conn.close()
    
    return render_template('index.html', 
                         salas=salas, 
                         hoy=hoy,
                         usuario=session['usuario_nombre'],
                         es_admin=session['rol'] == 'admin',
                         solicitudes_pendientes=solicitudes_pendientes)

@app.route('/calendario/<int:sala_id>')
@login_required
def get_calendario(sala_id):
    fecha = request.args.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    
    if not es_dia_habil(fecha):
        return jsonify({'error': 'Los fines de semana no están disponibles'}), 400
    
    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    nombre_dia = dias_semana[fecha_obj.weekday()]
    
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    sala_info = c.execute('SELECT nombre, capacidad FROM salas WHERE id = ?', (sala_id,)).fetchone()
    capacidad_sala = sala_info[1] if sala_info else 0
    nombre_sala = sala_info[0] if sala_info else 'Sala'
    
    clases_fijas = c.execute('''SELECT id, materia, profesor, num_alumnos, hora_inicio, hora_fin
                                FROM clases_fijas
                                WHERE sala_id = ? AND dia_semana = ? AND activo = 1''',
                           (sala_id, nombre_dia)).fetchall()
    
    reservas_activas = c.execute('''SELECT r.id, u.nombre, r.hora_inicio, r.hora_fin, r.usuario_id, r.num_alumnos
                                    FROM reservas r
                                    JOIN usuarios u ON r.usuario_id = u.id
                                    WHERE r.sala_id = ? AND r.fecha = ? AND r.estado = 'activa'
                                    ORDER BY r.hora_inicio''', (sala_id, fecha)).fetchall()
    
    conn.close()
    
    datos = []
    
    datos.append({
        'tipo': 'info',
        'capacidad': capacidad_sala,
        'nombre_sala': nombre_sala
    })
    
    for c in clases_fijas:
        datos.append({
            'id': f'clase_{c[0]}',
            'usuario': f'📚 {c[1]} - {c[2]} ({c[3]} alumnos)',
            'hora_inicio': c[4],
            'hora_fin': c[5],
            'es_mia': False,
            'es_clase': True,
            'tipo': 'clase'
        })
    
    for r in reservas_activas:
        datos.append({
            'id': r[0],
            'usuario': r[1],
            'hora_inicio': r[2],
            'hora_fin': r[3],
            'es_mia': r[4] == session['usuario_id'],
            'es_clase': False,
            'tipo': 'reserva',
            'num_alumnos': r[5]
        })
    
    return jsonify(datos)

@app.route('/reservar', methods=['POST'])
@login_required
def reservar():
    sala_id = int(request.form['sala_id'])
    usuario_id = session['usuario_id']
    fecha = request.form['fecha']
    hora_inicio = request.form['hora_inicio']
    hora_fin = request.form['hora_fin']
    num_alumnos = int(request.form.get('num_alumnos', 0))
    comentarios = request.form.get('comentarios', '')
    
    if not es_dia_habil(fecha):
        flash('❌ Solo se pueden hacer reservas de Lunes a Viernes', 'danger')
        return redirect(url_for('index'))
    
    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    nombre_dia = dias_semana[fecha_obj.weekday()]
    
    hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M')
    hora_fin_obj = datetime.strptime(hora_fin, '%H:%M')
    
    if hora_inicio_obj < datetime.strptime('07:00', '%H:%M') or hora_fin_obj > datetime.strptime('21:00', '%H:%M'):
        flash('El horario debe ser entre 7:00 AM y 9:00 PM', 'danger')
        return redirect(url_for('index'))
    
    if hora_inicio_obj >= hora_fin_obj:
        flash('La hora de inicio debe ser menor que la hora de fin', 'danger')
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    sala = c.execute('SELECT nombre, capacidad FROM salas WHERE id = ?', (sala_id,)).fetchone()
    if not sala:
        conn.close()
        flash('❌ Sala no encontrada', 'danger')
        return redirect(url_for('index'))
    
    nombre_sala = sala[0]
    capacidad_sala = sala[1]
    
    if nombre_sala == 'CC5' and session['rol'] != 'admin':
        conn.close()
        flash('La sala CC5 solo puede ser reservada por administradores', 'danger')
        return redirect(url_for('index'))
    
    if num_alumnos <= 0:
        conn.close()
        flash('⚠️ Debes indicar el número de alumnos', 'danger')
        return redirect(url_for('index'))
    
    if num_alumnos > capacidad_sala:
        conn.close()
        flash(f'⚠️ La sala {nombre_sala} tiene capacidad para {capacidad_sala} alumnos. Has solicitado {num_alumnos}.', 'danger')
        return redirect(url_for('index'))
    
    clase_conflicto = c.execute('''SELECT * FROM clases_fijas 
                                   WHERE sala_id = ? AND dia_semana = ? AND activo = 1
                                   AND ((hora_inicio < ? AND hora_fin > ?) OR
                                        (hora_inicio < ? AND hora_fin > ?) OR
                                        (hora_inicio >= ? AND hora_inicio < ?))''',
                              (sala_id, nombre_dia, hora_fin, hora_inicio, hora_fin, hora_inicio, hora_inicio, hora_fin)).fetchall()
    
    if clase_conflicto:
        conn.close()
        flash('⚠️ Este horario está ocupado por una clase fija', 'danger')
        return redirect(url_for('index'))
    
    conflicto = c.execute('''SELECT * FROM reservas 
                             WHERE sala_id = ? AND fecha = ? AND estado = 'activa'
                             AND ((hora_inicio < ? AND hora_fin > ?) OR
                                  (hora_inicio < ? AND hora_fin > ?) OR
                                  (hora_inicio >= ? AND hora_inicio < ?))''',
                         (sala_id, fecha, hora_fin, hora_inicio, hora_fin, hora_inicio, hora_inicio, hora_fin)).fetchall()
    
    if conflicto:
        conn.close()
        flash('⚠️ Este horario ya está ocupado', 'danger')
        return redirect(url_for('index'))
    
    c.execute('''INSERT INTO reservas (sala_id, usuario_id, fecha, hora_inicio, hora_fin, estado, num_alumnos, comentarios)
                 VALUES (?, ?, ?, ?, ?, 'pendiente', ?, ?)''',
             (sala_id, usuario_id, fecha, hora_inicio, hora_fin, num_alumnos, comentarios))
    conn.commit()
    conn.close()
    
    flash('✅ Solicitud de reserva enviada. Espera la confirmación del administrador.', 'success')
    return redirect(url_for('index'))

@app.route('/cancelar/<int:reserva_id>', methods=['POST'])
@login_required
def cancelar(reserva_id):
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    if session['rol'] == 'admin':
        c.execute('UPDATE reservas SET estado = "cancelada" WHERE id = ?', (reserva_id,))
    else:
        c.execute('UPDATE reservas SET estado = "cancelada" WHERE id = ? AND usuario_id = ? AND estado != "rechazada"', 
                 (reserva_id, session['usuario_id']))
    
    conn.commit()
    conn.close()
    flash('Reserva cancelada correctamente', 'info')
    return redirect(url_for('index'))

@app.route('/mis_reservas')
@login_required
def mis_reservas():
    usuario_id = session['usuario_id']
    
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    reservas = c.execute('''SELECT r.id, s.nombre, r.fecha, r.hora_inicio, r.hora_fin, 
                                   r.estado, r.mensaje_rechazo, r.num_alumnos, r.comentarios
                            FROM reservas r
                            JOIN salas s ON r.sala_id = s.id
                            WHERE r.usuario_id = ?
                            ORDER BY r.fecha DESC, r.hora_inicio DESC''', (usuario_id,)).fetchall()
    
    conn.close()
    
    return render_template('mis_reservas.html', 
                         reservas=reservas,
                         usuario=session['usuario_nombre'])

# ---------- RUTAS DE ADMINISTRACIÓN ----------
@app.route('/admin')
@admin_required
def admin_panel():
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    salas = c.execute('SELECT * FROM salas').fetchall()
    usuarios = c.execute('SELECT id, nombre, email, telefono, rol FROM usuarios').fetchall()
    
    solicitudes = c.execute('''SELECT r.id, s.nombre, u.nombre, u.email, r.fecha, r.hora_inicio, r.hora_fin,
                                      r.num_alumnos, r.comentarios
                               FROM reservas r
                               JOIN salas s ON r.sala_id = s.id
                               JOIN usuarios u ON r.usuario_id = u.id
                               WHERE r.estado = 'pendiente'
                               ORDER BY r.fecha, r.hora_inicio''').fetchall()
    
    clases_fijas = c.execute('''SELECT cf.id, s.nombre, cf.materia, cf.profesor, cf.num_alumnos, 
                                       cf.dia_semana, cf.hora_inicio, cf.hora_fin, cf.activo
                                FROM clases_fijas cf
                                JOIN salas s ON cf.sala_id = s.id
                                ORDER BY cf.dia_semana, cf.hora_inicio''').fetchall()
    
    total_reservas = c.execute('SELECT COUNT(*) FROM reservas WHERE estado = "activa"').fetchone()[0]
    reservas_hoy = c.execute('SELECT COUNT(*) FROM reservas WHERE fecha = ? AND estado = "activa"', 
                            (datetime.now().strftime('%Y-%m-%d'),)).fetchone()[0]
    total_pendientes = c.execute('SELECT COUNT(*) FROM reservas WHERE estado = "pendiente"').fetchone()[0]
    total_clases = c.execute('SELECT COUNT(*) FROM clases_fijas WHERE activo = 1').fetchone()[0]
    
    conn.close()
    
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    
    return render_template('admin.html', 
                         salas=salas,
                         usuarios=usuarios,
                         solicitudes=solicitudes,
                         clases_fijas=clases_fijas,
                         total_reservas=total_reservas,
                         reservas_hoy=reservas_hoy,
                         total_pendientes=total_pendientes,
                         total_clases=total_clases,
                         dias_semana=dias_semana)


# ---------- VISTA SEMANAL (NUEVA) ----------
@app.route('/admin/horario_semanal')
@admin_required
def horario_semanal():
    """Vista semanal de todas las clases y reservas"""
    
    sala_filtro = request.args.get('sala', 'todas')
    
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    salas = c.execute('SELECT id, nombre FROM salas ORDER BY nombre').fetchall()
    
    if sala_filtro == 'todas':
        clases = c.execute('''SELECT cf.id, s.nombre AS sala, cf.materia, cf.profesor, 
                                     cf.num_alumnos, cf.dia_semana, cf.hora_inicio, cf.hora_fin
                              FROM clases_fijas cf
                              JOIN salas s ON cf.sala_id = s.id
                              WHERE cf.activo = 1
                              ORDER BY cf.dia_semana, cf.hora_inicio''').fetchall()
    else:
        clases = c.execute('''SELECT cf.id, s.nombre AS sala, cf.materia, cf.profesor, 
                                     cf.num_alumnos, cf.dia_semana, cf.hora_inicio, cf.hora_fin
                              FROM clases_fijas cf
                              JOIN salas s ON cf.sala_id = s.id
                              WHERE cf.activo = 1 AND cf.sala_id = ?
                              ORDER BY cf.dia_semana, cf.hora_inicio''', (sala_filtro,)).fetchall()
    
    hoy = datetime.now()
    lunes = hoy - timedelta(days=hoy.weekday())
    viernes = lunes + timedelta(days=4)
    fecha_inicio = lunes.strftime('%Y-%m-%d')
    fecha_fin = viernes.strftime('%Y-%m-%d')
    
    if sala_filtro == 'todas':
        reservas = c.execute('''SELECT r.id, s.nombre AS sala, u.nombre AS usuario, 
                                       r.fecha, r.hora_inicio, r.hora_fin, r.num_alumnos, r.comentarios
                                FROM reservas r
                                JOIN salas s ON r.sala_id = s.id
                                JOIN usuarios u ON r.usuario_id = u.id
                                WHERE r.estado = 'activa' 
                                AND r.fecha BETWEEN ? AND ?
                                ORDER BY r.fecha, r.hora_inicio''', (fecha_inicio, fecha_fin)).fetchall()
    else:
        reservas = c.execute('''SELECT r.id, s.nombre AS sala, u.nombre AS usuario, 
                                       r.fecha, r.hora_inicio, r.hora_fin, r.num_alumnos, r.comentarios
                                FROM reservas r
                                JOIN salas s ON r.sala_id = s.id
                                JOIN usuarios u ON r.usuario_id = u.id
                                WHERE r.estado = 'activa' 
                                AND r.fecha BETWEEN ? AND ?
                                AND r.sala_id = ?
                                ORDER BY r.fecha, r.hora_inicio''', (fecha_inicio, fecha_fin, sala_filtro)).fetchall()
    
    conn.close()
    
    horas = []
    for h in range(7, 21):
        horas.append(f"{h:02d}:00 - {h+1:02d}:00")
    
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    
    colores = [
        '#e8f5e9', '#e3f2fd', '#fff9c4', '#ffebee',
        '#ffe0b2', '#fff59d', '#f8bbd0', '#d1c4e9',
        '#b2dfdb', '#ffccbc', '#f0f4c3', '#c5cae9'
    ]
    
    matriz = {}
    for dia in dias:
        matriz[dia] = {}
        for hora in horas:
            matriz[dia][hora] = None
    
    materias_colores = {}
    color_index = 0
    
    for clase in clases:
        materia = clase[2]
        dia = clase[5]
        hora_inicio = clase[6]
        
        if materia not in materias_colores:
            materias_colores[materia] = colores[color_index % len(colores)]
            color_index += 1
        
        hora_obj = int(hora_inicio.split(':')[0])
        hora_key = f"{hora_obj:02d}:00 - {hora_obj+1:02d}:00"
        
        if hora_key in matriz[dia]:
            matriz[dia][hora_key] = {
                'tipo': 'clase',
                'materia': materia,
                'profesor': clase[3],
                'sala': clase[1],
                'alumnos': clase[4],
                'color': materias_colores[materia]
            }
    
    for reserva in reservas:
        fecha_obj = datetime.strptime(reserva[3], '%Y-%m-%d')
        dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes'}
        dia = dias_map.get(fecha_obj.weekday())
        
        if not dia:
            continue
        
        hora_inicio = reserva[4]
        hora_obj = int(hora_inicio.split(':')[0])
        hora_key = f"{hora_obj:02d}:00 - {hora_obj+1:02d}:00"
        
        if hora_key in matriz[dia]:
            if matriz[dia][hora_key] is None:
                matriz[dia][hora_key] = {
                    'tipo': 'reserva',
                    'usuario': reserva[2],
                    'sala': reserva[1],
                    'alumnos': reserva[6],
                    'comentarios': reserva[7],
                    'color': '#ffcc80'
                }
    
    return render_template('horario_semanal.html',
                         matriz=matriz,
                         dias=dias,
                         horas=horas,
                         salas=salas,
                         sala_filtro=sala_filtro,
                         materias_colores=materias_colores,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin)


@app.route('/admin/reserva/aprobar/<int:reserva_id>', methods=['POST'])
@admin_required
def aprobar_reserva(reserva_id):
    mensaje = request.form.get('mensaje', '')
    
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    reserva = c.execute('''SELECT r.id, r.sala_id, r.usuario_id, r.fecha, r.hora_inicio, r.hora_fin,
                                  s.nombre, u.nombre, u.email
                           FROM reservas r
                           JOIN salas s ON r.sala_id = s.id
                           JOIN usuarios u ON r.usuario_id = u.id
                           WHERE r.id = ?''', (reserva_id,)).fetchone()
    
    if not reserva:
        conn.close()
        flash('Reserva no encontrada', 'danger')
        return redirect(url_for('admin_panel'))
    
    fecha = reserva[3]
    hora_inicio = reserva[4]
    hora_fin = reserva[5]
    sala_id = reserva[1]
    
    conflicto = c.execute('''SELECT * FROM reservas 
                             WHERE sala_id = ? AND fecha = ? AND estado = 'activa'
                             AND id != ?
                             AND ((hora_inicio < ? AND hora_fin > ?) OR
                                  (hora_inicio < ? AND hora_fin > ?) OR
                                  (hora_inicio >= ? AND hora_inicio < ?))''',
                         (sala_id, fecha, reserva_id, hora_fin, hora_inicio, hora_fin, hora_inicio, hora_inicio, hora_fin)).fetchall()
    
    if conflicto:
        c.execute('UPDATE reservas SET estado = "rechazada", mensaje_rechazo = ? WHERE id = ?',
                 ('La sala ya fue reservada por otro usuario en este horario', reserva_id))
        conn.commit()
        conn.close()
        flash('❌ La reserva fue rechazada porque el horario ya está ocupado', 'warning')
        return redirect(url_for('admin_panel'))
    
    fecha_obj = datetime.strptime(fecha, '%Y-%m-%d')
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    nombre_dia = dias_semana[fecha_obj.weekday()]
    
    clase_conflicto = c.execute('''SELECT * FROM clases_fijas 
                                   WHERE sala_id = ? AND dia_semana = ? AND activo = 1
                                   AND ((hora_inicio < ? AND hora_fin > ?) OR
                                        (hora_inicio < ? AND hora_fin > ?) OR
                                        (hora_inicio >= ? AND hora_inicio < ?))''',
                              (sala_id, nombre_dia, hora_fin, hora_inicio, hora_fin, hora_inicio, hora_inicio, hora_fin)).fetchall()
    
    if clase_conflicto:
        c.execute('UPDATE reservas SET estado = "rechazada", mensaje_rechazo = ? WHERE id = ?',
                 ('El horario coincide con una clase fija', reserva_id))
        conn.commit()
        conn.close()
        flash('❌ La reserva fue rechazada porque coincide con una clase fija', 'warning')
        return redirect(url_for('admin_panel'))
    
    c.execute('UPDATE reservas SET estado = "activa" WHERE id = ?', (reserva_id,))
    conn.commit()
    conn.close()
    
    flash(f'✅ Reserva aprobada para {reserva[7]} en {reserva[6]} el {fecha} de {hora_inicio} a {hora_fin}', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/reserva/rechazar/<int:reserva_id>', methods=['POST'])
@admin_required
def rechazar_reserva(reserva_id):
    mensaje = request.form.get('mensaje_rechazo', '')
    
    if not mensaje:
        flash('⚠️ Debes escribir un mensaje para el usuario', 'danger')
        return redirect(url_for('admin_panel'))
    
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    c.execute('UPDATE reservas SET estado = "rechazada", mensaje_rechazo = ? WHERE id = ?', (mensaje, reserva_id))
    conn.commit()
    conn.close()
    
    flash(f'❌ Reserva rechazada. Mensaje enviado', 'warning')
    return redirect(url_for('admin_panel'))

@app.route('/admin/clase/agregar', methods=['POST'])
@admin_required
def agregar_clase():
    sala_id = int(request.form['sala_id'])
    materia = request.form['materia']
    profesor = request.form['profesor']
    num_alumnos = int(request.form['num_alumnos'] or 0)
    dia_semana = request.form['dia_semana']
    hora_inicio = request.form['hora_inicio']
    hora_fin = request.form['hora_fin']
    
    hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M')
    hora_fin_obj = datetime.strptime(hora_fin, '%H:%M')
    
    if hora_inicio_obj < datetime.strptime('07:00', '%H:%M') or hora_fin_obj > datetime.strptime('21:00', '%H:%M'):
        flash('El horario debe ser entre 7:00 AM y 9:00 PM', 'danger')
        return redirect(url_for('admin_panel'))
    
    if hora_inicio_obj >= hora_fin_obj:
        flash('La hora de inicio debe ser menor que la hora de fin', 'danger')
        return redirect(url_for('admin_panel'))
    
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    sala = c.execute('SELECT capacidad FROM salas WHERE id = ?', (sala_id,)).fetchone()
    if sala and num_alumnos > sala[0]:
        conn.close()
        flash(f'⚠️ La sala tiene capacidad para {sala[0]} alumnos. Has solicitado {num_alumnos}.', 'danger')
        return redirect(url_for('admin_panel'))
    
    conflicto = c.execute('''SELECT * FROM clases_fijas 
                             WHERE sala_id = ? AND dia_semana = ? AND activo = 1
                             AND ((hora_inicio < ? AND hora_fin > ?) OR
                                  (hora_inicio < ? AND hora_fin > ?) OR
                                  (hora_inicio >= ? AND hora_inicio < ?))''',
                         (sala_id, dia_semana, hora_fin, hora_inicio, hora_fin, hora_inicio, hora_inicio, hora_fin)).fetchall()
    
    if conflicto:
        conn.close()
        flash('⚠️ Ya existe una clase en este horario para esta sala', 'danger')
        return redirect(url_for('admin_panel'))
    
    c.execute('''INSERT INTO clases_fijas (sala_id, materia, profesor, num_alumnos, dia_semana, hora_inicio, hora_fin)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
             (sala_id, materia, profesor, num_alumnos, dia_semana, hora_inicio, hora_fin))
    conn.commit()
    conn.close()
    
    flash(f'✅ Clase de {materia} agendada para {dia_semana}', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/clase/eliminar/<int:clase_id>', methods=['POST'])
@admin_required
def eliminar_clase(clase_id):
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    clase = c.execute('SELECT materia, dia_semana FROM clases_fijas WHERE id = ?', (clase_id,)).fetchone()
    
    if clase:
        c.execute('DELETE FROM clases_fijas WHERE id = ?', (clase_id,))
        conn.commit()
        flash(f'✅ Clase de {clase[0]} ({clase[1]}) eliminada', 'success')
    else:
        flash('❌ Clase no encontrada', 'danger')
    
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/sala/agregar', methods=['POST'])
@admin_required
def agregar_sala():
    nombre = request.form['nombre'].strip().upper()
    descripcion = request.form['descripcion']
    capacidad = int(request.form.get('capacidad', 25))
    
    if not nombre:
        flash('El nombre de la sala es requerido', 'danger')
        return redirect(url_for('admin_panel'))
    
    try:
        conn = sqlite3.connect('salas.db')
        c = conn.cursor()
        c.execute('INSERT INTO salas (nombre, descripcion, capacidad) VALUES (?, ?, ?)', (nombre, descripcion, capacidad))
        conn.commit()
        conn.close()
        flash(f'Sala {nombre} agregada exitosamente (Capacidad: {capacidad})', 'success')
    except sqlite3.IntegrityError:
        flash(f'La sala {nombre} ya existe', 'danger')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/sala/eliminar/<int:sala_id>', methods=['POST'])
@admin_required
def eliminar_sala(sala_id):
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    sala = c.execute('SELECT nombre FROM salas WHERE id = ?', (sala_id,)).fetchone()
    nombre_sala = sala[0] if sala else 'Sala'
    
    c.execute('UPDATE reservas SET estado = "cancelada" WHERE sala_id = ? AND estado = "activa"', (sala_id,))
    c.execute('DELETE FROM clases_fijas WHERE sala_id = ?', (sala_id,))
    c.execute('DELETE FROM salas WHERE id = ?', (sala_id,))
    
    conn.commit()
    conn.close()
    
    flash(f'✅ Sala {nombre_sala} eliminada', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/usuario/cambiar_rol/<int:usuario_id>', methods=['POST'])
@admin_required
def cambiar_rol_usuario(usuario_id):
    nuevo_rol = request.form['rol']
    
    if usuario_id == session['usuario_id']:
        flash('No puedes cambiar tu propio rol', 'danger')
        return redirect(url_for('admin_panel'))
    
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    c.execute('UPDATE usuarios SET rol = ? WHERE id = ?', (nuevo_rol, usuario_id))
    conn.commit()
    conn.close()
    flash('Rol de usuario actualizado', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/usuario/eliminar/<int:usuario_id>', methods=['POST'])
@admin_required
def eliminar_usuario(usuario_id):
    if usuario_id == session['usuario_id']:
        flash('⚠️ No puedes eliminar tu propia cuenta', 'danger')
        return redirect(url_for('admin_panel'))
    
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    usuario = c.execute('SELECT nombre, email FROM usuarios WHERE id = ?', (usuario_id,)).fetchone()
    
    if not usuario:
        conn.close()
        flash('❌ Usuario no encontrado', 'danger')
        return redirect(url_for('admin_panel'))
    
    nombre_usuario = usuario[0]
    email_usuario = usuario[1]
    
    c.execute('''UPDATE reservas 
                 SET estado = 'cancelada' 
                 WHERE usuario_id = ? AND estado IN ('activa', 'pendiente')''', (usuario_id,))
    reservas_canceladas = c.rowcount
    
    c.execute('DELETE FROM usuarios WHERE id = ?', (usuario_id,))
    
    conn.commit()
    conn.close()
    
    mensaje = f'✅ Usuario "{nombre_usuario}" ({email_usuario}) eliminado.'
    if reservas_canceladas > 0:
        mensaje += f' Se cancelaron {reservas_canceladas} reservas.'
    mensaje += ' El usuario puede registrarse de nuevo con el mismo correo.'
    
    flash(mensaje, 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/reservas/todas')
@admin_required
def todas_reservas():
    conn = sqlite3.connect('salas.db')
    c = conn.cursor()
    
    reservas = c.execute('''SELECT r.id, s.nombre, u.nombre, u.email, r.fecha, r.hora_inicio, r.hora_fin, 
                                   r.estado, r.mensaje_rechazo, r.num_alumnos, r.comentarios
                            FROM reservas r
                            JOIN salas s ON r.sala_id = s.id
                            JOIN usuarios u ON r.usuario_id = u.id
                            ORDER BY r.fecha DESC, r.hora_inicio''').fetchall()
    conn.close()
    
    return render_template('todas_reservas.html', reservas=reservas)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)