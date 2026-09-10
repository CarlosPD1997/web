import sqlite3

print("=" * 70)
print("🔍 DIAGNÓSTICO DE CLASES FIJAS")
print("=" * 70)

conn = sqlite3.connect('salas.db')
c = conn.cursor()

# 1. Ver todas las clases
print("\n📚 TODAS LAS CLASES EN LA BD:")
clases = c.execute('''SELECT cf.id, s.nombre, cf.materia, cf.profesor, cf.dia_semana, 
                             cf.hora_inicio, cf.hora_fin, cf.activo
                      FROM clases_fijas cf
                      JOIN salas s ON cf.sala_id = s.id''').fetchall()

if clases:
    print(f"✅ {len(clases)} clases encontradas:\n")
    for c in clases:
        estado = "✅ Activa" if c[7] == 1 else "❌ Inactiva"
        print(f"  ID:{c[0]} | Sala:{c[1]} | {c[2]} | {c[3]} | {c[4]} | {c[5]}-{c[6]} | {estado}")
else:
    print("❌ No hay clases en la base de datos")

# 2. Verificar qué días están registrados
print("\n📅 DÍAS REGISTRADOS:")
dias = c.execute('SELECT DISTINCT dia_semana FROM clases_fijas').fetchall()
for d in dias:
    print(f"  - {d[0]}")

# 3. Simular una consulta para CC4 en Lunes
print("\n🧪 PRUEBA: Clases para CC4 en Lunes")
prueba = c.execute('''SELECT materia, profesor, hora_inicio, hora_fin
                      FROM clases_fijas
                      WHERE sala_id = 4 AND dia_semana = 'Lunes' AND activo = 1''').fetchall()

if prueba:
    print(f"✅ {len(prueba)} clases encontradas:")
    for p in prueba:
        print(f"  - {p[0]} | {p[1]} | {p[2]}-{p[3]}")
else:
    print("❌ No hay clases para CC4 en Lunes")
    print("   Verifica el ID de la sala CC4:")

# 4. Ver IDs de salas
print("\n🏫 SALAS EN EL SISTEMA:")
salas = c.execute('SELECT id, nombre FROM salas ORDER BY id').fetchall()
for s in salas:
    print(f"  ID:{s[0]} | {s[1]}")

conn.close()
print("\n" + "=" * 70)
print("🔧 Si ves clases pero no aparecen en el calendario, el problema es el filtro de día.")
print("   Las clases deben tener el día escrito exactamente como: 'Lunes', 'Martes', etc.")
print("=" * 70)