import sqlite3
import hashlib

print("🔧 REPARANDO BASE DE DATOS COMPLETAMENTE")
print("=" * 60)

conn = sqlite3.connect('salas.db')
c = conn.cursor()

# 1. Verificar y agregar columna capacidad a salas
try:
    c.execute('ALTER TABLE salas ADD COLUMN capacidad INTEGER DEFAULT 25')
    print("✅ Columna 'capacidad' agregada a tabla salas")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("ℹ️ La columna 'capacidad' ya existe en salas")
    else:
        print(f"❌ Error: {e}")

# 2. Verificar y agregar columnas a reservas
try:
    c.execute('ALTER TABLE reservas ADD COLUMN num_alumnos INTEGER DEFAULT 0')
    print("✅ Columna 'num_alumnos' agregada a tabla reservas")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("ℹ️ La columna 'num_alumnos' ya existe en reservas")
    else:
        print(f"❌ Error: {e}")

try:
    c.execute('ALTER TABLE reservas ADD COLUMN comentarios TEXT')
    print("✅ Columna 'comentarios' agregada a tabla reservas")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("ℹ️ La columna 'comentarios' ya existe en reservas")
    else:
        print(f"❌ Error: {e}")

try:
    c.execute('ALTER TABLE reservas ADD COLUMN mensaje_rechazo TEXT')
    print("✅ Columna 'mensaje_rechazo' agregada a tabla reservas")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("ℹ️ La columna 'mensaje_rechazo' ya existe en reservas")
    else:
        print(f"❌ Error: {e}")

# 3. Actualizar capacidades de las salas existentes
capacidades = [
    ('CC1', 25),
    ('CC2', 25),
    ('CC3', 64),
    ('CC4', 64),
    ('CC5', 10)
]

for nombre, cap in capacidades:
    try:
        c.execute('UPDATE salas SET capacidad = ? WHERE nombre = ?', (cap, nombre))
        print(f"✅ {nombre} → Capacidad: {cap} alumnos")
    except sqlite3.OperationalError as e:
        print(f"❌ Error al actualizar {nombre}: {e}")

# 4. Verificar que todo está bien
print("\n📊 VERIFICACIÓN FINAL:")

# Verificar columnas en salas
c.execute("PRAGMA table_info(salas)")
columnas_salas = c.fetchall()
print("Columnas en 'salas':")
for col in columnas_salas:
    print(f"  - {col[1]} ({col[2]})")

# Verificar columnas en reservas
c.execute("PRAGMA table_info(reservas)")
columnas_reservas = c.fetchall()
print("\nColumnas en 'reservas':")
for col in columnas_reservas:
    print(f"  - {col[1]} ({col[2]})")

# Verificar salas con capacidad
c.execute('SELECT nombre, capacidad FROM salas')
salas = c.fetchall()
print("\n📋 SALAS CON CAPACIDAD:")
for s in salas:
    print(f"  {s[0]} → {s[1]} alumnos")

conn.commit()
conn.close()

print("\n" + "=" * 60)
print("✅ ¡BASE DE DATOS REPARADA EXITOSAMENTE!")
print("🚀 Ahora puedes ejecutar: python app.py")