import sqlite3
import random
from datetime import datetime, timedelta

def rellenar_viajes_prueba():
    # Conectamos a tu base de datos real
    conn = sqlite3.connect('taxis.db')
    cursor = conn.cursor()

    print("--- Generando historial de viajes 2024-2025 ---")

    # 1. Obtener los IDs de los taxis que ya tienes (para no inventar taxis nuevos)
    cursor.execute("SELECT id, numero_economico FROM taxis")
    lista_taxis = cursor.fetchall()
    
    if not lista_taxis:
        print("❌ Error: No hay taxis en la tabla 'taxis'. Registra uno primero.")
        return

    # 2. Configuración de datos aleatorios
    destinos = ["Centro", "CU2 BUAP", "Plaza Dorada", "Capu", "Cholula", "Hospital", "Base El Zorro"]
    conceptos = ["Local", "Especial", "Mandado"]
    
    # Rango: Desde Enero 2024 hasta hoy
    fecha_inicio = datetime(2024, 1, 1)
    fecha_hoy = datetime.now()
    dias_totales = (fecha_hoy - fecha_inicio).days

    total_viajes = 0

    for d in range(dias_totales):
        fecha_actual = fecha_inicio + timedelta(days=d)
        
        # Generar entre 5 y 15 viajes por día para que las gráficas se vean llenas
        for _ in range(random.randint(5, 15)):
            t_id, num_econ = random.choice(lista_taxis)
            
            # Datos del viaje
            hora = random.randint(6, 22) # Taxis activos de 6am a 10pm
            minuto = random.randint(0, 59)
            f_hora = fecha_actual.replace(hour=hora, minute=minuto)
            fecha_str = f_hora.strftime('%Y-%m-%d %H:%M:%S')
            
            precio = random.choice([45, 50, 65, 80, 100, 150, 200])
            # Usamos 'ganancia' porque es el nombre que definimos para los reportes
            ganancia = precio 
            
            try:
                # Ajustado a tu estructura de Taxis El Zorro Manager
                cursor.execute("""
                    INSERT INTO viajes (taxi_id, fecha_hora_inicio, concepto, origen, destino, precio, ganancia)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (t_id, fecha_str, random.choice(conceptos), "Base", random.choice(destinos), precio, ganancia))
                total_viajes += 1
            except sqlite3.OperationalError as e:
                # Si tu tabla no tiene la columna 'ganancia' aún, intentamos solo con precio
                cursor.execute("""
                    INSERT INTO viajes (taxi_id, fecha_hora_inicio, concepto, origen, destino, precio)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (t_id, fecha_str, random.choice(conceptos), "Base", random.choice(destinos), precio))
                total_viajes += 1

    conn.commit()
    conn.close()
    print(f"✅ Éxito: Se crearon {total_viajes} viajes históricos.")

if __name__ == "__main__":
    rellenar_viajes_prueba()