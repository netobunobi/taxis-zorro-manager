import sqlite3
""""""
def insertar_flota_masiva(inicio, fin):
    try:
        # Conectamos a tu base de datos actual
        conexion = sqlite3.connect('taxis.db')
        cursor = conexion.cursor()
        
        print(f"🚀 Iniciando registro de taxis del {inicio} al {fin}...")
        
        for num in range(inicio, fin + 1):
            # Ignoramos el modelo y placas ya que no son campos requeridos en tu imagen
            # Insertamos con estado 'ACTIVO' y base_actual_id 12
            try:
                cursor.execute("""
                    INSERT INTO taxis (numero_economico, estado_sistema, base_actual_id)
                    VALUES (?, ?, ?)
                """, (str(num), 'ACTIVO', 12))
            except sqlite3.IntegrityError:
                # Si el número ya existe en la base de datos, lo salta para no detener el proceso
                continue
        
        conexion.commit()
        conexion.close()
        print(f"✅ ¡Se han agregado correctamente los taxis al catálogo!")
        
    except Exception as e:
        print(f"❌ Error durante la inserción: {e}")

if __name__ == "__main__":
    # Rango solicitado: del 35 al 100
    insertar_flota_masiva(35, 100)





    import sqlite3
import random
from datetime import datetime, timedelta

# CONFIGURACIÓN
DB_NAME = "taxis.db"
NUM_TAXIS = 10     # Crearemos taxis del 500 al 510
DIAS_ATRAS = 365   # Generar historia de un año

def generar_datos_prueba():
    print("🚀 Iniciando generación de datos de prueba...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. CREAR TAXIS DE PRUEBA (Si no existen)
    taxis_ids = []
    print("🚕 Registrando unidades de prueba (500-510)...")
    for i in range(NUM_TAXIS):
        num_eco = str(500 + i)
        # Verificamos si existe
        cursor.execute("SELECT id FROM taxis WHERE numero_economico = ?", (num_eco,))
        res = cursor.fetchone()
        
        if res:
            taxis_ids.append(res[0])
        else:
            # Insertamos nuevo (Base 12 = Fuera de servicio por defecto)
            cursor.execute("INSERT INTO taxis (numero_economico, estado_sistema, base_actual_id) VALUES (?, ?, ?)", 
                           (num_eco, 'ACTIVO', 12))
            taxis_ids.append(cursor.lastrowid)

    # 2. GENERAR HISTORIAL (VIAJES Y TURNOS)
    print(f"📅 Generando historial para los últimos {DIAS_ATRAS} días...")
    
    total_viajes = 0
    fecha_actual = datetime.now()

    # Recorremos día por día desde el pasado hasta hoy
    for d in range(DIAS_ATRAS, -1, -1):
        fecha_dia = fecha_actual - timedelta(days=d)
        fecha_str = fecha_dia.strftime("%Y-%m-%d")
        
        # Probabilidad de que un taxi trabaje ese día (70%)
        taxis_que_trabajan = [t for t in taxis_ids if random.random() > 0.3]
        
        for taxi_id in taxis_que_trabajan:
            # --- A. SIMULAR TURNO DE TRABAJO (Para gráfica de Horas) ---
            # El turno empieza entre las 6am y 10am
            hora_inicio = random.randint(6, 10)
            inicio_turno = fecha_dia.replace(hour=hora_inicio, minute=0, second=0)
            
            # El turno dura entre 6 y 12 horas
            horas_trabajadas = random.randint(6, 12)
            fin_turno = inicio_turno + timedelta(hours=horas_trabajadas)
            
            cursor.execute("""
                INSERT INTO turnos_trabajo (taxi_id, fecha_inicio, fecha_fin)
                VALUES (?, ?, ?)
            """, (taxi_id, inicio_turno, fin_turno))
            
            # --- B. SIMULAR VIAJES DENTRO DEL TURNO (Para gráficas Dinero y Viajes) ---
            # Generamos entre 5 y 15 viajes por día
            num_viajes = random.randint(5, 15)
            
            tiempo_actual = inicio_turno
            
            for _ in range(num_viajes):
                # El viaje ocurre unos minutos después del anterior
                tiempo_actual += timedelta(minutes=random.randint(15, 60))
                
                if tiempo_actual > fin_turno:
                    break # Se acabó el turno
                
                # Datos del viaje
                tipo_servicio = random.choice([1, 2, 3, 4]) # Base, Teléfono, etc.
                base_salida = random.randint(1, 11) if tipo_servicio == 1 else None
                destino = random.choice(["Centro", "Hospital", "Escuela", "Terminal", "Plaza", "Colonia Sur"])
                precio = round(random.uniform(35.0, 150.0), 2) # Costo entre 35 y 150
                
                cursor.execute("""
                    INSERT INTO viajes (taxi_id, tipo_servicio_id, base_salida_id, destino, precio, fecha_hora_inicio)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (taxi_id, tipo_servicio, base_salida, destino, precio, tiempo_actual))
                
                total_viajes += 1

    conn.commit()
    conn.close()
    print(f"✅ ¡LISTO! Se generaron aproximadamente {total_viajes} viajes históricos.")
    print("👉 Abre tu sistema, ve a 'Gestión Taxis', busca el taxi '500' y prueba los filtros HOY/MES/ANIO.")

if __name__ == "__main__":
    generar_datos_prueba()