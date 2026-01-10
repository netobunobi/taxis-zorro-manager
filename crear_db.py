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
    CREATE TABLE IF NOT EXISTS cat_estados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT UNIQUE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cat_tipos_servicio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT UNIQUE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cat_bases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_base TEXT UNIQUE NOT NULL
    );
    """)

    # --- Tablas Principales ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS taxis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_economico TEXT NOT NULL,
        estado_sistema TEXT DEFAULT 'ACTIVO',
        fecha_alta TEXT,
        fecha_baja TEXT,
        estado_actual_id INTEGER DEFAULT 1, 
        FOREIGN KEY(estado_actual_id) REFERENCES cat_estados(id)
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
    # 2. CARGA DE DATOS REALES (SEGÚN IMÁGENES)
    # ==========================================
    
    print("Cargando catálogos del sitio...")

    # A. ESTADOS (Estos son fijos para tu lógica interna)
    datos_estados = [
        (1, 'Fuera de Servicio'), 
        (2, 'En Base'), 
        (3, 'En Viaje'), 
        (4, 'Taller') # Opcional si lo usas
    ]
    cursor.executemany("INSERT OR IGNORE INTO cat_estados (id, descripcion) VALUES (?, ?)", datos_estados)

    # B. TIPOS DE SERVICIO (Datos de la imagen de salida)
    # Nota: Respeté el orden numérico de tu imagen.
    datos_servicios = [
        (1, 'Viaje en base'), 
        (2, 'Telefono base'), 
        (3, 'Telefono unidad'), 
        (4, 'Viaje aereo')
    ]
    cursor.executemany("INSERT OR IGNORE INTO cat_tipos_servicio (id, descripcion) VALUES (?, ?)", datos_servicios)

    # C. BASES (Datos de la lista de bases)
    # He corregido mayúsculas para que se vea profesional (ej: "cessa" -> "Cessa")
    datos_bases = [
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
        (11, 'Parada principal')
    ]
    cursor.executemany("INSERT OR IGNORE INTO cat_bases (id, nombre_base) VALUES (?, ?)", datos_bases)

    # ==========================================
    # 3. UNIDAD DE PRUEBA
    # ==========================================

    # Creamos la Unidad 80 (Si no existe ya)
    cursor.execute("SELECT count(*) FROM taxis WHERE numero_economico = '80'")
    if cursor.fetchone()[0] == 0:
        print("Creando unidad de prueba: 80...")
        # Nace "Fuera de Servicio" (ID 1) y "ACTIVO"
        cursor.execute("""
            INSERT INTO taxis (numero_economico, estado_sistema, estado_actual_id) 
            VALUES ('80', 'ACTIVO', 1)
        """)

    conexion.commit()
    conexion.close()
    
    print("¡Base de datos actualizada con la información de las imágenes!")

if __name__ == "__main__":
    crear_base_datos()