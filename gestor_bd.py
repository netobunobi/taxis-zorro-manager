import sqlite3
import os

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
        """
        Devuelve la lista de taxis que están trabajando (ACTIVOS).
        Sirve para pintar las fichas en el tablero.
        """
        sql = """
            SELECT 
                t.id, 
                t.numero_economico, 
                e.descripcion as estado_texto,
                t.estado_actual_id
            FROM taxis t
            JOIN cat_estados e ON t.estado_actual_id = e.id
            WHERE t.estado_sistema = 'ACTIVO'
        """
        try:
            conexion, cursor = self._conectar()
            cursor.execute(sql)
            resultados = cursor.fetchall()
            conexion.close()
            # Convertimos a una lista de diccionarios para usarla fácil
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