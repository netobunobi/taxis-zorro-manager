import sqlite3
import os
import ctypes
from datetime import datetime, timedelta

class GestorBaseDatos:
    def __init__(self, nombre_base_datos="taxis.db"):
        self.nombre_base_datos = nombre_base_datos
        
        # INICIO AUTOMÁTICO:
        # Si no existe el archivo, se crea la estructura completa V3
        if not os.path.exists(self.nombre_base_datos):
            print("⚠️ Base de datos no encontrada. Creando sistema nuevo...")
            self.crear_nueva_bd_v3()
        else:
            self._verificar_estructura()

    def _conectar(self):
        conn = sqlite3.connect(self.nombre_base_datos)
        conn.row_factory = sqlite3.Row
        return conn, conn.cursor()

    def crear_nueva_bd_v3(self):
        """ CREACIÓN LIMPIA CON NOMBRES CORRECTOS """
        try:
            conn = sqlite3.connect(self.nombre_base_datos)
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")

            # 1. CATÁLOGOS
            cursor.execute("CREATE TABLE IF NOT EXISTS cat_tipos_servicio (id INTEGER PRIMARY KEY AUTOINCREMENT, descripcion TEXT UNIQUE)")
            cursor.execute("CREATE TABLE IF NOT EXISTS cat_bases (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_base TEXT UNIQUE)")
            
            # 2. TAXIS (Con fecha_movimiento para la alerta naranja)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS taxis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    numero_economico TEXT NOT NULL UNIQUE, 
                    estado_sistema TEXT DEFAULT 'ACTIVO', 
                    base_actual_id INTEGER DEFAULT 12,
                    fecha_movimiento TEXT,
                    FOREIGN KEY(base_actual_id) REFERENCES cat_bases(id)
                )
            """)

            # 3. TURNOS (Para cálculo real de horas trabajadas)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS turnos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    taxi_id INTEGER,
                    fecha_inicio TEXT,
                    fecha_fin TEXT
                )
            """)

            # 4. VIAJES
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS viajes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    taxi_id INTEGER, 
                    tipo_servicio_id INTEGER, 
                    base_salida_id INTEGER, 
                    destino TEXT, 
                    precio REAL DEFAULT 0.0, 
                    fecha_hora_inicio TEXT, 
                    fecha_hora_fin TEXT
                )
            """)

            # 5. INCIDENCIAS
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    taxi_id INTEGER,
                    tipo TEXT,
                    descripcion TEXT,
                    monto REAL DEFAULT 0.0,
                    fecha_registro TEXT,
                    resuelto TEXT DEFAULT 'PENDIENTE',
                    operador_id TEXT DEFAULT 'SISTEMA'
                )
            """)

            # DATOS INICIALES (BASES Y SERVICIOS)
            bases_iniciales = [
                (1,'Cessa'), (2,'Licuor'), (3,'Santiaguito'), (4,'Aurrera'), (5,'Mercado'),
                (6,'Caros'), (7,'Survi'), (8,'Capulin'), (9,'Zocalo'), (10,'16 de Sept'),
                (11,'Parada'), (12,'Fuera de Servicio'), (13,'En Viaje'),
                (90, 'Taller 🛠️'), (91, 'Permiso/Descanso 📅'), (92, 'Foráneo'), (93, 'Local')
            ]
            cursor.executemany("INSERT OR IGNORE INTO cat_bases (id, nombre_base) VALUES (?,?)", bases_iniciales)
            
            servicios_iniciales = [(1,'Base'), (2,'Tel Base'), (3,'Tel Unidad'), (4,'Aéreo')]
            cursor.executemany("INSERT OR IGNORE INTO cat_tipos_servicio (id, descripcion) VALUES (?,?)", servicios_iniciales)

            # CREAR FLOTA INICIAL (35 al 100)
            for numero in range(35, 101):
                cursor.execute("INSERT OR IGNORE INTO taxis (numero_economico, base_actual_id) VALUES (?, 12)", (str(numero),))

            conn.commit()
            conn.close()
            
            # Ocultar archivo en Windows (Opcional)
            try: ctypes.windll.kernel32.SetFileAttributesW(self.nombre_base_datos, 0x80)
            except: pass
            
            print("✅ Base de Datos creada correctamente.")
            
        except Exception as error: 
            print(f"Error fatal creando BD: {error}")

    def _verificar_estructura(self):
        """ Asegura compatibilidad si la BD ya existe """
        try:
            conn, cursor = self._conectar()
            
            # Verificar tabla turnos
            cursor.execute("CREATE TABLE IF NOT EXISTS turnos (id INTEGER PRIMARY KEY AUTOINCREMENT, taxi_id INTEGER, fecha_inicio TEXT, fecha_fin TEXT)")
            
            # Verificar columnas nuevas
            cursor.execute("PRAGMA table_info(taxis)")
            columnas_taxis = [row['name'] for row in cursor.fetchall()]
            if 'fecha_movimiento' not in columnas_taxis: 
                cursor.execute("ALTER TABLE taxis ADD COLUMN fecha_movimiento TEXT")

            conn.commit()
            conn.close()
        except: pass 

    # ==========================================
    # LÓGICA DE TURNOS (RELOJ CHECADOR)
    # ==========================================
    def abrir_turno(self, taxi_id):
        conn, cursor = self._conectar()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Cerrar turno previo si quedó colgado
        cursor.execute("UPDATE turnos SET fecha_fin = ? WHERE taxi_id = ? AND fecha_fin IS NULL", (ahora, taxi_id))
        # Abrir nuevo
        cursor.execute("INSERT INTO turnos (taxi_id, fecha_inicio) VALUES (?, ?)", (taxi_id, ahora))
        conn.commit()
        conn.close()

    def cerrar_turno(self, taxi_id):
        conn, cursor = self._conectar()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE turnos SET fecha_fin = ? WHERE taxi_id = ? AND fecha_fin IS NULL", (ahora, taxi_id))
        conn.commit()
        conn.close()

    def actualizar_taxi_base(self, taxi_id, nueva_base_id):
        conn, cursor = self._conectar()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Actualiza ubicación y hora (para la alerta naranja)
        cursor.execute("UPDATE taxis SET base_actual_id = ?, fecha_movimiento = ? WHERE id = ?", (nueva_base_id, ahora, taxi_id))
        conn.commit()
        conn.close()

    # ==========================================
    # ESTADÍSTICAS Y REPORTES (NOMBRES COMPLETOS)
    # ==========================================

    def obtener_estadisticas_unidad(self, taxi_id, periodo, fecha_ref=None):
        conn, cursor = self._conectar()
        if not fecha_ref: fecha_ref = datetime.now().strftime("%Y-%m-%d")
        
        # 1. Ganancias y Viajes
        filtro_viajes = ""
        if periodo in ["DIA", "HOY"]: filtro_viajes = f"AND fecha_hora_inicio LIKE '{fecha_ref}%'"
        elif periodo == "MES": filtro_viajes = f"AND fecha_hora_inicio LIKE '{fecha_ref[:7]}%'"
        elif periodo == "AÑO": filtro_viajes = f"AND fecha_hora_inicio LIKE '{fecha_ref[:4]}%'"

        cursor.execute(f"SELECT SUM(precio), COUNT(*) FROM viajes WHERE taxi_id = ? {filtro_viajes}", (taxi_id,))
        resultado = cursor.fetchone()
        ganancia = resultado[0] if resultado[0] else 0.0
        viajes = resultado[1] if resultado[1] else 0

        # 2. Horas (Calculadas sumando turnos reales)
        segundos_totales = 0
        filtro_turnos = ""
        
        # Filtro para traer los turnos que iniciaron en ese periodo
        if periodo in ["DIA", "HOY"]: filtro_turnos = f"AND fecha_inicio LIKE '{fecha_ref}%'"
        elif periodo == "MES": filtro_turnos = f"AND fecha_inicio LIKE '{fecha_ref[:7]}%'"
        
        cursor.execute(f"SELECT fecha_inicio, fecha_fin FROM turnos WHERE taxi_id = ? {filtro_turnos}", (taxi_id,))
        lista_turnos = cursor.fetchall()
        
        ahora_dt = datetime.now()
        
        for turno in lista_turnos:
            try:
                inicio = datetime.strptime(turno['fecha_inicio'], "%Y-%m-%d %H:%M:%S")
                if turno['fecha_fin']:
                    fin = datetime.strptime(turno['fecha_fin'], "%Y-%m-%d %H:%M:%S")
                    segundos_totales += (fin - inicio).total_seconds()
                elif periodo == "HOY" or fecha_ref == ahora_dt.strftime("%Y-%m-%d"):
                    # Si el turno sigue abierto hoy, sumar tiempo hasta ahorita
                    segundos_totales += (ahora_dt - inicio).total_seconds()
            except: pass
            
        horas_reales = segundos_totales / 3600.0
        conn.close()
        
        return {"ganancia": ganancia, "viajes": viajes, "horas": horas_reales}

    def obtener_datos_tres_graficas(self, taxi_id, periodo, fecha_ref=None):
        """ Genera datos para las gráficas. Acepta 'fecha_ref' explícitamente. """
        conn, cursor = self._conectar()
        if not fecha_ref: fecha_ref = datetime.now().strftime("%Y-%m-%d")
        
        etiquetas, dinero, viajes, horas = [], [], [], []

        try:
            # MODO DÍA (Por Horas)
            if periodo in ["DIA", "HOY"]:
                datos_temp = {f"{h:02d}": {"dinero": 0.0, "viajes": 0} for h in range(24)}
                cursor.execute("""
                    SELECT strftime('%H', fecha_hora_inicio) as hora, SUM(precio), COUNT(*)
                    FROM viajes WHERE taxi_id = ? AND fecha_hora_inicio LIKE ? GROUP BY hora
                """, (taxi_id, f"{fecha_ref}%"))
                
                for fila in cursor.fetchall():
                    h = fila['hora']
                    if h in datos_temp:
                        datos_temp[h]["dinero"] = fila[1]
                        datos_temp[h]["viajes"] = fila[2]
                
                llaves = sorted(datos_temp.keys())
                etiquetas = [f"{h}h" for h in llaves]
                dinero = [datos_temp[h]["dinero"] for h in llaves]
                viajes = [datos_temp[h]["viajes"] for h in llaves]
                horas = [v * 0.5 for v in viajes] # Estimación visual

            # MODO MES (Por Días)
            elif periodo == "MES":
                mes_str = fecha_ref[:7]
                datos_temp = {f"{d:02d}": {"dinero": 0.0, "viajes": 0} for d in range(1, 32)}
                cursor.execute("""
                    SELECT strftime('%d', fecha_hora_inicio) as dia, SUM(precio), COUNT(*)
                    FROM viajes WHERE taxi_id = ? AND fecha_hora_inicio LIKE ? GROUP BY dia
                """, (taxi_id, f"{mes_str}%"))
                
                dias_con_datos = []
                for fila in cursor.fetchall():
                    d = fila['dia']
                    if d in datos_temp:
                        datos_temp[d]["dinero"] = fila[1]
                        datos_temp[d]["viajes"] = fila[2]
                        dias_con_datos.append(d)
                
                limite = int(max(dias_con_datos)) if dias_con_datos else 31
                rango_dias = [f"{d:02d}" for d in range(1, limite + 1)]
                
                etiquetas = rango_dias
                dinero = [datos_temp[d]["dinero"] for d in rango_dias]
                viajes = [datos_temp[d]["viajes"] for d in rango_dias]
                horas = [v * 0.8 for v in viajes] # Estimación visual

        except Exception as e: print(f"Error gráficas: {e}")
        conn.close()
        return {"etiquetas": etiquetas, "dinero": dinero, "viajes": viajes, "horas": horas}

    def obtener_viajes_por_unidad_y_periodo(self, taxi_id, periodo, fecha_ref=None):
        """ Para el reporte PDF. Acepta 'fecha_ref' explícitamente. """
        conn, cursor = self._conectar()
        filtro = ""
        if periodo in ["DIA", "HOY"]: filtro = f" AND v.fecha_hora_inicio LIKE '{fecha_ref}%'"
        
        cursor.execute(f"""
            SELECT v.fecha_hora_inicio as fecha, v.destino, v.precio, b.nombre_base 
            FROM viajes v LEFT JOIN cat_bases b ON v.base_salida_id=b.id 
            WHERE v.taxi_id=? {filtro} ORDER BY v.fecha_hora_inicio ASC
        """, (taxi_id,))
        
        datos = []
        for fila in cursor.fetchall():
            datos.append({
                "fecha": fila['fecha'], 
                "origen": fila['nombre_base'] or "Servicio", 
                "destino": fila['destino'], 
                "precio": fila['precio']
            })
        conn.close()
        return datos

    def obtener_ranking_bases(self, periodo):
        """ Para la gráfica de pastel de Bases """
        conn, cursor = self._conectar()
        fecha_ref = datetime.now().strftime("%Y-%m-%d")
        filtro = ""
        if periodo == "DIA": filtro = f" AND v.fecha_hora_inicio LIKE '{fecha_ref}%'"
        elif periodo == "MES": filtro = f" AND v.fecha_hora_inicio LIKE '{fecha_ref[:7]}%'"
        elif periodo == "AÑO": filtro = f" AND v.fecha_hora_inicio LIKE '{fecha_ref[:4]}%'"

        cursor.execute(f"""
            SELECT b.nombre_base, COUNT(*) as conteo
            FROM viajes v JOIN cat_bases b ON v.base_salida_id = b.id
            WHERE 1=1 {filtro} GROUP BY b.nombre_base ORDER BY conteo DESC LIMIT 5
        """)
        filas = cursor.fetchall()
        conn.close()
        
        if not filas: return ["Sin Datos"], [0]
        return [f['nombre_base'] for f in filas], [f['conteo'] for f in filas]

    # REEMPLAZAR EN gestor_db.py
    
    def obtener_datos_reporte_global(self, periodo, fecha_str):
        """
        Retorna un paquete completo de estadísticas para el reporte profesional.
        """
        conn, cursor = self._conectar()
        
        filtro = ""
        if periodo == "DIA": filtro = f" AND fecha_hora_inicio LIKE '{fecha_str}%'"
        elif periodo == "MES": filtro = f" AND fecha_hora_inicio LIKE '{fecha_str[:7]}%'"
        elif periodo == "AÑO": filtro = f" AND fecha_hora_inicio LIKE '{fecha_str[:4]}%'"
        
        # 1. TOTALES GENERALES (Dinero y Viajes)
        cursor.execute(f"SELECT SUM(precio), COUNT(*) FROM viajes WHERE 1=1 {filtro}")
        res = cursor.fetchone()
        ganancia_total = res[0] or 0.0
        viajes_totales = res[1] or 0
        
        # 2. DESGLOSE POR TIPO DE SERVICIO (Para ver qué se vende más)
        # 1=Base, 2=Tel Base, 3=Tel Unidad, 4=Aéreo
        cursor.execute(f"""
            SELECT tipo_servicio_id, COUNT(*) 
            FROM viajes WHERE 1=1 {filtro} GROUP BY tipo_servicio_id
        """)
        raw_servicios = cursor.fetchall()
        servicios = {1:0, 2:0, 3:0, 4:0}
        for s_id, count in raw_servicios:
            servicios[s_id] = count

        # 3. INCIDENCIAS (Multas y Ausencias del periodo)
        # Filtramos por fecha de registro de la incidencia
        filtro_inc = filtro.replace("fecha_hora_inicio", "fecha_registro")
        
        cursor.execute(f"""
            SELECT tipo, COUNT(*), SUM(monto) 
            FROM incidencias 
            WHERE 1=1 {filtro_inc}
            GROUP BY tipo
        """)
        raw_inc = cursor.fetchall()
        
        # Procesamos incidencias
        incidencias = {
            "total_count": 0,
            "total_multas_dinero": 0.0,
            "desglose": [] # Lista de tuplas (Tipo, Cantidad, Dinero)
        }
        for tipo, cant, lana in raw_inc:
            incidencias["total_count"] += cant
            incidencias["total_multas_dinero"] += (lana or 0.0)
            incidencias["desglose"].append((tipo, cant, lana or 0.0))
            
        conn.close()
        
        return {
            "totales": {
                "ganancia": ganancia_total,
                "viajes": viajes_totales,
                "ticket_promedio": (ganancia_total / viajes_totales) if viajes_totales > 0 else 0.0
            },
            "servicios": servicios,
            "incidencias": incidencias
        }
    
    
    def auditoria_inteligente(self, fecha_analisis):
        """
        AUDITORÍA V9 (Lógica Corregida con FECHA DE INICIO):
        """
        # --- NUEVO: CANDADO DE FECHA DE INICIO ---
        # Si la fecha que intentan revisar es ANTES del 28 de Enero de 2026, no hacemos nada.
        if fecha_analisis < "2026-01-28":
            print(f"--- Auditoría omitida por fecha de inicio ({fecha_analisis}) ---")
            return [] # Retornamos lista vacía: Nadie debe nada, nadie faltó.

        conn, cursor = self._conectar()
        taxis = self.obtener_toda_la_flota()
        candidatos = []
        
        print(f"--- INICIANDO AUDITORÍA V9 ({fecha_analisis}) ---")
        
        # ... (El resto del código sigue igual) ...

        # Objeto fecha para revisar el pasado
        try:
            fecha_obj = datetime.strptime(fecha_analisis, "%Y-%m-%d")
        except:
            fecha_obj = datetime.now()

        for taxi in taxis:
            num = taxi['numero_economico']
            
            # Filtros básicos
            if taxi['estado_sistema'] != 'ACTIVO': continue
            if taxi['base_actual_id'] == 90: continue # Taller perdonado

            # Calcular horas trabajadas
            stats = self.obtener_estadisticas_unidad(taxi['id'], "DIA", fecha_analisis)
            horas = stats['horas']

            # --- ESCENARIO 1: AUSENCIA TOTAL (0 Horas) ---
            if horas == 0:
                # Calcular Racha (Ahora miramos 7 días atrás)
                dias_consecutivos = 1
                for i in range(1, 8): # Del 1 al 7
                    dia_previo = (fecha_obj - timedelta(days=i)).strftime("%Y-%m-%d")
                    stats_prev = self.obtener_estadisticas_unidad(taxi['id'], "DIA", dia_previo)
                    
                    if stats_prev['horas'] == 0:
                        dias_consecutivos += 1
                    else:
                        break 
                
                # DEFINICIÓN DEL REPORTE (SIN DINERO)
                # No importa si faltó 1 día o 10, el monto es 0 porque es Ausencia.
                monto = 0.0
                tipo = "AUSENCIA"
                
                if dias_consecutivos == 1:
                    motivo = "Falta injustificada (1er día)"
                elif dias_consecutivos < 3:
                    motivo = f"Ausencia ({dias_consecutivos} días seguidos)"
                else:
                    # Si son 3 o más días, le ponemos la etiqueta fea para que la operadora se asuste
                    motivo = f"¡POSIBLE ABANDONO! ({dias_consecutivos} días sin trabajar)"
                
                # Contexto extra
                if taxi['base_actual_id'] == 12: motivo += " [En Fuera de Servicio]"
                if taxi['base_actual_id'] == 91: motivo += " [En Descanso]"

                candidatos.append({
                    "taxi_id": taxi['id'], 
                    "numero": num, 
                    "tipo": tipo,
                    "motivo": motivo,
                    "monto": monto 
                })

            # --- ESCENARIO 2: VAGO (< 10 Horas) ---
            elif horas < 10.0:
                # AQUÍ SÍ HAY DINERO DE POR MEDIO
                faltantes = 10.0 - horas
                multa = faltantes * 50.0 # $50 por hora faltante
                candidatos.append({
                    "taxi_id": taxi['id'], 
                    "numero": num, 
                    "tipo": "MULTA", # Esto activará el botón de cobrar
                    "motivo": f"Incumplimiento Horas ({horas:.1f} hrs trabajadas)", 
                    "monto": round(multa, 2)
                })
        
        print(f"--- FIN AUDITORÍA: {len(candidatos)} REGISTROS ---")      
        conn.close()
        return candidatos


    def ya_se_hizo_auditoria_hoy(self):
        """ Devuelve True si el sistema ya generó reportes automáticos HOY """
        conn, cursor = self._conectar()
        hoy = datetime.now().strftime("%Y-%m-%d")
        
        # Buscamos si hay algo registrado por 'SISTEMA' con la fecha de hoy
        cursor.execute(f"SELECT COUNT(*) FROM incidencias WHERE operador_id = 'SISTEMA' AND fecha_registro LIKE '{hoy}%'")
        conteo = cursor.fetchone()[0]
        conn.close()
        
        return conteo > 0
    # ==========================================
    # OPERACIONES BÁSICAS Y AUXILIARES
    # ==========================================
    
    def registrar_viaje(self, taxi_id, tipo_servicio, base_salida, destino, precio):
        conn, cursor = self._conectar()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO viajes (taxi_id, tipo_servicio_id, base_salida_id, destino, precio, fecha_hora_inicio) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (taxi_id, tipo_servicio, base_salida, destino, precio, ahora))
        conn.commit()
        conn.close()
    
    def registrar_fin_viaje(self, taxi_id):
        conn, cursor = self._conectar()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE viajes SET fecha_hora_fin = ? WHERE id = (SELECT MAX(id) FROM viajes WHERE taxi_id = ?)", (ahora, taxi_id))
        conn.commit()
        conn.close()

    def obtener_historial_viajes(self, filtro="HOY"):
        """ CORREGIDO: Incluye tipo_servicio_id para evitar IndexError en la tabla """
        conn, cursor = self._conectar()
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        
        condicion = ""
        if filtro == "HOY": condicion = f" WHERE v.fecha_hora_inicio LIKE '{fecha_hoy}%'"
        elif filtro == "MES": condicion = f" WHERE v.fecha_hora_inicio LIKE '{fecha_hoy[:7]}%'"
        elif filtro == "AÑO": condicion = f" WHERE v.fecha_hora_inicio LIKE '{fecha_hoy[:4]}%'"
        
        cursor.execute(f"""
            SELECT v.id, v.fecha_hora_inicio, t.numero_economico, 
                   v.destino, v.precio, v.tipo_servicio_id,
                   b.nombre_base, s.descripcion as nombre_servicio
            FROM viajes v
            JOIN taxis t ON v.taxi_id = t.id
            LEFT JOIN cat_bases b ON v.base_salida_id = b.id
            LEFT JOIN cat_tipos_servicio s ON v.tipo_servicio_id = s.id
            {condicion} ORDER BY v.id DESC
        """)
        datos = cursor.fetchall()
        conn.close()
        return datos

    def registrar_incidencia(self, taxi_id, tipo, descripcion, monto, operador_id):
            try:
                conn, cursor = self._conectar()
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                estado = 'PENDIENTE' if monto > 0 else 'INFORMATIVO'
                
                cursor.execute("""
                    INSERT INTO incidencias (taxi_id, tipo, descripcion, monto, fecha_registro, resuelto, operador_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (taxi_id, tipo, descripcion, monto, fecha, estado, operador_id))
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                return False
    
    def obtener_incidencias_pendientes(self):
        """ 
        VERSIÓN CORREGIDA: Trae TODO (Monto > 0 y Monto = 0).
        Quitamos el filtro 'solo_deudores' para que la interfaz reciba las ausencias.
        """
        conn, cursor = self._conectar()
        
        # Simplemente traemos todo lo que esté PENDIENTE
        query = """
            SELECT i.id, t.numero_economico, i.tipo, i.descripcion, i.monto, i.fecha_registro, i.operador_id 
            FROM incidencias i 
            JOIN taxis t ON i.taxi_id = t.id 
            WHERE i.resuelto = 'PENDIENTE' OR i.resuelto = 'INFORMATIVO'
            ORDER BY i.fecha_registro DESC
        """
        cursor.execute(query)
        datos = cursor.fetchall()
        conn.close()
        return datos

        
    def marcar_incidencia_pagada(self, incidencia_id):
        try:
            conn, cursor = self._conectar()
            cursor.execute("UPDATE incidencias SET resuelto='PAGADO' WHERE id=?", (incidencia_id,))
            conn.commit()
            conn.close()
            return True
        except: return False

    def obtener_taxis_activos(self):
        conn, cursor = self._conectar()
        cursor.execute("SELECT * FROM taxis WHERE estado_sistema = 'ACTIVO'")
        res = cursor.fetchall()
        conn.close()
        return res

    def obtener_toda_la_flota(self):
        conn, cursor = self._conectar()
        cursor.execute("SELECT * FROM taxis")
        res = cursor.fetchall()
        conn.close()
        return res

    def obtener_bases_fisicas(self):
        conn, cursor = self._conectar()
        cursor.execute("SELECT id, nombre_base FROM cat_bases WHERE id <= 13")
        res = cursor.fetchall()
        conn.close()
        return res
        
    def obtener_id_por_numero(self, numero):
        conn, cursor = self._conectar()
        cursor.execute("SELECT id FROM taxis WHERE numero_economico = ?", (numero,))
        res = cursor.fetchone()
        conn.close()
        return res['id'] if res else None
    
    def eliminar_viaje(self, viaje_id):
        conn, cursor = self._conectar()
        cursor.execute("DELETE FROM viajes WHERE id=?", (viaje_id,))
        conn.commit()
        conn.close()

    def calcular_banderola_del_dia(self):
        conn, cursor = self._conectar()
        taxis = self.obtener_taxis_activos()
        conn.close()
        taxis.sort(key=lambda x: int(x['numero_economico']))
        if not taxis: return "---"
        return taxis[(int(datetime.now().strftime("%j")) - 1) % len(taxis)]['numero_economico']

    # Métodos de compatibilidad
    def registrar_nuevo_taxi(self, numero_economico, id_base_inicial=12):
        try:
            conn, cursor = self._conectar()
            
            # === EL SEGURO ANTI-DUPLICADOS ===
            cursor.execute("SELECT id FROM taxis WHERE numero_economico = ?", (numero_economico,))
            if cursor.fetchone():
                print(f"ALERTA: El taxi {numero_economico} ya existe. No se duplicará.")
                conn.close()
                return False # Devuelve Falso para avisar que no se pudo
            # =================================

            # Si no existe, procedemos a crearlo
            fecha_alta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                INSERT INTO taxis (numero_economico, estado_sistema, fecha_alta, base_actual_id, fecha_movimiento)
                VALUES (?, 'ACTIVO', ?, ?, ?)
            """, (numero_economico, fecha_alta, id_base_inicial, fecha_alta))
            
            conn.commit()
            conn.close()
            print(f"Taxi {numero_economico} registrado correctamente.")
            return True
            
        except Exception as e:
            print(f"Error registrando taxi: {e}")
            return False
        

    def eliminar_taxi(self, taxi_id):
        try: 
            conn, cursor = self._conectar()
            cursor.execute("DELETE FROM taxis WHERE id=?", (taxi_id,))
            conn.commit(); conn.close()
            return True
        except: return False


    def obtener_top_taxis_admin(self, periodo, fecha_ref):
        """ 
        Genera los TOPS separados (Viajes y Horas) y cruza con historial de REPORTE.
        También prepara datos para gráficas.
        """
        conn, cursor = self._conectar()
        
        # Filtros de fecha
        filtro_v = "" # Para viajes
        filtro_i = "" # Para incidencias (fecha_registro)
        filtro_t = "" # Para turnos (fecha_inicio)
        
        if periodo == "DIA": 
            filtro_v = f"AND fecha_hora_inicio LIKE '{fecha_ref}%'"
            filtro_i = f"AND fecha_registro LIKE '{fecha_ref}%'"
            filtro_t = f"AND fecha_inicio LIKE '{fecha_ref}%'"
        elif periodo == "MES": 
            filtro_v = f"AND fecha_hora_inicio LIKE '{fecha_ref[:7]}%'"
            filtro_i = f"AND fecha_registro LIKE '{fecha_ref[:7]}%'"
            filtro_t = f"AND fecha_inicio LIKE '{fecha_ref[:7]}%'"
        elif periodo == "AÑO": 
            filtro_v = f"AND fecha_hora_inicio LIKE '{fecha_ref[:4]}%'"
            filtro_i = f"AND fecha_registro LIKE '{fecha_ref[:4]}%'"
            filtro_t = f"AND fecha_inicio LIKE '{fecha_ref[:4]}%'"

        # 1. TOTAL GANADO (Dato global)
        cursor.execute(f"SELECT SUM(precio) FROM viajes WHERE 1=1 {filtro_v}")
        total_empresa = cursor.fetchone()[0] or 0.0

        # 2. PROCESAMIENTO POR UNIDAD (Para sacar los Tops)
        # Obtenemos toda la flota activa para analizarla uno por uno
        cursor.execute("SELECT id, numero_economico FROM taxis")
        flota = cursor.fetchall()
        
        lista_rendimiento = []
        
        for taxi in flota:
            tid = taxi['id']
            num = taxi['numero_economico']
            
            # A) Conteo de Viajes y Dinero
            cursor.execute(f"SELECT COUNT(*), SUM(precio) FROM viajes WHERE taxi_id=? {filtro_v}", (tid,))
            res_v = cursor.fetchone()
            viajes = res_v[0] or 0
            dinero = res_v[1] or 0.0
            
            # B) Conteo de Reportes (Conducta) - ¡CRUCIAL!
            cursor.execute(f"SELECT COUNT(*) FROM incidencias WHERE taxi_id=? {filtro_i}", (tid,))
            reportes = cursor.fetchone()[0] or 0
            
            # C) Cálculo de Horas (Usamos la lógica existente)
            # (Simplificada aquí para velocidad, idealmente reusar obtener_estadisticas_unidad)
            horas = 0.0
            cursor.execute(f"SELECT fecha_inicio, fecha_fin FROM turnos WHERE taxi_id=? {filtro_t}", (tid,))
            turnos = cursor.fetchall()
            for t in turnos:
                try:
                    ini = datetime.strptime(t['fecha_inicio'], "%Y-%m-%d %H:%M:%S")
                    fin_str = t['fecha_fin']
                    if fin_str:
                        fin = datetime.strptime(fin_str, "%Y-%m-%d %H:%M:%S")
                        horas += (fin - ini).total_seconds() / 3600
                except: pass
            
            # Solo agregamos si trabajó algo (viajes u horas)
            if viajes > 0 or horas > 0:
                lista_rendimiento.append({
                    "numero": num,
                    "viajes": viajes,
                    "dinero": dinero,
                    "horas": horas,
                    "reportes": reportes # <--- EL DATO DEL REGALO DE NAVIDAD
                })
        
        # 3. GENERAR LOS TOPS
        # Top Viajes (Los más rápidos)
        top_viajes = sorted(lista_rendimiento, key=lambda x: x['viajes'], reverse=True)[:5]
        
        # Top Horas (Los más constantes)
        top_horas = sorted(lista_rendimiento, key=lambda x: x['horas'], reverse=True)[:5]

        # 4. DATOS PARA GRÁFICA (Distribución de Servicios)
        cursor.execute(f"""
            SELECT s.descripcion, COUNT(*) 
            FROM viajes v JOIN cat_tipos_servicio s ON v.tipo_servicio_id = s.id 
            WHERE 1=1 {filtro_v} GROUP BY s.descripcion
        """)
        datos_grafica = cursor.fetchall() # [(Base, 10), (Telefono, 5)...]

        conn.close()
        
        return {
            "total_empresa": total_empresa, 
            "top_viajes": top_viajes, 
            "top_horas": top_horas,
            "grafica_servicios": datos_grafica
        }
    
    def cambiar_estado_taxi(self, taxi_id, nuevo_estado):
        try:
            # CORRECCIÓN: Recibimos conn Y cursor separados por coma
            conn, cursor = self._conectar() 
            
            cursor.execute("UPDATE taxis SET estado_sistema = ? WHERE id = ?", (nuevo_estado, taxi_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error al cambiar estado taxi: {e}")
            return False
        

    # --- NUEVAS FUNCIONES PARA DERECHO DE PISO Y REPORTE UNIDAD ---
    def obtener_incidencias_globales_periodo(self, fecha_inicio, fecha_fin):
        try:
            conn, c = self._conectar()
            query = """
                SELECT t.numero_economico as unidad, i.tipo, i.descripcion, i.operador_id as operador, i.monto
                FROM incidencias i
                JOIN taxis t ON i.taxi_id = t.id
                WHERE date(i.fecha_registro) BETWEEN ? AND ?
                AND i.resuelto NOT IN ('RESUELTO', 'PAGADO')
                ORDER BY i.fecha_registro ASC
            """
            c.execute(query, (fecha_inicio, fecha_fin))
            return [dict(row) for row in c.fetchall()]
        except Exception as e:
            print(f"Error al obtener incidencias globales: {e}")
            return []
    
    def obtener_incidencias_por_unidad(self, taxi_id, periodo="SIEMPRE", fecha_ref=None):
        # Esta función busca multas, reportes y cuotas de un solo taxi
        try:
            conn, c = self._conectar()
            query = """
                SELECT tipo, descripcion, monto, fecha_registro, resuelto 
                FROM incidencias 
                WHERE taxi_id = ? 
                AND resuelto NOT IN ('RESUELTO', 'PAGADO')
            """
            params = [taxi_id]
            
            # Filtro de fecha (igual que en los viajes)
            if periodo == "DIA":
                query += " AND date(fecha_registro) = ?"
                params.append(fecha_ref)
            elif periodo == "MES":
                query += " AND strftime('%Y-%m', fecha_registro) = ?"
                params.append(fecha_ref[:7]) # YYYY-MM
                
            query += " ORDER BY fecha_registro DESC"
            
            c.execute(query, params)
            datos = c.fetchall()
            conn.close()
            return datos
        except Exception as e:
            print(f"Error obteniendo incidencias unidad: {e}")
            return []
        

    # EN LA FUNCIÓN __init__ o donde creas tablas (OJO: Esto se auto-repara, 
    # pero asegúrate de que interfaz.py llame a verificar_db al inicio)
    # ...
    
    def obtener_config_piso(self):
        try:
            conn, c = self._conectar()
            # Creamos tabla si no existe al vuelo (por si acaso)
            c.execute("CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)")
            
            c.execute("SELECT valor FROM configuracion WHERE clave='costo_piso'")
            res = c.fetchone()
            
            if res:
                return float(res['valor'])
            else:
                # Valor por defecto
                c.execute("INSERT INTO configuracion (clave, valor) VALUES ('costo_piso', '150.0')")
                conn.commit()
                return 150.0
            conn.close()
        except:
            return 150.0

    def guardar_config_piso(self, nuevo_monto):
        try:
            conn, c = self._conectar()
            c.execute("REPLACE INTO configuracion (clave, valor) VALUES ('costo_piso', ?)", (str(nuevo_monto),))
            conn.commit(); conn.close()
            return True
        except: return False

    def obtener_fecha_ultimo_cobro(self):
        # Esta función lee la "memoria" para saber cuándo fue el último cobro
        try:
            conn, c = self._conectar()
            # Aseguramos que la tabla exista
            c.execute("CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)")
            
            c.execute("SELECT valor FROM configuracion WHERE clave='fecha_ultimo_piso'")
            res = c.fetchone()
            conn.close()
            if res: return res['valor'] # Devuelve la fecha "2026-01-25"
            return None # Nunca se ha cobrado
        except: return None

    def generar_cargos_piso_masivos(self):
        monto = self.obtener_config_piso() # Obtiene el precio (ej: 150)
        try:
            conn, c = self._conectar()
            
            # 1. Obtenemos taxis activos
            c.execute("SELECT id FROM taxis WHERE estado_sistema = 'ACTIVO'")
            taxis = c.fetchall()
            
            ahora = datetime.now()
            fecha_hora = ahora.strftime("%Y-%m-%d %H:%M:%S")
            fecha_corta = ahora.strftime("%Y-%m-%d") # Solo fecha para el candado
            
            count = 0
            # 2. Generamos la deuda a cada uno
            for t in taxis:
                c.execute("""
                    INSERT INTO incidencias (taxi_id, tipo, descripcion, monto, fecha_registro, resuelto, operador_id)
                    VALUES (?, '💰 Derecho de Piso', 'Cuota operativa', ?, ?, 'PENDIENTE', 'SISTEMA')
                """, (t['id'], monto, fecha_hora))
                count += 1
            
            # 3. === AQUÍ ESTÁ LA MAGIA (MEMORIA) ===
            # Guardamos que "hoy" se hizo el cobro
            c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('fecha_ultimo_piso', ?)", (fecha_corta,))
            # =======================================
            
            conn.commit(); conn.close()
            return count, monto
        except Exception as e:
            print(f"Error: {e}")
            return 0, 0
        

    def marcar_incidencia_resuelta(self, id_incidencia):
        # Sirve para PAGAR o para REVISAR (Archivar)
        try:
            conn, c = self._conectar()
            # Cambiamos estado a RESUELTO (sirve para ambos casos)
            c.execute("UPDATE incidencias SET resuelto = 'RESUELTO' WHERE id = ?", (id_incidencia,))
            conn.commit(); conn.close()
            return True
        except: return False

    def obtener_historial_incidencias_filtro(self, texto="", fecha=None):
        # Búsqueda en el historial (YA NO PENDIENTES)
        try:
            conn, c = self._conectar()
            query = """
                SELECT i.id, t.numero_economico, i.tipo, i.descripcion, i.monto, i.fecha_registro, i.resuelto, i.operador_id
                FROM incidencias i
                JOIN taxis t ON i.taxi_id = t.id
                WHERE i.resuelto != 'PENDIENTE' 
            """
            params = []
            
            if fecha:
                query += " AND date(i.fecha_registro) = ?"
                params.append(fecha)
            
            if texto:
                query += " AND (t.numero_economico LIKE ? OR i.tipo LIKE ?)"
                params.append(f"%{texto}%")
                params.append(f"%{texto}%")
                
            query += " ORDER BY i.fecha_registro DESC LIMIT 100"
            
            c.execute(query, params)
            datos = c.fetchall()
            conn.close()
            return datos
        except Exception as e:
            print(e); return []
        
    def obtener_costo_banderola(self):
        try:
            conn, c = self._conectar()
            c.execute("SELECT valor FROM configuracion WHERE clave='costo_banderola'")
            res = c.fetchone()
            conn.close()
            if res: return float(res['valor'])
            return 50.0 # Valor por defecto si no existe
        except: return 50.0

    def guardar_costo_banderola(self, nuevo_monto):
        try:
            conn, c = self._conectar()
            c.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('costo_banderola', ?)", (str(nuevo_monto),))
            conn.commit(); conn.close()
            return True
        except: return False