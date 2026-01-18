import sqlite3

def crear_base_datos():
    nombre_db = "taxis.db"
    conexion = sqlite3.connect(nombre_db)
    cursor = conexion.cursor()

    # ACTIVAR LLAVES FORÁNEAS
    cursor.execute("PRAGMA foreign_keys = ON;")

    print(f"Creando tablas maestras en {nombre_db}...")

    # ==========================================
    # 1. ESTRUCTURA (TABLAS)
    # ==========================================

    # --- Catálogos ---

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cat_tipos_servicio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT UNIQUE NOT NULL
    );
    """)

    # NOTA: Aquí están TODAS las ubicaciones (Reales y Virtuales)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cat_bases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_base TEXT UNIQUE NOT NULL
    );
    """)

    # --- Tablas Principales ---
    # CAMBIO IMPORTANTE: Eliminé 'estado_actual_id'. 
    # Ahora solo usamos 'base_actual_id' para saber dónde está (Cessa, Taller, Viaje, etc.)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS taxis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_economico TEXT NOT NULL,
        estado_sistema TEXT DEFAULT 'ACTIVO', -- Para bajas lógicas (borrado suave)
        fecha_alta TEXT,
        fecha_baja TEXT,
        
        base_actual_id INTEGER DEFAULT 12, -- Por defecto nace en 'Fuera de Servicio' (ID 12)
        
        FOREIGN KEY(base_actual_id) REFERENCES cat_bases(id)
    );
    """)

    cursor.execute("""
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
        FOREIGN KEY(tipo_servicio_id) REFERENCES cat_tipos_servicio(id),
        FOREIGN KEY(base_salida_id) REFERENCES cat_bases(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS turnos_trabajo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        taxi_id INTEGER NOT NULL,
        fecha_inicio TEXT,
        fecha_fin TEXT,
        FOREIGN KEY(taxi_id) REFERENCES taxis(id)
    );
    """)

    # ==========================================
    # 2. CARGA DE DATOS 
    # ==========================================
    
    print("Cargando catálogos...")

    # A. TIPOS DE SERVICIO
    datos_servicios = [
        (1, 'Viaje en base'), 
        (2, 'Telefono base'), 
        (3, 'Telefono unidad'), 
        (4, 'Viaje aereo')
    ]
    cursor.executemany("INSERT OR IGNORE INTO cat_tipos_servicio (id, descripcion) VALUES (?, ?)", datos_servicios)

    # B. BASES UNIFICADAS (Lugares físicos + Estados virtuales)
    datos_bases = [
        # --- Bases Físicas ---
        (1, 'Cessa'), 
        (2, 'Licuor'), 
        (3, 'Santiagito'),
        (4, 'Aurrera'),
        (5, 'Mercado'),
        (6, 'Caros'),
        (7, 'Survi'),
        (8, 'Capulin'),
        (9, 'Zocalo'),
        (10, '16 de septiembre'),
        (11, 'Parada principal'),
        
        # --- Ubicaciones Virtuales ---
        (12, 'Fuera de Servicio'),
        (13, 'En Viaje')
    ]
    cursor.executemany("INSERT OR IGNORE INTO cat_bases (id, nombre_base) VALUES (?, ?)", datos_bases)

    # ==========================================
    # 3. UNIDAD DE PRUEBA
    # ==========================================

    # Creamos la Unidad 80
    cursor.execute("SELECT count(*) FROM taxis WHERE numero_economico = '80'")
    if cursor.fetchone()[0] == 0:
        print("Creando unidad de prueba: 80...")
        # Nace con base_actual_id = 12 (Fuera de Servicio)
        cursor.execute("""
            INSERT INTO taxis (numero_economico, estado_sistema, base_actual_id) 
            VALUES ('80', 'ACTIVO', 12)
        """)

    conexion.commit()
    conexion.close()
    
    print("¡Base de datos actualizada correctamente con lógica unificada!")

if __name__ == "__main__":
    crear_base_datos()