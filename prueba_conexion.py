import sqlite3

def ver_columnas_reales():
    conexion = sqlite3.connect("taxis.db")
    cursor = conexion.cursor()
    
    # Le preguntamos a la base de datos: "¿Qué columnas tiene la tabla viajes?"
    cursor.execute("PRAGMA table_info(viajes)")
    columnas = cursor.fetchall()
    
    print("--- LA VERDAD SOBRE LA TABLA 'VIAJES' ---")
    if not columnas:
        print("❌ La tabla no existe.")
    else:
        for col in columnas:
            # col[1] es el nombre de la columna
            print(f"✅ Columna encontrada: {col[1]}")

    conexion.close()

if __name__ == "__main__":
    ver_columnas_reales()