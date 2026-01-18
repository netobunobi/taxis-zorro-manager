import sqlite3

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