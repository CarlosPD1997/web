import sqlite3
import hashlib
import os

print("=" * 70)
print("🔄 RECREANDO BASE DE DATOS DESDE CERO")
print("=" * 70)

# 1. Eliminar la base de datos existente si existe
if os.path.exists('salas.db'):
    os.remove('salas.db')
    print("✅ Base de datos anterior eliminada")
else:
    print("ℹ️ No existía base de datos anterior")

# 2. Crear nueva base de datos
conn = sqlite3.connect('salas.db')
c = conn.cursor()

print("\n📊 Creando tablas...")

# Tabla de usuarios
c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             nombre TEXT NOT NULL,
             email TEXT UNIQUE NOT NULL,
             telefono TEXT,
             password TEXT NOT NULL,
             rol TEXT DEFAULT 'usuario')''')
print("✅ Tabla 'usuarios' creada")

# Tabla de salas (CON CAPACIDAD)
c.execute('''CREATE TABLE IF NOT EXISTS salas (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             nombre TEXT UNIQUE NOT NULL,
             descripcion TEXT,
             capacidad INTEGER DEFAULT 25)''')
print("✅ Tabla 'salas' creada (con capacidad)")

# Tabla de reservas (CON TODAS LAS COLUMNAS)
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
print("✅ Tabla 'reservas' creada (con todas las columnas)")

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
print("✅ Tabla 'clases_fijas' creada")

print("\n📚 Insertando datos iniciales...")

# Insertar salas con CAPACIDAD
salas_default = [
    ('CC1', 'Sala de cómputo 1 - 20 equipos', 25),
    ('CC2', 'Sala de cómputo 2 - 25 equipos', 25),
    ('CC3', 'Sala de cómputo 3 - 30 equipos', 64),
    ('CC4', 'Sala de cómputo 4 - 15 equipos', 64),
    ('CC5', 'Sala de cómputo 5 - 10 equipos (SOLO ADMIN)', 10)
]

for nombre, desc, cap in salas_default:
    c.execute('INSERT OR IGNORE INTO salas (nombre, descripcion, capacidad) VALUES (?, ?, ?)', (nombre, desc, cap))
    print(f"  ✅ {nombre} (Capacidad: {cap} alumnos)")

# Crear usuario admin
admin_pass = hashlib.sha256('admin123'.encode()).hexdigest()
c.execute('''INSERT OR IGNORE INTO usuarios (nombre, email, password, rol) 
             VALUES ('Administrador', 'admin@salas.com', ?, 'admin')''', (admin_pass,))
print("✅ Usuario admin creado (admin@salas.com / admin123)")

# Verificar que todo está bien
print("\n📊 VERIFICACIÓN:")

c.execute('SELECT nombre, capacidad FROM salas')
salas = c.fetchall()
print("  Salas:")
for s in salas:
    print(f"    - {s[0]}: {s[1]} alumnos")

c.execute('SELECT nombre, email, rol FROM usuarios')
usuarios = c.fetchall()
print("  Usuarios:")
for u in usuarios:
    print(f"    - {u[0]} ({u[1]}) - {u[2]}")

conn.commit()
conn.close()

print("\n" + "=" * 70)
print("✅ ¡BASE DE DATOS RECREADA EXITOSAMENTE!")
print("🚀 Ahora ejecuta: python app.py")
print("=" * 70)