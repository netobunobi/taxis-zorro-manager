import sqlite3
import os
from datetime import datetime

class GestorBaseDatos:
    def __init__(self, nombre_bd="taxis.db"):
        self.nombre_bd = nombre_bd
        self._verificar_archivo()

    def _verificar_archivo(self):
        """Verifica que la BD exista antes de intentar conectar"""
        if not os.path.exists(self.nombre_bd):
            print(f"⚠️ ALERTA: No encuentro {self.nombre_bd}. Asegúrate de haber corrido crear_bd.py")

    def _conectar(self):
        """Crea la conexión y configura para recibir diccionarios"""
        conexion = sqlite3.connect(self.nombre_bd)
        # Esto permite acceder a los datos por nombre (fila['numero']) 
        conexion.row_factory = sqlite3.Row 
        
        cursor = conexion.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;") # Siempre activar esto
        return conexion, cursor

    # ==========================================
    # 1. FUNCIONES DE LECTURA (CONSULTAS)
    # ==========================================

    def obtener_taxis_activos(self):
        """Devuelve la lista de taxis que están trabajando (ACTIVOS)."""
        sql = """
            SELECT 
                t.id, 
                t.numero_economico, 
                t.base_actual_id,
                b.nombre_base as estado_texto
            FROM taxis t
            LEFT JOIN cat_bases b ON t.base_actual_id = b.id
            WHERE t.estado_sistema = 'ACTIVO'
        """
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql)
            resultados = cursor.fetchall()
            conexion.close()
            return [dict(fila) for fila in resultados]
        except Exception as error:
            print(f"Error al obtener taxis: {error}")
            return []

    def obtener_bases(self):
        """Devuelve la lista de bases (Cessa, Mercado, etc.)"""
        sql = "SELECT id, nombre_base FROM cat_bases"
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql)
            resultados = cursor.fetchall()
            conexion.close()
            return [dict(fila) for fila in resultados]
        except Exception as error:
            print(f"Error al obtener bases: {error}")
            return []

    
            return []

    def obtener_ganancias_fecha(self, fecha_str):
        """
        Suma todo el dinero ganado en una fecha específica.
        Formato fecha: 'YYYY-MM-DD' (Ej: '2026-01-17')
        """
        sql = "SELECT sum(precio) FROM viajes WHERE fecha_hora_inicio LIKE ?"
        parametro = f"{fecha_str}%"
        
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, (parametro,))
            resultado = cursor.fetchone()
            conexion.close()
            # Si devuelve None (no hubo viajes), retornamos 0.0
            return resultado[0] if resultado[0] else 0.0
        except Exception as e:
            print("Error al calcular ganancias:", e)
            return 0.0

    # ==========================================
    # 2. FUNCIONES DE ADMINISTRACIÓN (ALTAS Y BAJAS)
    # ==========================================

    def registrar_nuevo_taxi(self, numero_economico, id_base_inicial=12):
        """Crea un nuevo taxi en la base de datos."""
        sql = "INSERT INTO taxis (numero_economico, base_actual_id, estado_sistema) VALUES (?, ?, 'ACTIVO')"
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, (numero_economico, id_base_inicial))
            conexion.commit()
            conexion.close()
            print(f"✅ Taxi {numero_economico} creado.")
            return True
        except Exception as error:
            print(f"❌ Error al crear taxi: {error}")
            return False

    def dar_baja_taxi(self, taxi_id):
        """Borrado lógico: Desactiva el taxi pero mantiene su historial."""
        sql = "UPDATE taxis SET estado_sistema = 'BAJA' WHERE id = ?"
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, (taxi_id,))
            conexion.commit()
            conexion.close()
            print(f"🚫 Taxi {taxi_id} dado de baja.")
            return True
        except Exception as e:
            print("Error al dar de baja:", e)
            return False

    # ==========================================
    # 3. FUNCIONES DE OPERACIÓN (MOVIMIENTOS)
    # ==========================================

    def actualizar_taxi_base(self, taxi_id, base_actual_id):
        sql = "UPDATE taxis SET base_actual_id = ? WHERE id = ?"
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, (base_actual_id, taxi_id))
            conexion.commit() # <--- IMPORTANTE: Esto guarda el archivo en el disco
            conexion.close()
            return True
        except Exception as error:
            print(f"Error al guardar: {error}")
            return False

    def registrar_viaje(self, taxi_id, tipo_servicio_id, base_salida_id, destino, precio):
        """Registra el inicio de un viaje."""
        fecha_hora_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_hora_fin = None

        sql = """
            INSERT INTO viajes 
            (taxi_id, tipo_servicio_id, base_salida_id, destino, precio, fecha_hora_inicio, fecha_hora_fin) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        datos = (taxi_id, tipo_servicio_id, base_salida_id, destino, precio, fecha_hora_inicio, fecha_hora_fin)

        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, datos)
            conexion.commit()
            conexion.close()
            print(f"✅ Viaje registrado para taxi {taxi_id}")
            return True
        except Exception as e:
            print(f"❌ Error al registrar viaje: {e}")
            return False
    
    def registrar_fin_viaje(self, taxi_id):
        """Cierra el viaje abierto de un taxi."""
        fecha_hora_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sql = """
            UPDATE viajes
            SET fecha_hora_fin = ?
            WHERE taxi_id = ? AND fecha_hora_fin IS NULL
        """
        datos = (fecha_hora_fin, taxi_id)

        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, datos)
            conexion.commit()
            conexion.close()
            print(f"✅ Viaje cerrado para taxi {taxi_id}")
            return True
        except Exception as error:
            print(f"Error al cerrar viaje: {error}")
            return False

    # ==========================================
    # 4. FUNCIONES DE TURNOS (RELOJ CHECADOR)
    # ==========================================

    def hora_entrada(self, taxi_id):
        """ Solo abre un turno si NO hay uno abierto ya (evita duplicados al mover entre bases) """
        try:
            conexion, cursor = self._conectar()
            
            # Verificamos si ya existe un turno abierto para este taxi
            cursor.execute("SELECT id FROM turnos_trabajo WHERE taxi_id = ? AND fecha_fin IS NULL", (taxi_id,))
            existe_turno = cursor.fetchone()
            
            if existe_turno:
                conexion.close()
                return True # Ya está trabajando, no hacemos nada
            
            # Si no hay turno abierto, lo creamos
            fecha_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO turnos_trabajo (taxi_id, fecha_inicio) VALUES (?,?)", (taxi_id, fecha_inicio))
            
            conexion.commit()
            conexion.close()
            print(f"🕒 Turno abierto para taxi {taxi_id}")
            return True
        except Exception as e:
            print(f"Error en hora_entrada: {e}")
            return False
        
    def hora_salida(self, taxi_id):
        """Cierra el turno de trabajo abierto."""
        fecha_fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = "UPDATE turnos_trabajo SET fecha_fin = ? WHERE taxi_id = ? AND fecha_fin IS NULL"
        datos = (fecha_fin, taxi_id)

        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, datos)
            
            if cursor.rowcount == 0:
                print(f"⚠️ El taxi {taxi_id} no tenía turno abierto.")
                conexion.close()
                return False

            conexion.commit()
            conexion.close()
            print(f"🕒 Turno cerrado para taxi {taxi_id}")
            return True
        except Exception as error:
            print("Error al cerrar turno: ", error)
            return False
        

    def obtener_id_por_numero(self, numero):
        """Busca el ID de un taxi usando su número económico (ej. 80)"""
        try:
            conexion, cursor = self._conectar()
            cursor.execute("SELECT id FROM taxis WHERE numero_economico = ?", (numero,))
            res = cursor.fetchone()
            conexion.close()
            return res['id'] if res else None
        except:
            return None
        
    def registrar_fin_viaje(self, taxi_id):
        """Busca el viaje activo del taxi y pone la fecha_hora_fin"""
        # CORRECCIÓN: Nombre de columna cambiado a fecha_hora_fin
        sql = "UPDATE viajes SET fecha_hora_fin = datetime('now') WHERE taxi_id = ? AND fecha_hora_fin IS NULL"
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, (taxi_id,))
            
            # Solo si realmente había un viaje abierto que cerrar
            if cursor.rowcount > 0:
                conexion.commit()
                print(f"🏁 Viaje finalizado en BD para taxi ID: {taxi_id}")
            
            conexion.close()
            return True
        except Exception as e:
            # Aquí verás si hay algún otro error de nombre
            print(f"❌ Error al cerrar viaje en BD: {e}")
            return False
        


    # ==========================================
    # ACTUALIZACIÓN: MEJOR CONSULTA DE HISTORIAL
    # ==========================================
    def obtener_historial_viajes(self, filtro="HOY"):
        """
        Trae el historial filtrado.
        Filtros: 'HOY', 'MES', 'ANIO', 'SIEMPRE'
        """
        # Consulta Base
        sql = """
            SELECT 
                v.id, 
                v.fecha_hora_inicio, 
                v.tipo_servicio_id, 
                t.numero_economico, 
                b.nombre_base, 
                v.destino, 
                v.precio
            FROM viajes v
            JOIN taxis t ON v.taxi_id = t.id
            LEFT JOIN cat_bases b ON v.base_salida_id = b.id
        """
        
        # Aplicamos el filtro mágico de SQLite
        clausula = ""
        if filtro == "HOY":
            # Compara la fecha del registro con la fecha actual del sistema
            clausula = "WHERE date(v.fecha_hora_inicio) = date('now', 'localtime')"
        elif filtro == "MES":
            # Compara año y mes
            clausula = "WHERE strftime('%Y-%m', v.fecha_hora_inicio) = strftime('%Y-%m', 'now', 'localtime')"
        elif filtro == "ANIO":
            # Compara solo año
            clausula = "WHERE strftime('%Y', v.fecha_hora_inicio) = strftime('%Y', 'now', 'localtime')"
        # Si es 'SIEMPRE', no ponemos WHERE (trae todo)

        sql_final = f"{sql} {clausula} ORDER BY v.fecha_hora_inicio DESC"

        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql_final)
            resultados = cursor.fetchall()
            conexion.close()
            return [dict(fila) for fila in resultados]
        except Exception as e:
            print("Error historial:", e)
            return []

    # ==========================================
    # NUEVO: FUNCIONES PARA CORREGIR ERRORES
    # ==========================================
    def actualizar_viaje(self, viaje_id, columna_db, nuevo_valor):
        """ Edita un campo específico de un viaje (ej. precio o destino) """
        sql = f"UPDATE viajes SET {columna_db} = ? WHERE id = ?"
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, (nuevo_valor, viaje_id))
            conexion.commit()
            conexion.close()
            print(f"✅ Viaje {viaje_id} actualizado: {columna_db} = {nuevo_valor}")
            return True
        except Exception as e:
            print(f"❌ Error al actualizar viaje: {e}")
            return False

    def eliminar_viaje(self, viaje_id):
        """ Borra un viaje definitivamente """
        try:
            conexion, cursor = self._conectar()
            cursor.execute("DELETE FROM viajes WHERE id = ?", (viaje_id,))
            conexion.commit()
            conexion.close()
            print(f"🗑️ Viaje {viaje_id} eliminado.")
            return True
        except Exception as e:
            print(f"❌ Error al eliminar viaje: {e}")
            return False
        
    # ==========================================
    # 5. GESTIÓN DE FLOTA (ADMINISTRACIÓN)
    # ==========================================

    def obtener_toda_la_flota(self):
        """ Devuelve TODOS los taxis (Activos e Inactivos) para la tabla de Admin """
        sql = "SELECT * FROM taxis ORDER BY numero_economico ASC"
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql)
            res = cursor.fetchall()
            conexion.close()
            return [dict(f) for f in res]
        except Exception as e:
            print("Error flota:", e)
            return []

    def cambiar_estado_taxi(self, taxi_id, nuevo_estado):
        """ 
        nuevo_estado puede ser 'ACTIVO' o 'INACTIVO'.
        Si es INACTIVO, desaparecerá del tablero principal.
        """
        try:
            conexion, cursor = self._conectar()
            cursor.execute("UPDATE taxis SET estado_sistema = ? WHERE id = ?", (nuevo_estado, taxi_id))
            conexion.commit()
            conexion.close()
            return True
        except Exception as e:
            print("Error cambiar estado:", e)
            return False

    def obtener_estadisticas_unidad(self, taxi_id, periodo="DIA", fecha_ref=None):
        """ Calcula $$$, Viajes y Horas basado en una fecha de referencia """
        conexion, cursor = self._conectar()
        
        # Si no mandan fecha, usamos hoy
        if not fecha_ref:
            from datetime import datetime
            fecha_ref = datetime.now().strftime("%Y-%m-%d")

        # Clausulas WHERE dinámicas
        if periodo == "DIA": # Antes era HOY
            filtro = f"AND date(fecha_hora_inicio) = '{fecha_ref}'"
            filtro_t = f"AND date(fecha_inicio) = '{fecha_ref}'"
        elif periodo == "MES":
            # Extraemos YYYY-MM de la fecha seleccionada
            mes_ref = fecha_ref[:7] 
            filtro = f"AND strftime('%Y-%m', fecha_hora_inicio) = '{mes_ref}'"
            filtro_t = f"AND strftime('%Y-%m', fecha_inicio) = '{mes_ref}'"
        elif periodo == "ANIO":
            anio_ref = fecha_ref[:4]
            filtro = f"AND strftime('%Y', fecha_hora_inicio) = '{anio_ref}'"
            filtro_t = f"AND strftime('%Y', fecha_inicio) = '{anio_ref}'"
        else:
            filtro = "" # SIEMPRE
            filtro_t = ""

        # 1. Dinero y Viajes
        sql_dinero = f"SELECT count(*), sum(precio) FROM viajes WHERE taxi_id = ? {filtro}"
        cursor.execute(sql_dinero, (taxi_id,))
        res_dinero = cursor.fetchone()
        
        # 2. Horas
        sql_horas = f"SELECT sum((julianday(fecha_fin) - julianday(fecha_inicio)) * 24) FROM turnos_trabajo WHERE taxi_id = ? {filtro_t}"
        cursor.execute(sql_horas, (taxi_id,))
        res_horas = cursor.fetchone()

        conexion.close()
        
        return {
            "viajes": res_dinero[0] if res_dinero[0] else 0,
            "ganancia": res_dinero[1] if res_dinero[1] else 0.0,
            "horas": res_horas[0] if res_horas[0] else 0.0
        }

    def obtener_viajes_por_unidad_y_periodo(self, taxi_id, periodo, fecha_ref=None):
        """ Trae el detalle para el PDF """
        if not fecha_ref:
            from datetime import datetime
            fecha_ref = datetime.now().strftime("%Y-%m-%d")

        sql = """
            SELECT v.fecha_hora_inicio, v.tipo_servicio_id, b.nombre_base, v.destino, v.precio
            FROM viajes v LEFT JOIN cat_bases b ON v.base_salida_id = b.id
            WHERE v.taxi_id = ?
        """
        
        if periodo == "DIA":
            sql += f" AND date(v.fecha_hora_inicio) = '{fecha_ref}'"
        elif periodo == "MES":
            sql += f" AND strftime('%Y-%m', v.fecha_hora_inicio) = '{fecha_ref[:7]}'"
        elif periodo == "ANIO":
            sql += f" AND strftime('%Y', v.fecha_hora_inicio) = '{fecha_ref[:4]}'"
            
        sql += " ORDER BY v.fecha_hora_inicio DESC"
        
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, (taxi_id,))
            res = cursor.fetchall()
            conexion.close()
            
            mapa = {1: "Base", 2: "Tel. Base", 3: "Tel. Unidad", 4: "Aéreo"}
            return [{
                "fecha_hora_inicio": r['fecha_hora_inicio'],
                "concepto": mapa.get(r['tipo_servicio_id'], "Viaje"),
                "origen": r['nombre_base'] if r['nombre_base'] else "////",
                "destino": r['destino'],
                "precio": r['precio']
            } for r in res]
        except Exception as e:
            return []
        
    def obtener_datos_grafica(self, taxi_id):
        """ 
        Devuelve un diccionario con listas para: 
        Fechas, Dinero, Viajes y Horas (de los últimos 7 días con actividad)
        """
        conexion, cursor = self._conectar()
        
        # 1. OBTENER DINERO Y VIAJES (Agrupado por día)
        sql_viajes = """
            SELECT substr(fecha_hora_inicio, 1, 10) as fecha, SUM(precio) as total, COUNT(*) as viajes
            FROM viajes WHERE taxi_id = ? GROUP BY fecha ORDER BY fecha DESC LIMIT 7
        """
        cursor.execute(sql_viajes, (taxi_id,))
        datos_v = cursor.fetchall()
        
        # 2. OBTENER HORAS (Agrupado por día)
        sql_turnos = """
            SELECT substr(fecha_inicio, 1, 10) as fecha, 
            SUM((julianday(fecha_fin) - julianday(fecha_inicio)) * 24) as horas
            FROM turnos_trabajo WHERE taxi_id = ? AND fecha_fin IS NOT NULL
            GROUP BY fecha ORDER BY fecha DESC LIMIT 7
        """
        cursor.execute(sql_turnos, (taxi_id,))
        datos_t = cursor.fetchall()
        conexion.close()

        # 3. PROCESAR DATOS (Unificar en un diccionario por fecha)
        # Creamos un mapa maestro de fechas para combinar tablas
        mapa_datos = {}
        
        # Llenamos con viajes/dinero
        for d in datos_v:
            f = d['fecha'][5:] # MM-DD
            if f not in mapa_datos: mapa_datos[f] = {'dinero':0, 'viajes':0, 'horas':0}
            mapa_datos[f]['dinero'] = d['total']
            mapa_datos[f]['viajes'] = d['viajes']

        # Llenamos con horas
        for d in datos_t:
            f = d['fecha'][5:]
            if f not in mapa_datos: mapa_datos[f] = {'dinero':0, 'viajes':0, 'horas':0}
            mapa_datos[f]['horas'] = d['horas']

        # Ordenar cronológicamente
        fechas_ord = sorted(mapa_datos.keys())
        
        return {
            "fechas": fechas_ord,
            "dinero": [mapa_datos[f]['dinero'] for f in fechas_ord],
            "viajes": [mapa_datos[f]['viajes'] for f in fechas_ord],
            "horas":  [mapa_datos[f]['horas']  for f in fechas_ord]
        }
    
        """ 
        Devuelve 2 listas: Fechas y Ganancias de los últimos 7 días con actividad 
        para pintar la gráfica.
        """
        # SQLite: Agrupamos por fecha (YYYY-MM-DD) y sumamos el precio
        sql = """
            SELECT 
                substr(fecha_hora_inicio, 1, 10) as fecha, 
                SUM(precio) as total
            FROM viajes 
            WHERE taxi_id = ?
            GROUP BY fecha
            ORDER BY fecha DESC 
            LIMIT 7
        """
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, (taxi_id,))
            datos = cursor.fetchall()
            conexion.close()
            
            # Ordenamos cronológicamente (de antiguo a nuevo) para la gráfica
            datos.reverse()
            
            # Separamos en dos listas para Matplotlib
            fechas = [d['fecha'][5:] for d in datos] # Solo mostramos MM-DD para ahorrar espacio
            dineros = [d['total'] for d in datos]
            
            return fechas, dineros
        except Exception as e:
            print("Error gráfica:", e)
            return [], []
        

    def obtener_datos_tres_graficas(self, taxi_id, periodo, fecha_ref=None):
        """
        Genera gráficas respetando la fecha seleccionada en el calendario.
        """
        from datetime import datetime
        import calendar

        # Si no mandan fecha, usamos la del sistema
        if not fecha_ref:
            fecha_ref = datetime.now().strftime("%Y-%m-%d")

        if periodo == "DIA": periodo = "HOY"

        conexion, cursor = self._conectar()
        
        # Estructuras base
        etiquetas = []
        mapa_dinero = {}
        mapa_viajes = {}
        mapa_horas = {}

        # --- DEFINIR FILTROS DINÁMICOS CON LA FECHA ---
        if periodo == "HOY":
            # Rango: 00 a 23 horas del día seleccionado
            etiquetas = [f"{h:02d}:00" for h in range(24)]
            # OJO AQUÍ: Usamos fecha_ref en lugar de 'now'
            filtro_fecha = f"WHERE taxi_id = ? AND date(fecha_hora_inicio) = '{fecha_ref}'"
            col_group = "strftime('%H', fecha_hora_inicio)"
            
            filtro_turnos = f"WHERE taxi_id = ? AND date(fecha_inicio) = '{fecha_ref}'"
            col_group_turnos = "strftime('%H', fecha_inicio)"

        elif periodo == "MES":
            # Rango: Días del mes seleccionado
            # Truco: Averiguamos cuántos días tiene ESE mes específico
            anio = int(fecha_ref[:4])
            mes = int(fecha_ref[5:7])
            dias_mes = calendar.monthrange(anio, mes)[1]
            
            etiquetas = [str(d) for d in range(1, dias_mes + 1)]
            
            # Filtramos por el YYYY-MM de la fecha seleccionada
            mes_ref = fecha_ref[:7]
            filtro_fecha = f"WHERE taxi_id = ? AND strftime('%Y-%m', fecha_hora_inicio) = '{mes_ref}'"
            col_group = "strftime('%d', fecha_hora_inicio)"
            
            filtro_turnos = f"WHERE taxi_id = ? AND strftime('%Y-%m', fecha_inicio) = '{mes_ref}'"
            col_group_turnos = "strftime('%d', fecha_inicio)"

        elif periodo == "ANIO":
            # Rango: Meses del año seleccionado
            etiquetas = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            
            anio_ref = fecha_ref[:4]
            filtro_fecha = f"WHERE taxi_id = ? AND strftime('%Y', fecha_hora_inicio) = '{anio_ref}'"
            col_group = "strftime('%m', fecha_hora_inicio)"
            
            filtro_turnos = f"WHERE taxi_id = ? AND strftime('%Y', fecha_inicio) = '{anio_ref}'"
            col_group_turnos = "strftime('%m', fecha_inicio)"
        
        else: 
            # Caso SIEMPRE (Respaldo)
            datos_viejos = self.obtener_datos_grafica(taxi_id)
            conexion.close()
            return {
                "etiquetas": datos_viejos.get("fechas", []),
                "dinero": datos_viejos.get("dinero", []),
                "viajes": datos_viejos.get("viajes", []),
                "horas": datos_viejos.get("horas", [])
            }

        # --- EJECUCIÓN (Igual que antes) ---
        sql_viajes = f"""
            SELECT {col_group} as eje_x, SUM(precio) as total, COUNT(*) as viajes
            FROM viajes 
            {filtro_fecha}
            GROUP BY eje_x
        """
        cursor.execute(sql_viajes, (taxi_id,))
        for fila in cursor.fetchall():
            clave = fila['eje_x']
            if periodo in ["MES", "ANIO"]: clave = str(int(clave)) 
            if periodo == "ANIO": clave = etiquetas[int(clave)-1]
            if periodo == "HOY": clave = f"{clave}:00"
            mapa_dinero[clave] = fila['total']
            mapa_viajes[clave] = fila['viajes']

        sql_horas = f"""
            SELECT {col_group_turnos} as eje_x, 
            SUM((julianday(fecha_fin) - julianday(fecha_inicio)) * 24) as horas
            FROM turnos_trabajo 
            {filtro_turnos} AND fecha_fin IS NOT NULL
            GROUP BY eje_x
        """
        cursor.execute(sql_horas, (taxi_id,))
        for fila in cursor.fetchall():
            clave = fila['eje_x']
            if periodo in ["MES", "ANIO"]: clave = str(int(clave))
            if periodo == "ANIO": clave = etiquetas[int(clave)-1]
            if periodo == "HOY": clave = f"{clave}:00"
            mapa_horas[clave] = fila['horas']

        conexion.close()

        # Rellenar datos
        data_dinero = [mapa_dinero.get(e, 0) for e in etiquetas]
        data_viajes = [mapa_viajes.get(e, 0) for e in etiquetas]
        data_horas  = [mapa_horas.get(e, 0) for e in etiquetas]

        return {"etiquetas": etiquetas, "dinero": data_dinero, "viajes": data_viajes, "horas": data_horas}

    # ==========================================
    # 6. GESTIÓN DE BASES
    # ==========================================

    def obtener_bases_fisicas(self):
        """ Retorna solo las bases reales (excluye 12=Fuera y 13=Viaje) """
        # Asumimos que 12 y 13 son las especiales.
        sql = "SELECT id, nombre_base FROM cat_bases WHERE id NOT IN (12, 13) ORDER BY id ASC"
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql)
            res = cursor.fetchall()
            conexion.close()
            # Convertimos a lista de tuplas [(1, 'Cessa'), (2, 'Licuor')...] para que sea compatible
            return [(fila['id'], fila['nombre_base']) for fila in res]
        except Exception as e:
            print("Error obteniendo bases:", e)
            return []

    def registrar_nueva_base(self, nombre_base):
        try:
            conexion, cursor = self._conectar()
            cursor.execute("INSERT INTO cat_bases (nombre_base) VALUES (?)", (nombre_base,))
            conexion.commit()
            conexion.close()
            return True
        except Exception as e:
            print("Error al crear base:", e)
            return False

    def eliminar_base_fisica(self, id_base):
        """ 
        Elimina la base. 
        OJO: Si hay taxis ahí, los mandamos a 'Fuera de Servicio' (12) para que no queden en el limbo.
        """
        try:
            conexion, cursor = self._conectar()
            
            # 1. Rescatar taxis: Si están en esa base, moverlos a Fuera de Servicio (12)
            cursor.execute("UPDATE taxis SET base_actual_id = 12 WHERE base_actual_id = ?", (id_base,))
            
            # 2. Borrar la base
            cursor.execute("DELETE FROM cat_bases WHERE id = ?", (id_base,))
            
            conexion.commit()
            conexion.close()
            return True
        except Exception as e:
            print("Error al eliminar base:", e)
            return False

    def obtener_ranking_bases(self, filtro="SIEMPRE"):
        """ Retorna ranking filtrado por tiempo """
        # Base de la consulta: Ignoramos 12 y 13
        sql_base = """
            SELECT b.nombre_base, COUNT(v.id) as total
            FROM viajes v
            JOIN cat_bases b ON v.base_salida_id = b.id
            WHERE b.id NOT IN (12, 13)
        """
        
        # Agregamos el filtro de fecha
        filtro_sql = ""
        if filtro == "HOY":
            filtro_sql = " AND date(v.fecha_hora_inicio) = date('now', 'localtime')"
        elif filtro == "MES":
            filtro_sql = " AND strftime('%Y-%m', v.fecha_hora_inicio) = strftime('%Y-%m', 'now', 'localtime')"
        elif filtro == "ANIO":
            filtro_sql = " AND strftime('%Y', v.fecha_hora_inicio) = strftime('%Y', 'now', 'localtime')"
        
        # Armamos la consulta final
        sql_final = f"{sql_base} {filtro_sql} GROUP BY b.nombre_base ORDER BY total DESC LIMIT 10"

        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql_final)
            datos = cursor.fetchall()
            conexion.close()
            
            nombres = [d['nombre_base'] for d in datos]
            viajes = [d['total'] for d in datos]
            return nombres, viajes
        except Exception as e:
            print("Error ranking bases:", e)
            return [], []
        

    def obtener_datos_reporte_global(self, periodo, fecha_ref=None):
        """ Extrae TODA la info: Totales, Bases, Tops y Horas Pico """
        from datetime import datetime
        
        if not fecha_ref: fecha_ref = datetime.now().strftime("%Y-%m-%d")
        
        conexion, cursor = self._conectar()
        
        # 1. PREPARAR FILTROS
        filtro = ""
        filtro_turnos = "" # Filtro especial para tabla de turnos
        
        if periodo == "DIA":
            filtro = f"AND date(fecha_hora_inicio) = '{fecha_ref}'"
            filtro_turnos = f"AND date(fecha_inicio) = '{fecha_ref}'"
        elif periodo == "MES":
            filtro = f"AND strftime('%Y-%m', fecha_hora_inicio) = '{fecha_ref[:7]}'"
            filtro_turnos = f"AND strftime('%Y-%m', fecha_inicio) = '{fecha_ref[:7]}'"
        elif periodo == "ANIO":
            filtro = f"AND strftime('%Y', fecha_hora_inicio) = '{fecha_ref[:4]}'"
            filtro_turnos = f"AND strftime('%Y', fecha_inicio) = '{fecha_ref[:4]}'"

        # --- A. TOTALES GENERALES ---
        cursor.execute(f"SELECT count(*), sum(precio) FROM viajes WHERE 1=1 {filtro}")
        res_tot = cursor.fetchone()
        totales = {
            "viajes": res_tot[0] if res_tot[0] else 0,
            "ganancia": res_tot[1] if res_tot[1] else 0.0
        }

        # --- B. BASES MÁS POPULARES (Top 5) ---
        sql_bases = f"""
            SELECT b.nombre_base, count(*) as num
            FROM viajes v JOIN cat_bases b ON v.base_salida_id = b.id
            WHERE b.id NOT IN (12, 13) {filtro}
            GROUP BY b.nombre_base ORDER BY num DESC LIMIT 5
        """
        cursor.execute(sql_bases)
        top_bases = cursor.fetchall()

        # --- C. TOP 3 UNIDADES: INGRESOS ($) ---
        sql_top_dinero = f"""
            SELECT t.numero_economico, sum(v.precio) as total
            FROM viajes v JOIN taxis t ON v.taxi_id = t.id
            WHERE 1=1 {filtro} GROUP BY t.numero_economico ORDER BY total DESC LIMIT 3
        """
        cursor.execute(sql_top_dinero)
        top_dinero = cursor.fetchall()

        # --- D. TOP 3 UNIDADES: VIAJES (Cantidad) ---
        sql_top_viajes = f"""
            SELECT t.numero_economico, count(*) as total
            FROM viajes v JOIN taxis t ON v.taxi_id = t.id
            WHERE 1=1 {filtro} GROUP BY t.numero_economico ORDER BY total DESC LIMIT 3
        """
        cursor.execute(sql_top_viajes)
        top_viajes = cursor.fetchall()

        # --- E. TOP 3 UNIDADES: HORAS TRABAJADAS (CORREGIDO) ---
        # Antes decía 't.numero_economico' (Error), ahora dice 'tx.numero_economico' (Correcto)
        sql_top_horas = f"""
            SELECT tx.numero_economico, sum((julianday(fecha_fin) - julianday(fecha_inicio)) * 24) as horas
            FROM turnos_trabajo t JOIN taxis tx ON t.taxi_id = tx.id
            WHERE t.fecha_fin IS NOT NULL {filtro_turnos}
            GROUP BY tx.numero_economico ORDER BY horas DESC LIMIT 3
        """
        cursor.execute(sql_top_horas)
        top_horas_trabajadas = cursor.fetchall()

        # --- F. HORAS PICO (Distribución por hora del día) ---
        sql_pico = f"""
            SELECT strftime('%H', fecha_hora_inicio) as hr, count(*) 
            FROM viajes WHERE 1=1 {filtro} GROUP BY hr
        """
        cursor.execute(sql_pico)
        # Rellenamos las 24 horas para que el gráfico no tenga huecos
        mapa_horas = {f"{h:02d}": 0 for h in range(24)}
        for r in cursor.fetchall():
            mapa_horas[r[0]] = r[1]
            
        horas_pico = list(mapa_horas.items()) # Lista de tuplas [('00', 5), ('01', 2)...]

        conexion.close()
        
        return {
            "totales": totales,
            "bases": top_bases,
            "top_dinero": top_dinero,
            "top_viajes": top_viajes,
            "top_horas": top_horas_trabajadas,
            "horas_pico": horas_pico
        }
        """ Extrae TODA la info para el reporte ejecutivo de la empresa """
        from datetime import datetime
        import calendar

        if not fecha_ref: fecha_ref = datetime.now().strftime("%Y-%m-%d")
        
        conexion, cursor = self._conectar()
        
        # 1. PREPARAR FILTROS (Igual que siempre)
        filtro = ""
        if periodo == "DIA":
            filtro = f"AND date(fecha_hora_inicio) = '{fecha_ref}'"
        elif periodo == "MES":
            filtro = f"AND strftime('%Y-%m', fecha_hora_inicio) = '{fecha_ref[:7]}'"
        elif periodo == "ANIO":
            filtro = f"AND strftime('%Y', fecha_hora_inicio) = '{fecha_ref[:4]}'"

        # 2. TOTALES GENERALES (Dinero y Viajes)
        sql_totales = f"SELECT count(*), sum(precio) FROM viajes WHERE 1=1 {filtro}"
        cursor.execute(sql_totales)
        res_tot = cursor.fetchone()
        totales = {
            "viajes": res_tot[0] if res_tot[0] else 0,
            "ganancia": res_tot[1] if res_tot[1] else 0.0
        }

        # 3. TOP 5 BASES (Aquí metemos el reporte de bases)
        # Ignoramos base 12 (Fuera servicio) y 13 (Calle)
        sql_bases = f"""
            SELECT b.nombre_base, count(*) as num_viajes
            FROM viajes v
            JOIN cat_bases b ON v.base_salida_id = b.id
            WHERE b.id NOT IN (12, 13) {filtro}
            GROUP BY b.nombre_base
            ORDER BY num_viajes DESC
            LIMIT 5
        """
        cursor.execute(sql_bases)
        top_bases = cursor.fetchall() # Lista de tuplas (Nombre, Cantidad)

        # 4. TOP 5 CONDUCTORES (Por dinero generado)
        sql_taxis = f"""
            SELECT t.numero_economico, sum(v.precio) as dinero
            FROM viajes v
            JOIN taxis t ON v.taxi_id = t.id
            WHERE 1=1 {filtro}
            GROUP BY t.numero_economico
            ORDER BY dinero DESC
            LIMIT 5
        """
        cursor.execute(sql_taxis)
        top_taxis = cursor.fetchall()

        conexion.close()
        
        return {
            "totales": totales,
            "bases": top_bases,
            "taxis": top_taxis
        }


        """ Trae el detalle de viajes para el reporte PDF """
        sql = """
            SELECT 
                v.fecha_hora_inicio, 
                v.tipo_servicio_id, 
                b.nombre_base, 
                v.destino, 
                v.precio
            FROM viajes v
            LEFT JOIN cat_bases b ON v.base_salida_id = b.id
            WHERE v.taxi_id = ?
        """
        # Filtros de fecha (Igual que en tus gráficas)
        clausula = ""
        if periodo == "HOY":
            clausula = " AND date(v.fecha_hora_inicio) = date('now', 'localtime')"
        elif periodo == "MES":
            clausula = " AND strftime('%Y-%m', v.fecha_hora_inicio) = strftime('%Y-%m', 'now', 'localtime')"
        elif periodo == "ANIO":
            clausula = " AND strftime('%Y', v.fecha_hora_inicio) = strftime('%Y', 'now', 'localtime')"
            
        sql_final = f"{sql} {clausula} ORDER BY v.fecha_hora_inicio DESC"
        
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql_final, (taxi_id,))
            res = cursor.fetchall()
            conexion.close()
            
            # Formateamos bonito para el PDF
            mapa_servicios = {1: "Base", 2: "Tel. Base", 3: "Tel. Unidad", 4: "Aéreo"}
            lista_procesada = []
            
            for r in res:
                id_serv = r['tipo_servicio_id']
                concepto = mapa_servicios.get(id_serv, "Viaje")
                origen = r['nombre_base'] if r['nombre_base'] else "////"
                
                lista_procesada.append({
                    "fecha_hora_inicio": r['fecha_hora_inicio'],
                    "concepto": concepto,
                    "origen": origen,
                    "destino": r['destino'],
                    "precio": r['precio']
                })
            return lista_procesada
        except Exception as e:
            print("Error viajes unidad:", e)
            return []