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

    def obtener_historial_viajes(self, taxi_id=None, fecha=None):
        """
        Devuelve la lista de viajes. 
        Puede filtrar por taxi, por fecha, o traer todo si los dejas vacíos.
        """
        sql = """
            SELECT v.id, v.destino, v.precio, v.fecha_hora_inicio, t.numero_economico
            FROM viajes v
            JOIN taxis t ON v.taxi_id = t.id
            WHERE 1=1 
        """
        params = []
        
        if taxi_id:
            sql += " AND v.taxi_id = ?"
            params.append(taxi_id)
        if fecha:
            sql += " AND v.fecha_hora_inicio LIKE ?"
            params.append(f"{fecha}%")
            
        sql += " ORDER BY v.fecha_hora_inicio DESC"

        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, tuple(params))
            filas = cursor.fetchall()
            conexion.close()
            return [dict(f) for f in filas]
        except Exception as e:
            print("Error al obtener historial:", e)
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
        """Mueve un taxi de una base a otra (o a Taller/Viaje)."""
        sql = "UPDATE taxis SET base_actual_id = ? WHERE id = ?"
        datos = (base_actual_id, taxi_id)
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, datos)
            conexion.commit()
            conexion.close()
            return True
        except Exception as error:
            print("ERROR al mover taxi:", error)
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
        """Abre un turno de trabajo."""
        fecha_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = "INSERT INTO turnos_trabajo (taxi_id, fecha_inicio, fecha_fin) VALUES (?,?,?)"
        datos = (taxi_id, fecha_inicio, None)

        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql, datos)
            conexion.commit()
            conexion.close()
            print(f"🕒 Turno abierto para taxi {taxi_id}")
            return True
        except Exception as error:
            print("Error al abrir turno:", error)
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