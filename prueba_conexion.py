from gestor_bd import GestorBaseDatos

# 1. Iniciamos el gestor
gestor = GestorBaseDatos()

# 2. Pedimos los taxis
print("--- PROBANDO CONSULTA DE TAXIS ---")
lista_taxis = gestor.obtener_taxis_activos()

if lista_taxis:
    for taxi in lista_taxis:
        print(f"Taxi ID: {taxi['id']} | Unidad: {taxi['numero_economico']} | Estado: {taxi['estado_texto']}")
else:
    print("No hay taxis activos (¿Ya corriste crear_bd.py?)")

# 3. Pedimos las bases
print("\n--- PROBANDO CONSULTA DE BASES ---")
lista_bases = gestor.obtener_bases()

for base in lista_bases:
    print(f"Base ID: {base['id']} | Nombre: {base['nombre_base']}")