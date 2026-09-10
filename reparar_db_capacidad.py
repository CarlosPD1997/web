import sqlite3

print("🔧 Reparando base de datos - Agregando capacidad y comentarios")
print("=" * 60)

conn = sqlite3.connect('salas.db')
c = conn.cursor()

# 1. Agregar columna capacidad a la tabla salas
try:
    c.execute('ALTER TABLE salas ADD COLUMN capacidad INTEGER DEFAULT 25')
    print("✅ Columna 'capacidad' agregada a la tabla salas")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("ℹ️ La columna 'capacidad' ya existe")
    else:
        print(f"❌ Error: {e}")

# 2. Agregar columnas a la tabla reservas
try:
    c.execute('ALTER TABLE reservas ADD COLUMN num_alumnos INTEGER DEFAULT 0')
    print("✅ Columna 'num_alumnos' agregada a la tabla reservas")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("ℹ️ La columna 'num_alumnos' ya existe")
    else:
        print(f"❌ Error: {e}")

try:
    c.execute('ALTER TABLE reservas ADD COLUMN comentarios TEXT')
    print("✅ Columna 'comentarios' agregada a la tabla reservas")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("ℹ️ La columna 'comentarios' ya existe")
    else:
        print(f"❌ Error: {e}")

# 3. Actualizar capacidades de las salas
capacidades = [
    ('CC1', 25),
    ('CC2', 25),
    ('CC3', 64),
    ('CC4', 64),
    ('CC5', 10)
]

for nombre, capacidad in capacidades:
    c.execute('UPDATE salas SET capacidad = ? WHERE nombre = ?', (capacidad, nombre))
    print(f"✅ {nombre} → Capacidad: {capacidad} alumnos")

# 4. Verificar cambios
print("\n📊 VERIFICACIÓN:")
c.execute("PRAGMA table_info(salas)")
columnas_salas = c.fetchall()
print("Columnas en 'salas':")
for col in columnas_salas:
    print(f"  - {col[1]} ({col[2]})")

c.execute("PRAGMA table_info(reservas)")
columnas_reservas = c.fetchall()
print("\nColumnas en 'reservas':")
for col in columnas_reservas:
    print(f"  - {col[1]} ({col[2]})")

conn.commit()
conn.close()

print("\n" + "=" * 60)
print("✅ ¡Base de datos actualizada exitosamente!")
print("🚀 Ahora puedes ejecutar: python app.py")