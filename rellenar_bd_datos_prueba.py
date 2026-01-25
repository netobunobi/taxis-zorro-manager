import sqlite3
import random
from datetime import datetime, timedelta

def popular_base_datos_completa():
    db_path = "taxis.db"
    print(f"🔌 Conectando a {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. VERIFICAR FLOTA (No creamos nada raro, solo aseguramos que existan los normales)
    cursor.execute("SELECT id, numero_economico FROM taxis")
    flota = cursor.fetchall()
    
    if not flota:
        print("⚠️ No hay taxis. Creando flota estándar (35-100)...")
        for n in range(35, 101):
            cursor.execute("INSERT INTO taxis (numero_economico, base_actual_id, estado_sistema) VALUES (?, 12, 'ACTIVO')", (str(n),))
        conn.commit()
        cursor.execute("SELECT id, numero_economico FROM taxis")
        flota = cursor.fetchall()
    
    taxi_ids = [t[0] for t in flota]
    print(f"✅ Flota detectada: {len(taxi_ids)} unidades.")

    # 2. GENERADOR DE VIAJES (HISTORIAL)
    print("🚖 Generando 500 viajes históricos...")
    
    destinos_comunes = [
        "Centro", "CAPU", "Plaza Dorada", "Angelópolis", "Cholula", 
        "Amozoc Centro", "Tepeaca", "Acajete", "Hospital General", 
        "Estadio", "C.U.", "Periplaza", "Héroes", "Amalucan"
    ]
    
    # Generamos viajes distribuidos en los últimos 60 días
    for _ in range(500):
        taxi_id = random.choice(taxi_ids)
        tipo_servicio = random.choice([1, 1, 1, 2, 2, 3, 4]) # Más probabilidad de Base(1)
        base_salida = random.randint(1, 11)
        destino = random.choice(destinos_comunes)
        
        # Precio aleatorio pero realista ($40 - $350)
        precio = round(random.uniform(40.0, 350.0) / 5) * 5 # Redondear a múltiplos de 5
        
        # Fecha aleatoria
        dias_atras = random.randint(0, 60)
        horas = random.randint(6, 23) # Horario laboral
        minutos = random.randint(0, 59)
        
        inicio = datetime.now() - timedelta(days=dias_atras, hours=horas, minutes=minutos)
        fin = inicio + timedelta(minutes=random.randint(20, 90))
        
        cursor.execute("""
            INSERT INTO viajes (taxi_id, tipo_servicio_id, base_salida_id, destino, precio, fecha_hora_inicio, fecha_hora_fin) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (taxi_id, tipo_servicio, base_salida, destino, precio, 
              inicio.strftime("%Y-%m-%d %H:%M:%S"), 
              fin.strftime("%Y-%m-%d %H:%M:%S")))

    # 3. GENERADOR DE INCIDENCIAS (REPORTES)
    print("👮 Generando 40 reportes administrativos...")
    
    tipos = ["Multa Horas", "Multa Horas", "Ausencia", "Ausencia", "Falta Banderolas", "Deuda"]
    
    for _ in range(40):
        taxi_id = random.choice(taxi_ids)
        tipo = random.choice(tipos)
        
        monto = 0
        resuelto = 'INFORMATIVO'
        
        if tipo == "Multa Horas":
            monto = random.choice([50, 100])
            resuelto = 'PENDIENTE'
        elif tipo == "Deuda":
            monto = random.choice([200, 500, 1000])
            resuelto = 'PENDIENTE'
            
        fecha_inc = (datetime.now() - timedelta(days=random.randint(0, 45))).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            INSERT INTO incidencias (taxi_id, tipo, descripcion, monto, fecha_registro, resuelto, operador_id) 
            VALUES (?, ?, ?, ?, ?, ?, 'SISTEMA PRUEBAS')
        """, (taxi_id, tipo, "Reporte generado automáticamente", monto, fecha_inc, resuelto))

    # 4. CONFIGURACIÓN VISUAL (SEMÁFORO EN VIVO)
    print("🎨 Pintando tablero (Semáforo)...")
    
    # Función para "trucar" el reloj
    def mover_taxi(num, base_id, minutos_hace):
        t_mov = (datetime.now() - timedelta(minutes=minutos_hace)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE taxis SET base_actual_id=?, fecha_movimiento=? WHERE numero_economico=?", 
                       (base_id, t_mov, str(num)))

    # --- ESCENARIOS VISUALES ---
    # Taxis en LOCAL (Base 93)
    mover_taxi(35, 93, 10)  # Amarillo (10 min) - OK
    mover_taxi(36, 93, 35)  # Naranja (35 min) - ALERTA
    mover_taxi(37, 93, 55)  # Rojo (55 min) - PELIGRO

    # Taxis en FORÁNEO (Base 92)
    mover_taxi(38, 92, 100) # Naranja (1h 40m)
    mover_taxi(39, 92, 130) # Rojo (2h 10m)

    # Taxis en DESCANSO (Base 91)
    mover_taxi(40, 91, 5)   # Morado (5 min) - Comiendo a gusto
    mover_taxi(41, 91, 70)  # Naranja (70 min) - Se está tardando
    
    # Taxis en TALLER (Base 90)
    mover_taxi(42, 90, 500) # Café

    # Taxis TRABAJANDO NORMAL (Varios en Local)
    for t in range(43, 50):
        mover_taxi(t, 93, random.randint(1, 20)) # Todos ok

    conn.commit()
    conn.close()
    print("✨ ¡LISTO! Base de datos inyectada con éxito.")

if __name__ == "__main__":
    popular_base_datos_completa()