import sqlite3

print("🔧 Reparando base de datos...")

conn = sqlite3.connect('salas.db')
c = conn.cursor()

# 1. Agregar columna telefono si no existe
try:
    c.execute('ALTER TABLE usuarios ADD COLUMN telefono TEXT')
    print("✅ Columna 'telefono' agregada a la tabla usuarios")
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print("ℹ️ La columna 'telefono' ya existe")
    else:
        print(f"❌ Error: {e}")

# 2. Verificar que la columna existe
c.execute("PRAGMA table_info(usuarios)")
columnas = c.fetchall()
print("\n📊 Columnas en la tabla 'usuarios':")
for col in columnas:
    print(f"  - {col[1]} ({col[2]})")

conn.commit()
conn.close()

print("\n✅ ¡Base de datos reparada exitosamente!")
print("🚀 Ahora puedes ejecutar: python app.py")