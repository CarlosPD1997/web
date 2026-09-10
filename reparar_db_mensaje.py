import sqlite3

print("🔧 Reparando base de datos - Agregando columna mensaje_rechazo")
print("=" * 60)

conn = sqlite3.connect('salas.db')
c = conn.cursor()

# 1. Verificar si la columna ya existe
c.execute("PRAGMA table_info(reservas)")
columnas = c.fetchall()
nombres_columnas = [col[1] for col in columnas]

print("\n📊 Columnas actuales en 'reservas':")
for col in columnas:
    print(f"  - {col[1]} ({col[2]})")

# 2. Agregar columna mensaje_rechazo si no existe
if 'mensaje_rechazo' not in nombres_columnas:
    try:
        c.execute('ALTER TABLE reservas ADD COLUMN mensaje_rechazo TEXT')
        print("\n✅ Columna 'mensaje_rechazo' agregada correctamente")
    except sqlite3.OperationalError as e:
        print(f"\n❌ Error: {e}")
else:
    print("\nℹ️ La columna 'mensaje_rechazo' ya existe")

# 3. Verificar que la columna se agregó
c.execute("PRAGMA table_info(reservas)")
columnas_final = c.fetchall()

print("\n📊 Columnas finales en 'reservas':")
for col in columnas_final:
    print(f"  - {col[1]} ({col[2]})")

conn.commit()
conn.close()

print("\n" + "=" * 60)
print("✅ ¡Base de datos reparada exitosamente!")
print("🚀 Ahora puedes ejecutar: python app.py")