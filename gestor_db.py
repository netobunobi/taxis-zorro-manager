import sqlite3
import os
import ctypes
from datetime import datetime

class GestorBaseDatos:
    def __init__(self, db_name="taxis.db"):
        self.db_name = db_name

    def _conectar(self):
        """Método privado para obtener conexión"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
        return conn, conn.cursor()

    # ==========================================
    # LÓGICA DE CREACIÓN (V2.0)
    # ==========================================
    @staticmethod
    def crear_nueva_bd_v2(nombre_db="taxis.db"):
        """ Crea la estructura completa V2 desde cero """
        try:
            conn = sqlite3.connect(nombre_db)
            c = conn.cursor()
            c.execute("PRAGMA foreign_keys = ON;")

            # 1. TABLAS CATÁLOGO
            c.execute("CREATE TABLE IF NOT EXISTS cat_tipos_servicio (id INTEGER PRIMARY KEY AUTOINCREMENT, descripcion TEXT UNIQUE NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS cat_bases (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_base TEXT UNIQUE NOT NULL)")
            
            # 2. TABLA CONFIGURACIÓN (Para contraseñas y ajustes)
            c.execute("CREATE TABLE IF NOT EXISTS configuracion (clave TEXT PRIMARY KEY, valor TEXT)")

            # 3. TABLA TAXIS
            c.execute("""
                CREATE TABLE IF NOT EXISTS taxis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    numero_economico TEXT NOT NULL UNIQUE, 
                    estado_sistema TEXT DEFAULT 'ACTIVO', 
                    base_actual_id INTEGER DEFAULT 12, 
                    FOREIGN KEY(base_actual_id) REFERENCES cat_bases(id)
                )
            """)

            # 4. TABLA VIAJES
            c.execute("""
                CREATE TABLE IF NOT EXISTS viajes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    taxi_id INTEGER NOT NULL, 
                    tipo_servicio_id INTEGER NOT NULL, 
                    base_salida_id INTEGER, 
                    destino TEXT, 
                    precio REAL DEFAULT 0.0, 
                    fecha_hora_inicio TEXT, 
                    fecha_hora_fin TEXT, 
                    FOREIGN KEY(taxi_id) REFERENCES taxis(id),
                    FOREIGN KEY(tipo_servicio_id) REFERENCES cat_tipos_servicio(id)
                )
            """)

            # 5. NUEVA: TABLA INCIDENCIAS (Multas, Reportes, Observaciones)
            c.execute("""
                CREATE TABLE IF NOT EXISTS incidencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    taxi_id INTEGER,
                    tipo TEXT,       -- 'MULTA', 'OBSERVACION', 'CASTIGO'
                    descripcion TEXT,
                    monto REAL DEFAULT 0.0,
                    fecha_registro TEXT,
                    FOREIGN KEY(taxi_id) REFERENCES taxis(id)
                )
            """)

            # 6. NUEVA: TABLA BITÁCORA (Pendientes entre turnos)
            c.execute("""
                CREATE TABLE IF NOT EXISTS bitacora (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mensaje TEXT,
                    fecha_creacion TEXT,
                    estado TEXT DEFAULT 'PENDIENTE' -- 'PENDIENTE', 'RESUELTO'
                )
            """)

            # --- INSERCIÓN DE DATOS INICIALES ---

            # A. Tipos de Servicio
            c.executemany("INSERT OR IGNORE INTO cat_tipos_servicio (id, descripcion) VALUES (?, ?)", 
                          [(1,'Viaje en base'),(2,'Telefono base'),(3,'Telefono unidad'),(4,'Viaje aereo')])

            # B. Bases Físicas (1-13) + BASES ESPECIALES (90+)
            # Nota: Usamos 90+ para que sea fácil distinguir en el código que NO cuentan horas
            bases_data = [
                (1,'Cessa'), (2,'Licuor'), (3,'Santiaguito'), (4,'Aurrera'), (5,'Mercado'),
                (6,'Caros'), (7,'Survi'), (8,'Capulin'), (9,'Zocalo'), (10,'16 de Septiembre'),
                (11,'Parada Principal'), (12,'Fuera de Servicio'), (13,'En Viaje / Ocupado'),
                (90, 'Taller 🛠️'), (91, 'Z2 Descanso 🌮'), (92, 'Viaje Foráneo 🛣️'), (93, 'Viaje Local 🏘️')
            ]
            c.executemany("INSERT OR IGNORE INTO cat_bases (id, nombre_base) VALUES (?, ?)", bases_data)

            # C. Taxis (35 al 100)
            # Todos inician en base 12 (Fuera de servicio)
            taxis_nuevos = [(str(n), 'ACTIVO', 12) for n in range(35, 101)]
            c.executemany("INSERT OR IGNORE INTO taxis (numero_economico, estado_sistema, base_actual_id) VALUES (?, ?, ?)", taxis_nuevos)

            # D. Contraseña Admin por defecto
            c.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES ('admin_pass', '1234')")

            conn.commit()
            conn.close()

            # Asegurar que sea visible en Windows
            try: ctypes.windll.kernel32.SetFileAttributesW(nombre_db, 0x80)
            except: pass
            
            return True
        except Exception as e:
            print(f"Error crítico creando DB: {e}")
            return False

    # ==========================================
    # MÉTODOS DE CONSULTA (LO QUE YA TENÍAS)
    # ==========================================
    
    def registrar_nuevo_taxi(self, numero, id_base_inicial=12):
        try:
            conn, c = self._conectar()
            c.execute("INSERT INTO taxis (numero_economico, base_actual_id) VALUES (?, ?)", (numero, id_base_inicial))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def cambiar_estado_taxi(self, taxi_id, nuevo_estado):
        try:
            conn, c = self._conectar()
            c.execute("UPDATE taxis SET estado_sistema = ? WHERE id = ?", (nuevo_estado, taxi_id))
            conn.commit()
            conn.close()
            return True
        except: return False

    def obtener_taxis_activos(self):
        conn, c = self._conectar()
        # Solo traemos taxis ACTIVOS para el tablero
        c.execute("SELECT * FROM taxis WHERE estado_sistema = 'ACTIVO'")
        return c.fetchall()

    def obtener_toda_la_flota(self):
        conn, c = self._conectar()
        c.execute("SELECT * FROM taxis")
        return c.fetchall()

    def obtener_bases_fisicas(self):
        conn, c = self._conectar()
        # Solo queremos bases reales (ID < 90) para dibujarlas en el mapa
        # Las bases 90+ (Taller, Z2) no se dibujan en el grid, van a la derecha o en menús
        c.execute("SELECT id, nombre_base FROM cat_bases WHERE id <= 13") 
        return c.fetchall()

    def obtener_id_por_numero(self, numero):
        conn, c = self._conectar()
        c.execute("SELECT id FROM taxis WHERE numero_economico = ?", (numero,))
        res = c.fetchone()
        return res['id'] if res else None

    def registrar_viaje(self, taxi_id, tipo_serv, base_salida, destino, precio):
        conn, c = self._conectar()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            INSERT INTO viajes (taxi_id, tipo_servicio_id, base_salida_id, destino, precio, fecha_hora_inicio)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (taxi_id, tipo_serv, base_salida, destino, precio, ahora))
        conn.commit()
        conn.close()

    def registrar_fin_viaje(self, taxi_id):
        # Cierra el último viaje abierto de ese taxi
        conn, c = self._conectar()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Buscamos el último viaje de este taxi que no tenga fecha fin (o sea el mas reciente)
        # Simplificación: actualizamos el ultimo registro insertado para ese taxi
        c.execute("""
            UPDATE viajes 
            SET fecha_hora_fin = ? 
            WHERE id = (SELECT MAX(id) FROM viajes WHERE taxi_id = ?)
        """, (ahora, taxi_id))
        conn.commit()
        conn.close()

    def actualizar_taxi_base(self, taxi_id, nueva_base_id):
        conn, c = self._conectar()
        c.execute("UPDATE taxis SET base_actual_id = ? WHERE id = ?", (nueva_base_id, taxi_id))
        conn.commit()
        conn.close()

    def hora_entrada(self, taxi_id):
        # Lógica futura para checador
        pass

    def hora_salida(self, taxi_id):
        # Lógica futura para checador
        pass
        
    def eliminar_base_fisica(self, id_base):
        try:
            conn, c = self._conectar()
            # Mover taxis de esa base a "Fuera de Servicio" (12) antes de borrar
            c.execute("UPDATE taxis SET base_actual_id = 12 WHERE base_actual_id = ?", (id_base,))
            c.execute("DELETE FROM cat_bases WHERE id = ?", (id_base,))
            conn.commit()
            conn.close()
            return True
        except: return False

    def registrar_nueva_base(self, nombre):
        try:
            conn, c = self._conectar()
            c.execute("INSERT INTO cat_bases (nombre_base) VALUES (?)", (nombre,))
            conn.commit()
            conn.close()
            return True
        except: return False

    # --- REPORTES ---
    
    def obtener_historial_viajes(self, filtro="HOY"):
        conn, c = self._conectar()
        
        query = """
            SELECT v.id, v.fecha_hora_inicio, t.numero_economico, 
                   s.descripcion as nombre_servicio, 
                   b.nombre_base, v.destino, v.precio, v.tipo_servicio_id
            FROM viajes v
            JOIN taxis t ON v.taxi_id = t.id
            LEFT JOIN cat_tipos_servicio s ON v.tipo_servicio_id = s.id
            LEFT JOIN cat_bases b ON v.base_salida_id = b.id
        """
        
        where_clause = ""
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        mes_actual = datetime.now().strftime("%Y-%m")
        anio_actual = datetime.now().strftime("%Y")

        if filtro == "HOY":
            where_clause = f" WHERE v.fecha_hora_inicio LIKE '{fecha_hoy}%'"
        elif filtro == "MES":
            where_clause = f" WHERE v.fecha_hora_inicio LIKE '{mes_actual}%'"
        elif filtro == "AÑO":
            where_clause = f" WHERE v.fecha_hora_inicio LIKE '{anio_actual}%'"
        
        c.execute(query + where_clause + " ORDER BY v.id DESC")
        return c.fetchall()
        
    def eliminar_viaje(self, viaje_id):
        try:
            conn, c = self._conectar()
            c.execute("DELETE FROM viajes WHERE id = ?", (viaje_id,))
            conn.commit(); conn.close()
            return True
        except: return False

    def actualizar_viaje(self, viaje_id, columna, valor):
        try:
            conn, c = self._conectar()
            # Validamos columna para evitar inyección SQL básica
            if columna not in ['destino', 'precio']: return False
            c.execute(f"UPDATE viajes SET {columna} = ? WHERE id = ?", (valor, viaje_id))
            conn.commit(); conn.close()
            return True
        except: return False

    def obtener_estadisticas_unidad(self, taxi_id, periodo, fecha_ref=None):
        conn, c = self._conectar()
        
        # Filtro de fecha
        filtro_fecha = ""
        if not fecha_ref: fecha_ref = datetime.now().strftime("%Y-%m-%d")
        
        if periodo in ["DIA", "HOY"]:
            filtro_fecha = f"AND fecha_hora_inicio LIKE '{fecha_ref}%'"
        elif periodo == "MES":
            mes = fecha_ref[:7] # YYYY-MM
            filtro_fecha = f"AND fecha_hora_inicio LIKE '{mes}%'"
        elif periodo == "AÑO":
            anio = fecha_ref[:4] # YYYY
            filtro_fecha = f"AND fecha_hora_inicio LIKE '{anio}%'"

        # 1. Ganancia Total y Conteo de Viajes
        c.execute(f"SELECT SUM(precio), COUNT(*) FROM viajes WHERE taxi_id = ? {filtro_fecha}", (taxi_id,))
        res = c.fetchone()
        ganancia = res[0] if res[0] else 0.0
        viajes = res[1] if res[1] else 0
        
        # 2. CÁLCULO DE HORAS REALES (Jornada)
        # Lógica: Hora del último viaje finalizado - Hora del primer viaje iniciado
        # Esto nos da el "tiempo activo" en el sistema ese día.
        c.execute(f"""
            SELECT MIN(fecha_hora_inicio), MAX(fecha_hora_fin) 
            FROM viajes 
            WHERE taxi_id = ? {filtro_fecha}
        """, (taxi_id,))
        
        row_horas = c.fetchone()
        horas_trabajadas = 0.0
        
        if row_horas and row_horas[0] and row_horas[1]:
            try:
                # Convertimos texto a objetos de fecha para poder restar
                fmt = "%Y-%m-%d %H:%M:%S"
                inicio = datetime.strptime(row_horas[0], fmt)
                fin = datetime.strptime(row_horas[1], fmt)
                
                diferencia = fin - inicio
                # Convertimos segundos totales a horas
                horas_trabajadas = diferencia.total_seconds() / 3600.0
                
                # Si trabajó menos de 15 minutos (ej. un solo viaje corto), ponemos el tiempo real
                if horas_trabajadas < 0.1: horas_trabajadas = 0.2
                
            except Exception as e:
                print(f"Error calculando horas: {e}")
                horas_trabajadas = 0.0
        
        return {"ganancia": ganancia, "viajes": viajes, "horas": horas_trabajadas}
    
    def obtener_datos_tres_graficas(self, taxi_id, periodo, fecha_ref):
        conn, c = self._conectar()
        
        etiquetas = []
        data_dinero = []
        data_viajes = []
        data_horas = []

        try:
            # 1. Lógica si el filtro es POR DÍA (Ver actividad por horas 00h - 23h)
            if periodo in ["DIA", "HOY"]:
                # fecha_ref viene como "2026-01-24"
                query = """
                    SELECT strftime('%H', fecha_hora_inicio) as hora, SUM(precio), COUNT(*) 
                    FROM viajes 
                    WHERE taxi_id = ? AND fecha_hora_inicio LIKE ?
                    GROUP BY hora
                """
                c.execute(query, (taxi_id, f"{fecha_ref}%"))
                
                # Preparamos las 24 horas vacías
                mapa_datos = {f"{h:02d}": (0,0) for h in range(24)}
                
                # Llenamos con lo que encontró la BD
                for row in c.fetchall():
                    hora = row[0] # Ej: "09", "14"
                    mapa_datos[hora] = (row[1], row[2]) # (Dinero, Viajes)
                
                # Convertimos a listas ordenadas para la gráfica
                etiquetas = [f"{h}h" for h in mapa_datos.keys()]
                data_dinero = [v[0] for v in mapa_datos.values()]
                data_viajes = [v[1] for v in mapa_datos.values()]

            # 2. Lógica si el filtro es POR MES (Ver actividad por días 1 - 31)
            elif periodo == "MES":
                # fecha_ref viene como "2026-01-24", cortamos a "2026-01"
                mes_str = fecha_ref[:7] 
                query = """
                    SELECT strftime('%d', fecha_hora_inicio) as dia, SUM(precio), COUNT(*) 
                    FROM viajes 
                    WHERE taxi_id = ? AND fecha_hora_inicio LIKE ?
                    GROUP BY dia
                """
                c.execute(query, (taxi_id, f"{mes_str}%"))
                
                # Preparamos días del 1 al 31
                mapa_datos = {f"{d:02d}": (0,0) for d in range(1, 32)}
                
                for row in c.fetchall():
                    dia = row[0] 
                    mapa_datos[dia] = (row[1], row[2])
                
                etiquetas = list(mapa_datos.keys())
                data_dinero = [v[0] for v in mapa_datos.values()]
                data_viajes = [v[1] for v in mapa_datos.values()]

            # 3. Lógica si el filtro es POR AÑO (Ver actividad por meses Ene - Dic)
            elif periodo == "AÑO":
                anio_str = fecha_ref[:4] # "2026"
                query = """
                    SELECT strftime('%m', fecha_hora_inicio) as mes, SUM(precio), COUNT(*) 
                    FROM viajes 
                    WHERE taxi_id = ? AND fecha_hora_inicio LIKE ?
                    GROUP BY mes
                """
                c.execute(query, (taxi_id, f"{anio_str}%"))
                
                mapa_datos = {f"{m:02d}": (0,0) for m in range(1, 13)}
                
                for row in c.fetchall():
                    mes = row[0]
                    mapa_datos[mes] = (row[1], row[2])
                
                nombres_meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                etiquetas = nombres_meses
                data_dinero = [mapa_datos[f"{m:02d}"][0] for m in range(1, 13)]
                data_viajes = [mapa_datos[f"{m:02d}"][1] for m in range(1, 13)]

            # 4. Cálculo de Horas (Estimado simple por ahora: 30 mins por viaje)
            # Luego lo conectamos con los tiempos de Taller/Descanso
            data_horas = [v * 0.5 for v in data_viajes]

        except Exception as e:
            print(f"Error generando gráficas: {e}")
            return {"etiquetas": [], "dinero": [], "viajes": [], "horas": []}

        return {
            "etiquetas": etiquetas,
            "dinero": data_dinero,
            "viajes": data_viajes,
            "horas": data_horas
        }
    

    def obtener_ranking_bases(self, periodo):
        # Placeholder para gráfica de bases
        return ["Base A", "Base B"], [10, 5]

    def obtener_datos_reporte_global(self, periodo, fecha_str):
        # Placeholder para reporte PDF
        # Aquí luego haremos la consulta que suma TODO
        return {"total_dinero": 0, "total_viajes": 0, "top_taxis": []}

    def obtener_viajes_por_unidad_y_periodo(self, taxi_id, periodo, fecha_ref):
        conn, c = self._conectar()
        
        filtro = ""
        if periodo in ["DIA", "HOY"]: 
            filtro = f" AND v.fecha_hora_inicio LIKE '{fecha_ref}%'"
        elif periodo == "MES": 
            filtro = f" AND v.fecha_hora_inicio LIKE '{fecha_ref[:7]}%'"
        elif periodo == "AÑO": 
            filtro = f" AND v.fecha_hora_inicio LIKE '{fecha_ref[:4]}%'"
        
        # CONSULTA MEJORADA: Trae el nombre de la base (Cessa, Mercado...) en vez del ID
        query = """
            SELECT v.fecha_hora_inicio, v.destino, v.precio, 
                   b.nombre_base, s.descripcion as tipo_servicio
            FROM viajes v
            LEFT JOIN cat_bases b ON v.base_salida_id = b.id
            LEFT JOIN cat_tipos_servicio s ON v.tipo_servicio_id = s.id
            WHERE v.taxi_id = ?
        """
        
        c.execute(query + filtro + " ORDER BY v.fecha_hora_inicio ASC", (taxi_id,))
        filas = c.fetchall()
        
        datos = []
        for f in filas:
            # Si el viaje salió de una base física, ponemos el nombre de la base
            # Si fue "Teléfono" o "Aéreo", ponemos el tipo de servicio
            if f["nombre_base"] and f["nombre_base"] not in ["Fuera de Servicio", "En Viaje"]:
                origen_texto = f["nombre_base"]
            else:
                origen_texto = f["tipo_servicio"] or "Desconocido"

            datos.append({
                "fecha": f["fecha_hora_inicio"],
                "origen": origen_texto,
                "destino": f["destino"] if f["destino"] else "---",
                "precio": f["precio"] if f["precio"] else 0.0
            })
            
        return datos

    def eliminar_taxi(self, taxi_id):
        try:
            conn, c = self._conectar()
            # Borramos historial para que no den error las llaves foráneas
            c.execute("DELETE FROM viajes WHERE taxi_id = ?", (taxi_id,))
            c.execute("DELETE FROM incidencias WHERE taxi_id = ?", (taxi_id,))
            # Borramos el taxi
            c.execute("DELETE FROM taxis WHERE id = ?", (taxi_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error borrando taxi: {e}")
            return False
        

        