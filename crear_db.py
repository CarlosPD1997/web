import sqlite3
import hashlib

print("🔧 Creando base de datos desde cero...")

# Conectar y crear la base de datos
conn = sqlite3.connect('salas.db')
c = conn.cursor()

# Eliminar tablas si existen (para empezar limpio)
c.execute('DROP TABLE IF EXISTS reservas')
c.execute('DROP TABLE IF EXISTS salas')
c.execute('DROP TABLE IF EXISTS usuarios')

print("✅ Tablas antiguas eliminadas")

# Crear tabla de usuarios
c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             nombre TEXT NOT NULL,
             email TEXT UNIQUE NOT NULL,
             password TEXT NOT NULL,
             rol TEXT DEFAULT 'usuario')''')
print("✅ Tabla 'usuarios' creada")

# Crear tabla de salas
c.execute('''CREATE TABLE IF NOT EXISTS salas (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             nombre TEXT UNIQUE NOT NULL,
             descripcion TEXT)''')
print("✅ Tabla 'salas' creada")

# Crear tabla de reservas
c.execute('''CREATE TABLE IF NOT EXISTS reservas (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             sala_id INTEGER,
             usuario_id INTEGER,
             fecha TEXT,
             hora_inicio TEXT,
             hora_fin TEXT,
             recurrente TEXT DEFAULT 'no',
             estado TEXT DEFAULT 'activa',
             FOREIGN KEY(sala_id) REFERENCES salas(id),
             FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
print("✅ Tabla 'reservas' creada")

# Insertar salas
salas_default = [
    ('CC1', 'Sala de cómputo 1 - 20 equipos'),
    ('CC2', 'Sala de cómputo 2 - 25 equipos'),
    ('CC3', 'Sala de cómputo 3 - 30 equipos'),
    ('CC4', 'Sala de cómputo 4 - 15 equipos'),
    ('CC5', 'Sala de cómputo 5 - 10 equipos (SOLO ADMIN)')
]

for nombre, desc in salas_default:
    c.execute('INSERT INTO salas (nombre, descripcion) VALUES (?, ?)', (nombre, desc))
print("✅ 5 salas insertadas (CC1 - CC5)")

# Crear usuario admin
admin_pass = hashlib.sha256('admin123'.encode()).hexdigest()
c.execute('''INSERT INTO usuarios (nombre, email, password, rol) 
             VALUES ('Administrador', 'admin@salas.com', ?, 'admin')''', (admin_pass,))
print("✅ Usuario admin creado (admin@salas.com / admin123)")

# Guardar cambios
conn.commit()
print("✅ Cambios guardados")

# Verificar que todo está bien
print("\n📊 VERIFICACIÓN:")
salas = c.execute('SELECT * FROM salas').fetchall()
print(f"  - {len(salas)} salas en la base de datos")
for sala in salas:
    print(f"    * {sala[1]}: {sala[2]}")

usuarios = c.execute('SELECT id, nombre, email, rol FROM usuarios').fetchall()
print(f"  - {len(usuarios)} usuarios en la base de datos")
for user in usuarios:
    print(f"    * {user[1]} ({user[2]}) - Rol: {user[3]}")

conn.close()
print("\n✅ ¡BASE DE DATOS CREADA EXITOSAMENTE!")
print("🚀 Ahora puedes ejecutar: python app.py")