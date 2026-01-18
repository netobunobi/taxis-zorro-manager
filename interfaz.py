import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QLineEdit, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QListWidget, QPushButton, QListWidgetItem, QDialog
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtCore import Qt
from gestor_db import GestorBaseDatos

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Taxis")
        self.resize(1280, 720)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 1. INICIALIZAMOS TU GESTOR
        self.db = GestorBaseDatos("taxis.db") # Asegúrate que el nombre coincida

        # 2. DICCIONARIO MAESTRO DE LISTAS
        # Aquí guardaremos las referencias: { ID_BASE : WIDGET_LISTA }
        # Así podremos decir: self.listas_bases[5].addItem("T-50")
        self.listas_bases = {} 



        # =======================================================
        # ESTILOS (QSS)
        # =======================================================
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0F172A; 
                color: #E2E8F0;
                font-family: 'Segoe UI', sans-serif;
            }
            QTabWidget::pane {
                border-top: 2px solid #FACC15;
                background-color: #0F172A;
            }
            QTabBar::tab {
                background: #1E293B;
                color: #94A3B8;
                padding: 10px 25px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
                font-weight: bold;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background: #0F172A;
                color: #FACC15;
                border-top: 2px solid #FACC15;
                border-bottom: 2px solid #0F172A;
            }
            QLineEdit {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 5px;
                color: #FACC15;
                padding: 5px 10px;
                font-size: 14px;
                font-weight: bold;
            }
            /* Estilo para las cajas de las bases normales */
            #cajaBase {
                background-color: #1E293B;
                border: 2px dashed #334155;
                border-radius: 10px;
            }
        """)

        tab_tablero = QWidget()
        tab_reportes = QWidget()
        
        self.tabs.addTab(tab_tablero, "TABLERO DE CONTROL")

        # 1. CREACIÓN DE LA PESTAÑA ÚNICA
        self.tabs.addTab(tab_tablero, "TABLERO DE CONTROL")

        # 2. CONFIGURACIÓN DEL BUSCADOR (Esquina superior derecha)
        container_buscador = QWidget()
        layout_corner = QHBoxLayout(container_buscador)
        layout_corner.setContentsMargins(0, 0, 10, 0) # Margen de 10px a la derecha
        
        self.txt_buscar_taxi = QLineEdit()
        self.txt_buscar_taxi.setPlaceholderText("🔍 Buscar unidad...")
        self.txt_buscar_taxi.setFixedWidth(200)
        self.txt_buscar_taxi.setStyleSheet("""
            QLineEdit {
                background-color: #1E293B;
                border: 2px solid #00D1FF;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            }
        """)
        self.txt_buscar_taxi.textChanged.connect(self.filtrar_taxis_tablero)
        layout_corner.addWidget(self.txt_buscar_taxi)
        
        # Esto lo pega a las pestañas sin crear una nueva
        self.tabs.setCornerWidget(container_buscador, Qt.Corner.TopRightCorner)

        # 3. LAYOUT DEL TABLERO (El que usan tus líneas 226/227)
        layout_tablero = QHBoxLayout(tab_tablero)
        layout_tablero.setContentsMargins(10, 10, 10, 10)
        layout_tablero.setSpacing(10)


        # --- ZONA IZQUIERDA: BASES FÍSICAS ---
        zona_bases = QWidget()
        self.grid_bases = QGridLayout(zona_bases) 
        self.grid_bases.setSpacing(10) # Espacio entre cuadritos
        
        # LLAMAMOS A LA FUNCIÓN QUE CREA LAS CAJAS AUTOMÁTICAMENTE
        self.generar_bases_fisicas()

        # ------------------------------------------
        # 2. DERECHA: BARRA LATERAL (ESTADOS ESPECIALES)
        # ------------------------------------------
        zona_derecha = QWidget()
        zona_derecha.setFixedWidth(280) 
        layout_derecha = QVBoxLayout(zona_derecha)
        layout_derecha.setContentsMargins(0, 0, 0, 0)
        layout_derecha.setSpacing(15)

        # === CAJA VERDE: EN VIAJE (ID 13 en tu BD) ===
        caja_viaje = QWidget()
        caja_viaje.setStyleSheet("""
            background-color: #064E3B; 
            border-radius: 10px;
            border: 2px solid #10B981;
        """)
        vbox_viaje = QVBoxLayout(caja_viaje)
        vbox_viaje.setContentsMargins(5,5,5,5)

        lbl_viaje = QLabel("🚖 EN VIAJE / OCUPADOS")
        lbl_viaje.setStyleSheet("color: #34D399; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        lbl_viaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox_viaje.addWidget(lbl_viaje)

        # CREAMOS LA LISTA VISUAL PARA VIAJES
        self.lista_viajes = QListWidget()
        self.lista_viajes.setObjectName("lista_viajes")
        self.lista_viajes.setDragEnabled(True)
        self.lista_viajes.setAcceptDrops(True)
        self.lista_viajes.setDefaultDropAction(Qt.DropAction.MoveAction)

        self.lista_viajes.model().rowsInserted.connect(
            lambda: self.detectar_cambio_base(self.lista_viajes)
        )
        
        self.lista_viajes.setStyleSheet("""
            QListWidget { background: transparent; border: none; }
            QListWidget::item { 
                background-color: #065F46; color: white; border-bottom: 1px solid #10B981; 
                padding: 5px; font-weight: bold; font-size: 14px;
            }
        """)
        vbox_viaje.addWidget(self.lista_viajes)

        # ¡IMPORTANTE! REGISTRAMOS EL ID 13 EN EL DICCIONARIO
        # Así cuando la BD diga "Taxi en base 13", el programa sabe que va aquí.
        
        self.listas_bases[13] = self.lista_viajes 


        # === CAJA ROJA: FUERA DE SERVICIO (ID 12) Y TALLER (ID 14) ===
        caja_taller = QWidget()
        caja_taller.setStyleSheet("""
            background-color: #450A0A; 
            border-radius: 10px;
            border: 2px solid #EF4444;
        """)
        vbox_taller = QVBoxLayout(caja_taller)
        vbox_taller.setContentsMargins(5,5,5,5)

        lbl_taller = QLabel("⛔ FUERA DE SERVICIO")
        lbl_taller.setStyleSheet("color: #F87171; font-weight: bold; font-size: 16px; border: none; background: transparent;")
        lbl_taller.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox_taller.addWidget(lbl_taller)

        # CREAMOS LA LISTA VISUAL PARA TALLER
        self.lista_taller = QListWidget()
        self.lista_taller.setObjectName("lista_taller")
        self.lista_taller.setDragEnabled(True)
        self.lista_taller.setAcceptDrops(True)
        self.lista_taller.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.lista_taller.model().rowsInserted.connect(
            lambda: self.detectar_cambio_base(self.lista_taller)
        )
        self.lista_taller.setStyleSheet("""
            QListWidget { background: transparent; border: none; }
            QListWidget::item { 
                background-color: #7F1D1D; color: #FECACA; border-bottom: 1px solid #EF4444; 
                padding: 5px; font-weight: bold; font-size: 14px;
            }
        """)
        vbox_taller.addWidget(self.lista_taller)

        # ¡IMPORTANTE! REGISTRAMOS LOS IDs 12 y 14 AQUÍ
        # Redirigimos ambos estados a la misma caja roja
        self.listas_bases[12] = self.lista_taller 
        self.listas_bases[14] = self.lista_taller 

        # Agregar las cajas al layout vertical derecho
        layout_derecha.addWidget(caja_viaje, 1) 
        layout_derecha.addWidget(caja_taller, 1)
        
        # Y finalmente, agregamos la zona derecha al tablero principal
        layout_tablero.addWidget(zona_bases, 1)    # Izquierda (Grid)
        layout_tablero.addWidget(zona_derecha, 0)  # Derecha (Panel)

        # ==========================================
        # PESTAÑA 2: ADMINISTRACIÓN (Renombrada)
        # ==========================================
        # 1. Crear los widgets base
        tab_admin = QWidget()
        self.tabs.addTab(tab_admin, "ADMINISTRACIÓN") # Cambio de nombre

        # Layout principal de esta pestaña (Horizontal: Menú | Contenido)
        layout_admin_main = QHBoxLayout(tab_admin)
        layout_admin_main.setContentsMargins(0, 0, 0, 0)
        layout_admin_main.setSpacing(0)

        # ------------------------------------------
        # A. MENÚ LATERAL (Izquierda)
        # ------------------------------------------
        menu_lateral = QWidget()
        menu_lateral.setFixedWidth(200) # Ancho fijo para el menú
        menu_lateral.setStyleSheet("background-color: #0F172A; border-right: 1px solid #334155;")
        
        layout_menu = QVBoxLayout(menu_lateral)
        layout_menu.setContentsMargins(10, 20, 10, 20)
        layout_menu.setSpacing(10)

        # Función auxiliar para crear botones de menú bonitos
        def crear_btn_menu(texto):
            btn = QPushButton(texto)
            btn.setCheckable(True) # Para que se quede "presionado"
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px;
                    border-radius: 5px;
                    color: #94A3B8;
                    font-weight: bold;
                    background: transparent;
                }
                QPushButton:checked {
                    background-color: #1E293B;
                    color: #FACC15;
                    border-left: 3px solid #FACC15;
                }
                QPushButton:hover {
                    background-color: #1E293B;
                    color: white;
                }
            """)
            return btn

        # Creamos los botones del menú
        self.btn_historial = crear_btn_menu("📜 Historial Viajes")
        self.btn_flota     = crear_btn_menu("🚖 Gestión Taxis")
        self.btn_bases     = crear_btn_menu("🏢 Gestión Bases")
        
        # Seleccionamos el primero por defecto
        self.btn_historial.setChecked(True)

        layout_menu.addWidget(self.btn_historial)
        layout_menu.addWidget(self.btn_flota)
        layout_menu.addWidget(self.btn_bases)
        layout_menu.addStretch() # Empuja todo arriba

        # ------------------------------------------
        # B. ZONA DE CONTENIDO (Derecha - Cambiante)
        # ------------------------------------------
        # Usamos QStackedWidget: Es como un libro, solo muestra una página a la vez
        from PyQt6.QtWidgets import QStackedWidget
        self.paginas_admin = QStackedWidget()
        
        # --- PÁGINA 1: HISTORIAL (La tabla que ya teníamos) ---
        page_historial = QWidget()
        self.construir_pagina_historial(page_historial) # Llamamos a función auxiliar
        
        # --- PÁGINA 2: FLOTA (Altas/Bajas Taxis) ---
        page_flota = QWidget()
        lbl_flota = QLabel("AQUÍ IRÁ EL ALTA/BAJA DE TAXIS")
        lbl_flota.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_f = QVBoxLayout(page_flota)
        layout_f.addWidget(lbl_flota)

        # --- PÁGINA 3: BASES (Configuración) ---
        page_bases = QWidget()
        lbl_bases = QLabel("AQUÍ SE CONFIGURAN LAS BASES")
        lbl_bases.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_b = QVBoxLayout(page_bases)
        layout_b.addWidget(lbl_bases)

        # Agregamos las páginas al libro
        self.paginas_admin.addWidget(page_historial) # Índice 0
        self.paginas_admin.addWidget(page_flota)     # Índice 1
        self.paginas_admin.addWidget(page_bases)     # Índice 2

        # ------------------------------------------
        # CONECTAR BOTONES CON PÁGINAS
        # ------------------------------------------
        # Lógica: Si clicas botón 1, muestra página 1, y apaga los otros botones
        self.btn_historial.clicked.connect(lambda: self.cambiar_pagina(0))
        self.btn_flota.clicked.connect(lambda: self.cambiar_pagina(1))
        self.btn_bases.clicked.connect(lambda: self.cambiar_pagina(2))

        # ------------------------------------------
        # ARMADO FINAL
        # ------------------------------------------
        layout_admin_main.addWidget(menu_lateral)
        layout_admin_main.addWidget(self.paginas_admin)

        self.listas_bases[12] = self.lista_taller  # Caja Roja
        self.listas_bases[13] = self.lista_viajes

        self.cargar_datos_en_tablero()

    # =======================================================
    # MÉTODOS AUXILIARES (Para no ensuciar el __init__)
    # =======================================================


    def cambiar_pagina(self, indice):
        """Cambia la página del StackedWidget y actualiza el estilo de los botones"""
        self.paginas_admin.setCurrentIndex(indice)
        
        # Actualizar estado visual de los botones (Solo uno puede estar activo)
        self.btn_historial.setChecked(indice == 0)
        self.btn_flota.setChecked(indice == 1)
        self.btn_bases.setChecked(indice == 2)

    def generar_bases_fisicas(self):
        bases_struct = [
            (1, "Cessa"), (2, "Licuor"), (3, "Santiaguito"), (4, "Aurrera"), (5, "Mercado"),
            (6, "Caros"), (7, "Survi"), (8, "Capulín"), (9, "Zócalo"), (10, "16 de Septiembre"), 
            (11, "Parada Principal")
        ]

        fila = 0
        columna = 0
        max_cols = 5

        for id_base, nombre in bases_struct:
            caja_contenedor = QWidget()
            caja_contenedor.setObjectName("cajaBase") 
            
            layout_caja = QVBoxLayout(caja_contenedor)
            layout_caja.setContentsMargins(2, 2, 2, 2)
            layout_caja.setSpacing(0)
            
            lbl = QLabel(nombre)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #FACC15; font-weight: bold; font-size: 14px; background: transparent;")
            layout_caja.addWidget(lbl)

            lista_taxis = QListWidget()
            lista_taxis.setObjectName(f"lista_base_{id_base}") 
            
            # --- CONFIGURACIÓN DE MOVIMIENTO (AQUÍ VA EL CAMBIO) ---
            lista_taxis.setDragEnabled(True)           # Permite arrastrar desde aquí
            lista_taxis.setAcceptDrops(True)           # Permite soltar aquí
            lista_taxis.setDefaultDropAction(Qt.DropAction.MoveAction) # Mueve el taxi, no lo copia
            lista_taxis.setDragDropMode(QListWidget.DragDropMode.DragDrop)
            lista_taxis.setDefaultDropAction(Qt.DropAction.MoveAction)
            
            # Conectamos el evento para que guarde en la BD al soltar
            lista_taxis.model().rowsInserted.connect(
                lambda index, first, last, w=lista_taxis: self.detectar_cambio_base(w)
            )
            # ------------------------------------------------------

            lista_taxis.setViewMode(QListWidget.ViewMode.IconMode) 
            lista_taxis.setResizeMode(QListWidget.ResizeMode.Adjust)
            # Nota: Quitamos setMovement(Static) para que el drag funcione bien

            lista_taxis.setIconSize(QSize(80, 60)) 
            lista_taxis.setSpacing(5) 

            lista_taxis.setStyleSheet("""
                QListWidget {
                    background-color: transparent;
                    border: none;
                }
                QListWidget::item {
                    background-color: #334155;
                    border: 2px solid #475569;
                    border-radius: 8px;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                }
                QListWidget::item:hover {
                    background-color: #475569;
                    border-color: #FACC15;
                }
                QListWidget::item:selected {
                    background-color: #FACC15; 
                    color: black;
                }
            """)

            self.listas_bases[id_base] = lista_taxis

            layout_caja.addWidget(lista_taxis)
            self.grid_bases.addWidget(caja_contenedor, fila, columna)

            columna += 1
            if columna == max_cols:
                columna = 0
                fila += 1
                

    def busqueda_inteligente(self, texto):
        """
        Función Maestra:
        Detecta en qué pestaña estás y filtra acorde.
        """
        texto = texto.lower().strip() # Convertir a minúsculas para buscar fácil
        indice_actual = self.tabs.currentIndex()

        # CASO 1: ESTAMOS EN REPORTES (Índice 1) -> Filtrar Tabla
        if indice_actual == 1:
            # Recorremos todas las filas de la tabla
            for fila in range(self.tabla.rowCount()):
                mostrar_fila = False
                # Recorremos todas las columnas de esa fila
                for col in range(self.tabla.columnCount()):
                    item = self.tabla.item(fila, col)
                    if item and texto in item.text().lower():
                        mostrar_fila = True
                        break # Ya encontramos coincidencia en esta fila
                
                # Ocultar o Mostrar la fila
                self.tabla.setRowHidden(fila, not mostrar_fila)

        # CASO 2: ESTAMOS EN TABLERO (Índice 0) -> Resaltar Taxi (Lo haremos después)
        elif indice_actual == 0:
            print(f"Buscando taxi {texto} en el tablero...") 
            # Aquí irá el código para iluminar el taxi en el Grid
            
    def cargar_datos_en_tablero(self):
        """
        Versión Final con Fichas Neón Pro y Arrastre Habilitado.
        """
        # 1. LIMPIEZA
        for lista in self.listas_bases.values():
            lista.clear()
            
            # --- ESTILO MEJORADO (Neon Matching) ---
            lista.setStyleSheet("""
                QListWidget {
                    border: 1px solid #1E293B;
                    background-color: rgba(30, 41, 59, 0.5); /* Fondo semi-transparente */
                    border-radius: 10px;
                }
                QListWidget::item {
                    background-color: #B28900; /* Amarillo Oro Obscuro */
                    color: white;
                    border: 2px solid #00D1FF; /* Azul Cian Neón */
                    border-radius: 15px;
                    margin: 5px;
                }
                QListWidget::item:hover {
                    background-color: #D4A017;
                    border: 2px solid #FFFFFF; /* Brillo blanco al pasar */
                }
                QListWidget::item:selected {
                    background-color: #FFD700;
                    color: black;
                }
            """)

            # Configuración para que parezcan botones/fichas (IconMode)
            lista.setViewMode(QListWidget.ViewMode.IconMode)
            lista.setResizeMode(QListWidget.ResizeMode.Adjust)
            lista.setSpacing(12)
            
            # RE-HABILITAR ARRASTRE (Esto es vital)
            lista.setDragEnabled(True)
            lista.setAcceptDrops(True)
            lista.setDefaultDropAction(Qt.DropAction.MoveAction)

        # 2. CONSULTA
        taxis_activos = self.db.obtener_taxis_activos() 
        
        # 3. DISTRIBUCIÓN
        for taxi in taxis_activos:
            numero = str(taxi['numero_economico'])
            id_base = taxi['base_actual_id']

            if id_base in self.listas_bases:
                item = QListWidgetItem(numero)
                
                # --- NÚMERO MÁS GRANDE Y FUENTE ---
                font = item.font()
                font.setPointSize(18) # Aumentamos el tamaño del número
                font.setBold(True)
                item.setFont(font)
                
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Tamaño de la ficha (un poco más grande para que luzca)
                item.setSizeHint(QSize(85, 85))
                
                # Guardamos el ID real
                item.setData(Qt.ItemDataRole.UserRole, taxi['id']) 
                
                self.listas_bases[id_base].addItem(item)

    def detectar_cambio_base(self, lista_destino):
        """ ACTUALIZADA: Ahora llama al cerebro que decide si cobrar o marcar entrada """
        from PyQt6.QtCore import QTimer
        # El retraso es vital para que currentItem() no devuelva None
        QTimer.singleShot(50, lambda: self._ejecutar_actualizacion_bd(lista_destino))

    

    def construir_pagina_historial(self, widget_padre):
        """Esta función crea la tabla de viajes dentro de Administración"""
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QPushButton
        
        layout = QVBoxLayout(widget_padre)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- BARRA SUPERIOR DE LA TABLA ---
        barra = QWidget()
        barra.setStyleSheet("background-color: #1E293B; border-radius: 8px;")
        layout_barra = QHBoxLayout(barra)
        
        combo = QComboBox()
        combo.addItems(["Reporte de Hoy", "Mes Actual"])
        combo.setStyleSheet("background: #0F172A; color: white; padding: 5px;")
        
        btn_pdf = QPushButton("🖨️ PDF")
        btn_pdf.setStyleSheet("""
            QPushButton { background-color: #FACC15; color: black; font-weight: bold; padding: 5px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #EAB308; }
        """)

        layout_barra.addWidget(QLabel("📅 Filtro:"))
        layout_barra.addWidget(combo)
        layout_barra.addStretch()
        layout_barra.addWidget(btn_pdf)

        # --- LA TABLA TIPO EXCEL ---
        self.tabla_reportes = QTableWidget()
        cols = ["ID", "FECHA", "HORA", "UNIDAD", "BASE", "DESTINO", "COSTO"]
        self.tabla_reportes.setColumnCount(len(cols))
        self.tabla_reportes.setHorizontalHeaderLabels(cols)
        self.tabla_reportes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Estilo oscuro para la tabla
        self.tabla_reportes.setStyleSheet("""
            QTableWidget { background-color: #1E293B; color: white; border: none; gridline-color: #334155; }
            QHeaderView::section { background-color: #0F172A; color: #FACC15; padding: 5px; font-weight: bold; }
        """)
        
        layout.addWidget(barra)
        layout.addWidget(self.tabla_reportes)

    def cambiar_pagina(self, indice):
        """Cambia entre Historial, Gestión de Taxis y Gestión de Bases"""
        self.paginas_admin.setCurrentIndex(indice)
        # Actualizamos qué botón se ve presionado
        self.btn_historial.setChecked(indice == 0)
        self.btn_flota.setChecked(indice == 1)
        self.btn_bases.setChecked(indice == 2)


    def _ejecutar_actualizacion_bd(self, lista_destino):
            count = lista_destino.count()
            if count == 0: return
            item = lista_destino.item(count - 1)
            if not item: return

            taxi_id_bd = item.data(Qt.ItemDataRole.UserRole)
            taxi_num = item.text()
            
            # 1. Identificar ID de la base de destino
            id_base_nueva = None
            for id_b, widget in self.listas_bases.items():
                if widget == lista_destino:
                    id_base_nueva = id_b
                    break

            if id_base_nueva and taxi_id_bd:
                # --- 2. CONSULTAR ESTADO ANTERIOR (De dónde venía) ---
                # Esto es vital para saber si iniciamos turno al ir directo a viaje
                conexion, cursor = self.db._conectar()
                cursor.execute("SELECT base_actual_id FROM taxis WHERE id = ?", (taxi_id_bd,))
                res = cursor.fetchone()
                id_base_anterior = res['base_actual_id'] if res else None
                conexion.close()

                # --- 3. LÓGICA DE NEGOCIO SEGÚN DESTINO ---
                
                if id_base_nueva == 13: # DESTINO: EN VIAJE
                    # Si venía de Fuera de Servicio (12), abrimos turno primero
                    if id_base_anterior == 12:
                        self.db.hora_entrada(taxi_id_bd)
                        print(f"☀️ Turno iniciado (salida directa a viaje): {taxi_num}")
                    
                    # Abrimos la ventana que ya arreglamos (la de QDialog.DialogCode.Accepted)
                    self.abrir_ventana_nuevo_viaje(taxi_id_bd, taxi_num)

                elif id_base_nueva == 12: # DESTINO: FUERA DE SERVICIO
                    self.db.hora_salida(taxi_id_bd)
                    # Por si venía de un viaje y lo mandaron directo a taller
                    self.db.registrar_fin_viaje(taxi_id_bd)

                elif id_base_nueva <= 11: # DESTINO: BASES NORMALES
                    # Si venía de Fuera de Servicio, iniciamos turno
                    if id_base_anterior == 12:
                        self.db.hora_entrada(taxi_id_bd)
                    
                    # Si venía de Viaje, cerramos el viaje
                    self.db.registrar_fin_viaje(taxi_id_bd)

                # --- 4. PERSISTENCIA FINAL (Actualiza la tabla 'taxis') ---
                # Esta línea se ejecuta siempre al final para que el cambio sea permanente
                self.db.actualizar_taxi_base(taxi_id_bd, id_base_nueva)
                
                print(f"✅ Sincronizado: {taxi_num} (De {id_base_anterior} a {id_base_nueva})")



    def abrir_ventana_nuevo_viaje(self, taxi_id, taxi_num):
        """ NUEVA: Ventana emergente para capturar datos del viaje al mover a zona verde """
        from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout
        
        dialogo = QDialog(self)
        dialogo.setWindowTitle(f"🚕 Registrar Viaje - Taxi {taxi_num}")
        dialogo.setMinimumWidth(300)
        dialogo.setStyleSheet("""
            QDialog { background-color: #1E293B; }
            QLabel { color: #FACC15; font-weight: bold; }
            QLineEdit { background-color: #0F172A; color: white; border: 1px solid #334155; padding: 5px; }
        """)
        
        layout = QVBoxLayout(dialogo)
        formulario = QFormLayout()
        
        # Guardamos como self para leerlos abajo
        self.txt_destino = QLineEdit()
        self.txt_costo = QLineEdit()
        self.txt_costo.setPlaceholderText("0.00")
        
        formulario.addRow("📍 Destino:", self.txt_destino)
        formulario.addRow("💰 Costo $:", self.txt_costo)
        
        layout.addLayout(formulario)
        
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        layout.addWidget(botones)

        # CORRECCIÓN AQUÍ: Se agrega .DialogCode.
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            destino = self.txt_destino.text()
            costo_str = self.txt_costo.text().replace(',', '.')
            
            try:
                costo = float(costo_str) if costo_str else 0.0
            except ValueError:
                costo = 0.0 
            
            # 1. Registrar el viaje en la BD
            self.db.registrar_viaje(taxi_id, 1, 13, destino, costo) 
            # 2. Actualizar su posición visual y en tabla taxis
            self.db.actualizar_taxi_base(taxi_id, 13) 
            print(f"✅ Viaje guardado: Taxi {taxi_num} a {destino}")
        else:
            # SI CANCELA: Refrescamos el tablero para que el taxi regrese a su base original
            self.cargar_datos_en_tablero()


    def filtrar_taxis_tablero(self, texto):
        """Filtra los taxis por número económico"""
        busqueda = texto.lower().strip()
        for lista in self.listas_bases.values():
            for i in range(lista.count()):
                item = lista.item(i)
                if not busqueda or busqueda in item.text().lower():
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    



    
   


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.showMaximized()
    sys.exit(app.exec())