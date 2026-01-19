import sys
import traceback
from datetime import datetime

# === CAZADOR DE ERRORES ===
# Esto guardará cualquier fallo en un archivo de texto
def log_excepciones(type, value, tb):
    texto_error = "".join(traceback.format_exception(type, value, tb))
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Escribir el error en "errores_crash.txt"
    with open("errores_crash.txt", "a", encoding="utf-8") as f:
        f.write(f"\n\n--- ERROR REGISTRADO: {fecha} ---\n")
        f.write(texto_error)
        f.write("\n----------------------------------\n")
    
    # Mostrar el error en la consola si existe, o cerrar si es fatal
    sys.__excepthook__(type, value, tb)

# Activamos el cazador
sys.excepthook = log_excepciones

import sys
from PyQt6.QtGui import QFont, QColor # Agrega QFont aquí
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QLineEdit, 
    QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QListWidget, 
    QPushButton, QListWidgetItem, QDialog, QTableWidgetItem, 
    QComboBox, QDateEdit, QMessageBox, QFrame, QHeaderView,
    QLCDNumber
)
from PyQt6.QtCore import Qt, QSize, QDate
from gestor_db import GestorBaseDatos

# ... resto de importaciones (matplotlib, reportes, etc) ...
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from reportes import GeneradorPDF
from PyQt6.QtGui import QFont, QColor, QPixmap # <--- Agrega QPixmap
from PyQt6.QtWidgets import (
    QApplication, QSplashScreen, # <--- Agrega QSplashScreen
    QMainWindow, # ... y el resto que ya tenías
)
import time # Opcional, por si quieres que dure un poquito más a propósito

class LienzoGrafico(FigureCanvas):
    def __init__(self, parent=None, color_fondo='#1E293B'):
        self.fig = Figure(figsize=(4, 3), dpi=80, facecolor='#0F172A') # DPI más bajo para que quepa mejor
        self.axes = self.fig.add_subplot(111)
        self.color_fondo = color_fondo
        self.axes.set_facecolor(self.color_fondo) 
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(self.sizePolicy().Policy.Expanding, self.sizePolicy().Policy.Expanding)

    def actualizar_grafico(self, etiquetas, valores, tipo="dinero"):
        self.axes.clear()
        self.axes.set_facecolor(self.color_fondo)
        
        # CONFIGURACIÓN DE COLORES
        config = {
            "dinero": {"color": "#FACC15", "titulo": "Ingresos"},
            "viajes": {"color": "#10B981", "titulo": "Viajes"},
            "horas":  {"color": "#F472B6", "titulo": "Horas"}
        }
        c = config.get(tipo, config["dinero"])

        if not etiquetas or sum(valores) == 0:
            self.axes.text(0.5, 0.5, "Sin datos", color="#64748B", ha='center', fontsize=10)
            self.axes.set_title(c['titulo'], color='white', fontsize=10, fontweight='bold')
        else:
            # Dibujar Barras
            # width=0.6 hace que las barras sean delgadas y elegantes
            barras = self.axes.bar(etiquetas, valores, color=c["color"], width=0.6)
            
            # Título Minimalista
            self.axes.set_title(c['titulo'], color=c['color'], fontsize=11, fontweight='bold')
            
            # Ejes limpios
            self.axes.tick_params(axis='y', colors='#94A3B8', labelsize=8)
            # ... (código anterior de barras) ...

            # === ESTILO MEJORADO DE EJES (Textos que resaltan) ===
            # Eje X (Nombres): Color Cyan Neón, Negrita y Tamaño 9
            self.axes.tick_params(axis='x', colors='#00D1FF', labelsize=9, labelrotation=15)
            
            # Forzamos que las etiquetas sean negritas (Bold)
            for label in self.axes.get_xticklabels():
                label.set_fontweight('bold')

            # Eje Y (Números): Blanco discreto
            self.axes.tick_params(axis='y', colors='#94A3B8', labelsize=8)
            
            # Solo mostrar línea inferior
            self.axes.spines['top'].set_visible(False)
            self.axes.spines['right'].set_visible(False)
            self.axes.spines['left'].set_visible(False)
            self.axes.spines['bottom'].set_color('#334155')

        self.fig.tight_layout() # Ajuste automático para que no se corten textos
        self.draw()


# CLASE ESPECIAL PARA QUE SE ORDENEN POR NÚMERO
# Esta clase enseña al programa que "100" es mayor que "35"
class TaxiItem(QListWidgetItem):
    def __lt__(self, other):
        try:
            return int(self.text()) < int(other.text())
        except:
            return self.text() < other.text()

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
        # Ahora conectamos al cerebro unificado, no solo al tablero
        self.txt_buscar_taxi.textChanged.connect(self.busqueda_unificada)
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
            lambda parent, first, last: self.detectar_cambio_base(self.lista_viajes, first)
        )

        self.lista_viajes.model().rowsMoved.connect(
            lambda parent, start, end, dest, row: self.detectar_cambio_base(self.lista_viajes, row)
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
        # === AGREGA ESTA LÍNEA MÁGICA ===
        # Reemplazamos el comportamiento normal por nuestro truco
        self.lista_viajes.dropEvent = self.evento_drop_viajes 
        # ================================
        
        


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
            lambda parent, first, last: self.detectar_cambio_base(self.lista_taller, first)
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
        self.listas_bases[13] = self.lista_viajes 
        self.listas_bases[12] = self.lista_taller

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
        self.btn_reportes = crear_btn_menu("📉 Reportes Globales")

        
        # Seleccionamos el primero por defecto
        self.btn_historial.setChecked(True)

        layout_menu.addWidget(self.btn_historial)
        layout_menu.addWidget(self.btn_flota)
        layout_menu.addWidget(self.btn_bases)
        layout_menu.addWidget(self.btn_reportes)
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
        self.construir_pagina_flota(page_flota)

        # --- PÁGINA 3: BASES (Configuración) ---
        page_bases = QWidget()
        self.construir_pagina_bases(page_bases)

        # --- PÁGINA 4: REPORTES GLOBALES (¡ESTO DEBE IR AQUÍ, ANTES DE AGREGARLO!) ---
        page_reportes = QWidget()
        self.construir_pagina_reportes_globales(page_reportes)

        # Agregamos las páginas al libro
        self.paginas_admin.addWidget(page_historial) # Índice 0
        self.paginas_admin.addWidget(page_flota)     # Índice 1
        self.paginas_admin.addWidget(page_bases)     # Índice 2
        self.paginas_admin.addWidget(page_reportes)  # 3

        # ------------------------------------------
        # CONECTAR BOTONES CON PÁGINAS
        # ------------------------------------------
        # Lógica: Si clicas botón 1, muestra página 1, y apaga los otros botones
        self.btn_historial.clicked.connect(lambda: self.cambiar_pagina(0))
        self.btn_flota.clicked.connect(lambda: self.cambiar_pagina(1))
        self.btn_bases.clicked.connect(lambda: self.cambiar_pagina(2))
        self.btn_reportes.clicked.connect(lambda: self.cambiar_pagina(3))

        # ------------------------------------------
        # ARMADO FINAL
        # ------------------------------------------
        layout_admin_main.addWidget(menu_lateral)
        layout_admin_main.addWidget(self.paginas_admin)

        self.tabs.currentChanged.connect(self.al_cambiar_pestana_principal)

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
        self.btn_reportes.setChecked(indice == 3)

    def generar_bases_fisicas(self):
        bases_struct = self.db.obtener_bases_fisicas() 

        # Limpiamos el grid por si estamos recargando
        for i in reversed(range(self.grid_bases.count())): 
            self.grid_bases.itemAt(i).widget().setParent(None)

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
                lambda parent, first, last, w=lista_taxis: self.detectar_cambio_base(w, first)
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
                item = TaxiItem(numero)
                
                # --- NÚMERO MÁS GRANDE Y FUENTE ---
                font = QFont()
                font.setPointSize(18) # Aumentamos el tamaño del número
                font.setBold(True)
                item.setFont(font)
                
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Tamaño de la ficha (un poco más grande para que luzca)
                item.setSizeHint(QSize(85, 85))
                
                # Guardamos el ID real
                item.setData(Qt.ItemDataRole.UserRole, taxi['id']) 
                
                self.listas_bases[id_base].addItem(item)

    def detectar_cambio_base(self, lista_destino, indice_caida):
        """ ACTUALIZADA: Recibe el índice exacto donde cayó la ficha """
        from PyQt6.QtCore import QTimer
        # Pasamos el índice a la lógica
        QTimer.singleShot(50, lambda: self._ejecutar_actualizacion_bd(lista_destino, indice_caida))

    

    def construir_pagina_historial(self, widget_padre):
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QPushButton, QMessageBox, QLabel, QHBoxLayout, QVBoxLayout, QWidget
        
        layout = QVBoxLayout(widget_padre)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- BARRA SUPERIOR CON FILTROS ---
        barra = QWidget()
        barra.setStyleSheet("background-color: #1E293B; border-radius: 8px;")
        layout_barra = QHBoxLayout(barra)
        
        # 1. ETIQUETA Y FILTRO (NUEVO)
        lbl_filtro = QLabel("📅 Mostrar:")
        lbl_filtro.setStyleSheet("color: #94A3B8; font-weight: bold;")
        
        self.cmb_filtro_historial = QComboBox()
        self.cmb_filtro_historial.addItems(["HOY", "MES", "AÑO", "SIEMPRE"])
        self.cmb_filtro_historial.setFixedWidth(120)
        self.cmb_filtro_historial.setStyleSheet("""
            QComboBox { background-color: #0F172A; color: white; padding: 5px; border: 1px solid #475569; border-radius: 4px; }
            QComboBox::drop-down { border: 0px; }
        """)
        # Al cambiar el filtro, recargamos la tabla automáticamente
        self.cmb_filtro_historial.currentIndexChanged.connect(self.cargar_historial_en_tabla)

        # 2. BOTONES EXISTENTES
        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.clicked.connect(self.cargar_historial_en_tabla)
        btn_refresh.setStyleSheet("color: white; border: 1px solid #475569; padding: 5px 10px; border-radius: 4px; background-color: #334155;")

        btn_delete = QPushButton("🗑️ Eliminar Seleccionado")
        btn_delete.setStyleSheet("""
            QPushButton { background-color: #EF4444; color: white; font-weight: bold; padding: 5px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #DC2626; }
        """)
        btn_delete.clicked.connect(self.eliminar_viaje_seleccionado)

        # AGREGAMOS TODO A LA BARRA
        layout_barra.addWidget(lbl_filtro)
        layout_barra.addWidget(self.cmb_filtro_historial)
        layout_barra.addSpacing(10)
        layout_barra.addWidget(btn_refresh)
        layout_barra.addStretch() # Empuja el botón de eliminar a la derecha
        layout_barra.addWidget(btn_delete)

        # --- TABLA (Igual que antes) ---
        self.tabla_reportes = QTableWidget()
        cols = ["ID", "FECHA", "HORA", "UNIDAD", "CONCEPTO", "BASE SALIDA", "DESTINO", "COSTO"]
        self.tabla_reportes.setColumnCount(len(cols))
        self.tabla_reportes.setHorizontalHeaderLabels(cols)
        self.tabla_reportes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_reportes.setColumnHidden(0, True) # ID oculto

        self.tabla_reportes.setStyleSheet("""
            QTableWidget { background-color: #1E293B; color: white; border: none; gridline-color: #334155; }
            QHeaderView::section { background-color: #0F172A; color: #FACC15; padding: 5px; font-weight: bold; }
            QTableWidget::item:selected { background-color: #334155; }
        """)
        
        self.tabla_reportes.cellChanged.connect(self.guardar_edicion_tabla)

        layout.addWidget(barra)
        layout.addWidget(self.tabla_reportes)



    def cambiar_pagina(self, indice):
        self.paginas_admin.setCurrentIndex(indice)
        self.btn_historial.setChecked(indice == 0)
        self.btn_flota.setChecked(indice == 1)
        self.btn_bases.setChecked(indice == 2)
        
        if indice == 0:
            self.cargar_historial_en_tabla()
        elif indice == 1: # Si entramos a Gestión de Flota
            self.cargar_tabla_flota()
        elif indice == 2: # Gestión Bases
            self.cargar_tabla_bases()


    def _ejecutar_actualizacion_bd(self, lista_destino, indice_item):
        from PyQt6.QtWidgets import QMessageBox # Necesario para la alerta

        item = lista_destino.item(indice_item)
        if not item: return

        taxi_id_bd = item.data(Qt.ItemDataRole.UserRole)
        taxi_num = item.text()
        
        # 1. IDENTIFICACIÓN DE BASE DESTINO
        id_base_nueva = None
        if lista_destino == self.lista_taller: id_base_nueva = 12
        elif lista_destino == self.lista_viajes: id_base_nueva = 13
        else:
            for id_b, widget in self.listas_bases.items():
                if widget == lista_destino:
                    id_base_nueva = id_b
                    break

        # 2. VERIFICAR Y GUARDAR
        if id_base_nueva and taxi_id_bd:
            conexion, cursor = self.db._conectar()
            cursor.execute("SELECT base_actual_id FROM taxis WHERE id = ?", (taxi_id_bd,))
            res = cursor.fetchone()
            conexion.close()
            
            id_base_anterior = res['base_actual_id'] if res else None

            # === LÓGICA DEL REBOTE (Ligar viajes consecutivos) ===
            es_rebote = (id_base_anterior == 13 and id_base_nueva == 13)

            # Si soltaste el taxi donde mismo Y NO ES UN REBOTE, no hacemos nada
            if id_base_anterior == id_base_nueva and not es_rebote:
                lista_destino.sortItems(Qt.SortOrder.AscendingOrder)
                return

            # --- LÓGICA DE MOVIMIENTOS ---

            if id_base_nueva == 13: # DESTINO: VIAJE
                if es_rebote:
                    # PREGUNTA DE SEGURIDAD
                    respuesta = QMessageBox.question(
                        self, "Ligar Nuevo Viaje", 
                        f"El taxi {taxi_num} ya está en viaje.\n¿Deseas finalizarlo y registrar uno nuevo inmediato?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if respuesta == QMessageBox.StandardButton.No:
                        lista_destino.sortItems(Qt.SortOrder.AscendingOrder)
                        return
                    
                    # SI DICE QUE SÍ:
                    print(f"🔄 Rebote confirmado: Taxi {taxi_num}.")
                    self.db.registrar_fin_viaje(taxi_id_bd) # Cerramos el anterior
                    # Abrimos ventana nuevo viaje (Origen 13 = En Circulación)
                    self.abrir_ventana_nuevo_viaje(taxi_id_bd, taxi_num, 13)
                
                else: # Viaje normal (saliendo de base o de descanso)
                    if id_base_anterior == 12: self.db.hora_entrada(taxi_id_bd)
                    # Abrimos ventana pasando el origen real
                    self.abrir_ventana_nuevo_viaje(taxi_id_bd, taxi_num, id_base_anterior)

            elif id_base_nueva == 12: # DESTINO: FUERA SERVICIO
                print(f"🛑 CERRANDO TURNO taxi {taxi_num}")
                self.db.hora_salida(taxi_id_bd)
                self.db.registrar_fin_viaje(taxi_id_bd)

            elif id_base_nueva <= 11: # DESTINO: BASES NORMALES
                if id_base_anterior == 12: self.db.hora_entrada(taxi_id_bd)
                self.db.registrar_fin_viaje(taxi_id_bd)

            # Guardado final de ubicación en BD
            self.db.actualizar_taxi_base(taxi_id_bd, id_base_nueva)
        
        # 3. ORDENAR SIEMPRE AL FINAL
        lista_destino.sortItems(Qt.SortOrder.AscendingOrder)



    def abrir_ventana_nuevo_viaje(self, taxi_id, taxi_num, id_origen_detectado):
        """ Ventana Inteligente: Bloquea la base si es servicio por teléfono """
        from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox, QVBoxLayout
        
        dialogo = QDialog(self)
        dialogo.setWindowTitle(f"🚕 Nuevo Viaje - Unidad {taxi_num}")
        dialogo.setMinimumWidth(350)
        dialogo.setStyleSheet("""
            QDialog { background-color: #1E293B; border: 2px solid #00D1FF; border-radius: 10px; }
            QLabel { color: #FACC15; font-weight: bold; font-size: 14px; }
            QLineEdit, QComboBox { 
                background-color: #0F172A; color: white; border: 1px solid #334155; padding: 5px; border-radius: 5px;
            }
            QComboBox:disabled { background-color: #334155; color: #94A3B8; }
        """)
        
        layout = QVBoxLayout(dialogo)
        formulario = QFormLayout()
        
        # 1. SERVICIO (Lo ponemos PRIMERO porque decide lo demás)
        self.cmb_servicio = QComboBox()
        # IDs visuales: 0=Base, 1=Tel Base, 2=Tel Unidad, 3=Aéreo
        self.cmb_servicio.addItems(["Viaje en base", "Teléfono base", "Teléfono unidad", "Viaje aéreo"])
        
        # 2. ORIGEN (Saliendo de...)
        self.cmb_origen = QComboBox()
        bases_info = [
            (1, "Cessa"), (2, "Licuor"), (3, "Santiaguito"), (4, "Aurrera"), (5, "Mercado"),
            (6, "Caros"), (7, "Survi"), (8, "Capulín"), (9, "Zócalo"), (10, "16 de Septiembre"), 
            (11, "Parada Principal"), (12, "Fuera de Servicio"), (13, "En Circulación/Calle") 
        ]
        
        indice_defecto = 0
        for i, (id_b, nombre) in enumerate(bases_info):
            self.cmb_origen.addItem(nombre, id_b)
            if id_b == id_origen_detectado:
                indice_defecto = i
        self.cmb_origen.setCurrentIndex(indice_defecto)

        # 3. Lógica de Bloqueo
        def actualizar_estado_origen():
            indice = self.cmb_servicio.currentIndex()
            # Si es "Viaje en base" (Índice 0), permitimos editar la base.
            # Si es cualquier otro (Teléfono/Aéreo), bloqueamos la base.
            if indice == 0:
                self.cmb_origen.setEnabled(True)
                # Opcional: regresar al origen detectado si se reactiva
            else:
                self.cmb_origen.setEnabled(False)

        self.cmb_servicio.currentIndexChanged.connect(actualizar_estado_origen)

        # Campos extra
        self.txt_destino = QLineEdit()
        self.txt_destino.setPlaceholderText("¿A dónde va?")
        self.txt_destino.setFocus()
        self.txt_costo = QLineEdit()
        self.txt_costo.setPlaceholderText("0.00")
        
        formulario.addRow("🛠️ Concepto:", self.cmb_servicio)
        formulario.addRow("🚩 Base Salida:", self.cmb_origen)
        formulario.addRow("📍 Destino:", self.txt_destino)
        formulario.addRow("💰 Costo $:", self.txt_costo)
        
        layout.addLayout(formulario)
        
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.accepted.connect(dialogo.accept)
        botones.rejected.connect(dialogo.reject)
        layout.addWidget(botones)

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            id_tipo_servicio = self.cmb_servicio.currentIndex() + 1
            
            # LÓGICA DE GUARDADO:
            # Si está bloqueado (Teléfono/Aéreo), guardamos el origen como NULL o un ID especial,
            # pero para no romper tu BD, usaremos el que está seleccionado pero visualmente lo ignoraremos en reportes.
            id_origen_final = self.cmb_origen.currentData()
            
            destino = self.txt_destino.text()
            try:
                costo = float(self.txt_costo.text().replace(',', '.')) if self.txt_costo.text() else 0.0
            except: costo = 0.0 
            
            self.db.registrar_viaje(taxi_id, id_tipo_servicio, id_origen_final, destino, costo) 
            self.db.actualizar_taxi_base(taxi_id, 13)
            print(f"✅ Viaje registrado ({self.cmb_servicio.currentText()})")
        else:
            self.cargar_datos_en_tablero()

    def filtrar_taxis_tablero(self, texto):
        """ Filtra los taxis por COINCIDENCIA EXACTA """
        busqueda = texto.lower().strip()
        
        for lista in self.listas_bases.values():
            for i in range(lista.count()):
                item = lista.item(i)
                texto_item = item.text().lower()
                
                # --- CAMBIO CLAVE ---
                # ANTES: if not busqueda or busqueda in texto_item:
                # AHORA: Usamos '==' para que sea exacto.
                # (Si 'busqueda' está vacío, mostramos todo con 'not busqueda')
                
                if not busqueda or texto_item == busqueda:
                    item.setHidden(False)
                else:
                    item.setHidden(True)

    def cargar_historial_en_tabla(self):
        try: self.tabla_reportes.cellChanged.disconnect()
        except: pass

        self.tabla_reportes.setRowCount(0)
        
        # 1. LEEMOS EL FILTRO DE FECHA (HOY, MES, ETC.)
        if hasattr(self, 'cmb_filtro_historial'):
            filtro = self.cmb_filtro_historial.currentText()
        else:
            filtro = "HOY"
            
        # 2. CARGAMOS LOS DATOS DESDE LA BD
        viajes = self.db.obtener_historial_viajes(filtro)

        mapa_servicios = {1: "Viaje en Base", 2: "Teléfono Base", 3: "Teléfono Unidad", 4: "Viaje Aéreo"}

        for datos in viajes:
            row = self.tabla_reportes.rowCount()
            self.tabla_reportes.insertRow(row)

            # Lógica visual (//// y Nombres)
            id_servicio = datos.get('tipo_servicio_id', 1) 
            nombre_servicio = mapa_servicios.get(id_servicio, "Otro")
            nombre_base = datos['nombre_base'] if datos['nombre_base'] else "---"
            if id_servicio != 1: nombre_base = "////"

            # Llenado de celdas
            self.tabla_reportes.setItem(row, 0, QTableWidgetItem(str(datos['id'])))
            fh = str(datos['fecha_hora_inicio']).split(" ")
            self.tabla_reportes.setItem(row, 1, QTableWidgetItem(fh[0]))
            self.tabla_reportes.setItem(row, 2, QTableWidgetItem(fh[1][:5] if len(fh)>1 else ""))
            self.tabla_reportes.setItem(row, 3, QTableWidgetItem(str(datos['numero_economico'])))
            self.tabla_reportes.setItem(row, 4, QTableWidgetItem(nombre_servicio))
            self.tabla_reportes.setItem(row, 5, QTableWidgetItem(nombre_base))
            self.tabla_reportes.setItem(row, 6, QTableWidgetItem(str(datos['destino'])))
            self.tabla_reportes.setItem(row, 7, QTableWidgetItem(str(datos['precio'])))

        self.tabla_reportes.cellChanged.connect(self.guardar_edicion_tabla)

        # === CORRECCIÓN AQUÍ: RE-APLICAR EL FILTRO DE BÚSQUEDA ===
        # Si tenías escrito "500" arriba, volvemos a filtrar la tabla recién cargada
        if hasattr(self, 'txt_buscar_taxi'):
            texto_buscado = self.txt_buscar_taxi.text().strip()
            if texto_buscado:
                self.filtrar_tabla_historial(texto_buscado)

                
    def guardar_edicion_tabla(self, row, col):
        """ Se activa automáticamente al editar una celda """
        id_viaje = self.tabla_reportes.item(row, 0).text()
        nuevo_valor = self.tabla_reportes.item(row, col).text()
        
        columna_db = ""
        if col == 5: columna_db = "destino"
        elif col == 6: columna_db = "precio"
        
        if columna_db:
            self.db.actualizar_viaje(id_viaje, columna_db, nuevo_valor)

    def eliminar_viaje_seleccionado(self):
        """ Elimina la fila seleccionada """
        fila_actual = self.tabla_reportes.currentRow()
        if fila_actual < 0: return

        id_viaje = self.tabla_reportes.item(fila_actual, 0).text()
        
        # Confirmación simple en consola (o puedes agregar un QMessageBox si prefieres)
        exito = self.db.eliminar_viaje(id_viaje)
        
        if exito:
            self.tabla_reportes.removeRow(fila_actual)


    def al_cambiar_pestana_principal(self, indice):
        """Si el usuario cambia a la pestaña de Administración (Índice 1), actualizamos la tabla"""
        if indice == 1: # 1 es el índice de Administración
            self.cargar_historial_en_tabla()


    def evento_drop_viajes(self, event):
        """ Truco: Detecta cuando sueltas un taxi en la caja verde (incluso si es el mismo) """
        # 1. Dejamos que la lista haga su trabajo visual (mover el icono)
        QListWidget.dropEvent(self.lista_viajes, event)
        
        # 2. Inmediatamente detectamos qué taxi quedó seleccionado/movido
        fila_actual = self.lista_viajes.currentRow()
        
        # 3. Forzamos la lógica de actualización (esto activa el Rebote)
        self.detectar_cambio_base(self.lista_viajes, fila_actual)
        
        # 4. Ordenamos para que no quede "flotando" en cualquier lado
        self.lista_viajes.sortItems(Qt.SortOrder.AscendingOrder)
    

    
    def construir_pagina_flota(self, widget_padre):
        from PyQt6.QtWidgets import (QHeaderView, QTableWidget, QTableWidgetItem, QFrame, 
                                     QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox)
        from PyQt6.QtCore import QDate
        
        layout = QHBoxLayout(widget_padre) 
        
        # --- ZONA IZQUIERDA: TABLA (Igual que antes) ---
        frame_tabla = QFrame()
        frame_tabla.setFixedWidth(380) 
        layout_tabla = QVBoxLayout(frame_tabla)
        layout_tabla.setContentsMargins(0, 0, 10, 0) 
        
        frame_alta = QFrame()
        frame_alta.setStyleSheet("background-color: #1E293B; border-radius: 5px;")
        l_alta = QHBoxLayout(frame_alta)
        
        self.txt_nuevo_taxi = QLineEdit()
        self.txt_nuevo_taxi.setPlaceholderText("Nuevo # (Ej. 150)")
        btn_agregar = QPushButton("➕ Alta")
        btn_agregar.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 5px 10px;")
        btn_agregar.clicked.connect(self.registrar_nuevo_taxi_ui)
        l_alta.addWidget(self.txt_nuevo_taxi)
        l_alta.addWidget(btn_agregar)
        
        self.tabla_flota = QTableWidget()
        self.tabla_flota.setColumnCount(3)
        self.tabla_flota.setHorizontalHeaderLabels(["UNIDAD", "ESTADO", "ACCIÓN"])
        self.tabla_flota.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_flota.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_flota.setStyleSheet("""
            QTableWidget { background-color: #1E293B; color: white; border: none; border-radius: 8px; }
            QHeaderView::section { background-color: #0F172A; color: #FACC15; font-weight: bold; padding: 4px; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #FACC15; color: black; }
        """)
        self.tabla_flota.itemClicked.connect(self.al_clic_tabla_flota)
        layout_tabla.addWidget(frame_alta)
        layout_tabla.addWidget(self.tabla_flota)
        
        # --- ZONA DERECHA: REPORTES ---
        frame_stats = QFrame()
        frame_stats.setStyleSheet("background-color: #0F172A; border-left: 2px solid #334155;")
        layout_stats = QVBoxLayout(frame_stats)
        layout_stats.setContentsMargins(20, 20, 20, 20) 
        
        # Cabecera
        header_reporte = QHBoxLayout()
        lbl_titulo = QLabel("📊 REPORTE DE UNIDAD")
        lbl_titulo.setStyleSheet("color: #94A3B8; font-size: 14px; font-weight: bold;")
        
        # === AQUÍ EL CAMBIO PARA SELECCIONAR FECHAS ===
        
        # 1. Selector de fecha (Calendario)
        self.date_selector = QDateEdit()
        self.date_selector.setCalendarPopup(True) # Que salga el cuadrito de calendario
        self.date_selector.setDate(QDate.currentDate()) # Por defecto hoy
        self.date_selector.setFixedWidth(110)
        self.date_selector.setStyleSheet("background-color: #1E293B; color: white; padding: 5px; border: 1px solid #334155;")
        self.date_selector.dateChanged.connect(self.buscar_stats_por_input) # Al cambiar fecha, recarga datos

        # 2. Combo de Periodo (Lo mantenemos para saber si quieres EL DIA, EL MES o EL AÑO de la fecha seleccionada)
        self.cmb_periodo_stats = QComboBox()
        self.cmb_periodo_stats.addItems(["DIA", "MES", "AÑO"]) # Cambié HOY por DIA para ser más claro
        self.cmb_periodo_stats.setFixedWidth(80)
        self.cmb_periodo_stats.setStyleSheet("background-color: #1E293B; color: white; padding: 5px;")
        self.cmb_periodo_stats.currentIndexChanged.connect(self.buscar_stats_por_input)

        # === CAMBIO 1: Conectamos a 'actualizar_formato_fecha' ===
        self.cmb_periodo_stats.currentIndexChanged.connect(self.actualizar_formato_fecha)
        self.cmb_periodo_stats.currentIndexChanged.connect(self.buscar_stats_por_input)
        
        header_reporte.addWidget(lbl_titulo)
        header_reporte.addStretch()
        header_reporte.addWidget(QLabel("Fecha Ref:"))
        header_reporte.addWidget(self.date_selector) # Agregamos el calendario
        header_reporte.addWidget(self.cmb_periodo_stats)
        
        # Input Taxi
        contenedor_input = QHBoxLayout()
        lbl_taxi = QLabel("Taxi:")
        lbl_taxi.setStyleSheet("color: #00D1FF; font-size: 40px; font-weight: bold;")
        self.txt_taxi_selec = QLineEdit()
        self.txt_taxi_selec.setPlaceholderText("#")
        self.txt_taxi_selec.setMaxLength(5)
        self.txt_taxi_selec.setFixedWidth(180)
        self.txt_taxi_selec.setStyleSheet("""
            QLineEdit { color: #00D1FF; font-size: 40px; font-weight: bold; background: transparent; border: none; border-bottom: 3px solid #334155; }
            QLineEdit:focus { border-bottom: 3px solid #00D1FF; }
        """)
        self.txt_taxi_selec.textChanged.connect(self.buscar_stats_por_input)
        contenedor_input.addWidget(lbl_taxi)
        contenedor_input.addWidget(self.txt_taxi_selec)
        contenedor_input.addStretch()

        # Input Taxi
        contenedor_input = QHBoxLayout()
        # ... (lbl_taxi y txt_taxi_selec) ...

        # === BOTÓN PDF ===
        btn_pdf = QPushButton("🖨️ PDF")
        btn_pdf.setFixedSize(80, 50) # Botón gordito
        btn_pdf.setStyleSheet("""
            QPushButton { background-color: #F87171; color: white; font-weight: bold; font-size: 16px; border-radius: 8px; }
            QPushButton:hover { background-color: #DC2626; }
        """)
        btn_pdf.clicked.connect(self.exportar_pdf_unidad) # Conectamos función

        contenedor_input.addWidget(lbl_taxi)
        contenedor_input.addWidget(self.txt_taxi_selec)
        contenedor_input.addSpacing(10)
        contenedor_input.addWidget(btn_pdf) # <--- Lo agregamos al layout
        contenedor_input.addStretch()

        # Tarjetas Numéricas
        layout_tarjetas = QHBoxLayout()
        layout_tarjetas.setSpacing(15)
        # Función auxiliar para crear tarjetas GRANDES y LIMPIAS
        def crear_tarjeta(titulo, color, icono):
            f = QFrame()
            # ESTILO CORREGIDO:
            # 1. border-left: Barra lateral gruesa (más elegante que arriba)
            # 2. Sin border-top para evitar la "doble línea"
            # 3. Padding interno generoso
            f.setStyleSheet(f"""
                QFrame {{
                    background-color: #1E293B; 
                    border-radius: 15px; 
                    border-left: 8px solid {color};
                }}
            """)
            
            # TAMAÑO: Forzamos altura mínima para que se vean GRANDES
            f.setMinimumHeight(110) 
            f.setSizePolicy(f.sizePolicy().Policy.Expanding, f.sizePolicy().Policy.Fixed)
            
            l = QVBoxLayout(f)
            l.setContentsMargins(20, 15, 20, 15) # Margen interno para que respire
            
            # Título un poco más grande
            lbl_t = QLabel(f"{icono} {titulo}")
            lbl_t.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold; border: none; background: transparent;")
            
            # Valor GIGANTE
            lbl_v = QLabel("0")
            lbl_v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl_v.setStyleSheet("color: white; font-size: 36px; font-weight: bold; border: none; background: transparent;")
            
            l.addWidget(lbl_t)
            l.addWidget(lbl_v)
            return f, lbl_v
            
        c_dinero, self.lbl_stat_dinero = crear_tarjeta("GANANCIAS", "#FACC15", "💰")
        c_viajes, self.lbl_stat_viajes = crear_tarjeta("VIAJES", "#10B981", "🚖")
        c_horas,  self.lbl_stat_horas  = crear_tarjeta("HORAS", "#F472B6", "⏱️")
        layout_tarjetas.addWidget(c_dinero)
        layout_tarjetas.addWidget(c_viajes)
        layout_tarjetas.addWidget(c_horas)

        # === ZONA GRÁFICOS: 3 PANELES ===
        self.zona_graficos = QFrame()
        self.zona_graficos.setStyleSheet("border-radius: 10px; background-color: #0F172A;")
        lay_graficos = QHBoxLayout(self.zona_graficos) # Layout Horizontal para ponerlas una al lado de otra
        lay_graficos.setSpacing(10)
        lay_graficos.setContentsMargins(0,0,0,0)

        # Creamos las 3 instancias
        self.grafico_dinero = LienzoGrafico(self.zona_graficos)
        self.grafico_viajes = LienzoGrafico(self.zona_graficos)
        self.grafico_horas  = LienzoGrafico(self.zona_graficos)

        lay_graficos.addWidget(self.grafico_dinero)
        lay_graficos.addWidget(self.grafico_viajes)
        lay_graficos.addWidget(self.grafico_horas)

        # Ensamblaje
        layout_stats.addLayout(header_reporte)
        layout_stats.addLayout(contenedor_input)
        layout_stats.addSpacing(10)
        layout_stats.addLayout(layout_tarjetas) 
        layout_stats.addSpacing(20)
        layout_stats.addWidget(self.zona_graficos, 1) # Stretch para que los gráficos ocupen el espacio
        
        layout.addWidget(frame_tabla) 
        layout.addWidget(frame_stats, 1)

        self.actualizar_formato_fecha()

    # --- LÓGICA DE LA FLOTA ---

    def cargar_tabla_flota(self):
        """ Llena la lista y ORDENA numéricamente """
        self.tabla_flota.setRowCount(0)
        flota = self.db.obtener_toda_la_flota()
        
        # === SOLUCIÓN AL ORDEN (100 antes de 35) ===
        # Ordenamos la lista en Python convirtiendo a entero
        try:
            flota.sort(key=lambda x: int(x['numero_economico']))
        except ValueError:
            pass # Si hay letras (ej. "T-1"), no ordenará perfecto, pero no tronará
            
        for taxi in flota:
            row = self.tabla_flota.rowCount()
            self.tabla_flota.insertRow(row)
            
            # 1. Número
            item_num = QTableWidgetItem(str(taxi['numero_economico']))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_num.setData(Qt.ItemDataRole.UserRole, taxi['id']) 
            self.tabla_flota.setItem(row, 0, item_num)
            
            # 2. Estado
            estado = taxi['estado_sistema']
            item_estado = QTableWidgetItem(estado)
            item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_estado.setForeground(Qt.GlobalColor.green if estado == 'ACTIVO' else Qt.GlobalColor.red)
            self.tabla_flota.setItem(row, 1, item_estado)
            
            # 3. Botón Acción
            btn_accion = QPushButton("Desactivar" if estado == "ACTIVO" else "Activar")
            color_btn = "#EF4444" if estado == "ACTIVO" else "#10B981"
            btn_accion.setStyleSheet(f"background-color: {color_btn}; color: white; font-weight: bold;")
            btn_accion.clicked.connect(lambda _, t_id=taxi['id'], est=estado: self.alternar_estado_taxi(t_id, est))
            self.tabla_flota.setCellWidget(row, 2, btn_accion)

    def al_clic_tabla_flota(self, item):
        """ Cuando clicas la tabla, rellenamos el input grande """
        fila = self.tabla_flota.currentRow()
        if fila < 0: return
        numero = self.tabla_flota.item(fila, 0).text()
        
        self.txt_taxi_selec.setText(numero) # Ponemos el número en el input
        self.buscar_stats_por_input()       # Ejecutamos la búsqueda

    def buscar_stats_por_input(self):
        numero = self.txt_taxi_selec.text().strip()
        periodo = self.cmb_periodo_stats.currentText()
        
        # === CORRECCIÓN CLAVE: LEER LA FECHA ===
        # Obtenemos la fecha del selector y la convertimos a texto "YYYY-MM-DD"
        qdate = self.date_selector.date()
        fecha_str = qdate.toString("yyyy-MM-dd")
        # =======================================

        # Limpieza
        if not numero: 
            self.lbl_stat_dinero.setText("$0.00")
            self.lbl_stat_viajes.setText("0")
            self.lbl_stat_horas.setText("0.0 h")
            # Limpiar gráficas
            self.grafico_dinero.actualizar_grafico([], [], "dinero")
            self.grafico_viajes.actualizar_grafico([], [], "viajes")
            self.grafico_horas.actualizar_grafico([], [], "horas")
            return

        taxi_id = self.db.obtener_id_por_numero(numero)
        
        if taxi_id:
            # 1. Tarjetas Numéricas (Ahora pasamos fecha_ref)
            stats = self.db.obtener_estadisticas_unidad(taxi_id, periodo, fecha_ref=fecha_str)
            
            self.lbl_stat_dinero.setText(f"${stats['ganancia']:,.2f}") # Agregué comas
            self.lbl_stat_viajes.setText(str(stats['viajes']))
            self.lbl_stat_horas.setText(f"{stats['horas']:.1f} h")
            
            # 2. Gráficas Detalladas (Ahora pasamos fecha_ref)
            if periodo == "SIEMPRE": periodo = "AÑO" 
            datos = self.db.obtener_datos_tres_graficas(taxi_id, periodo, fecha_ref=fecha_str)
            
            self.grafico_dinero.actualizar_grafico(datos["etiquetas"], datos["dinero"], "dinero")
            self.grafico_viajes.actualizar_grafico(datos["etiquetas"], datos["viajes"], "viajes")
            self.grafico_horas.actualizar_grafico(datos["etiquetas"], datos["horas"], "horas")
            
            # 3. Sincronizar tabla izquierda
            # (Código anterior para seleccionar fila...)
            self.filtrar_tabla_flota(numero) # Truco: Refiltramos la tabla para que se vea solo este taxi
        else:
            # Si no existe, limpiamos
            self.grafico_dinero.actualizar_grafico([], [], "dinero")
            self.grafico_viajes.actualizar_grafico([], [], "viajes")
            self.grafico_horas.actualizar_grafico([], [], "horas")


    def filtrar_tabla_flota(self, texto):
        """ 
        Filtra la tabla de la izquierda para mostrar solo el taxi que buscas.
        Es vital para que cuando busques '500', la lista oculte a los demás.
        """
        busqueda = texto.lower().strip()
        
        for fila in range(self.tabla_flota.rowCount()):
            item = self.tabla_flota.item(fila, 0) # Columna 0 = Unidad
            if item:
                # Si no hay búsqueda, mostramos todo.
                # Si hay búsqueda, verificamos si coincide parcialmente.
                if not busqueda or busqueda in item.text().lower():
                    self.tabla_flota.setRowHidden(fila, False)
                else:
                    self.tabla_flota.setRowHidden(fila, True)


    def actualizar_solo_grafico(self):
        """ Re-pinta el gráfico usando los datos que ya bajamos de la BD """
        if not hasattr(self, 'datos_grafica_actual') or not self.datos_grafica_actual:
            return

        indice = self.cmb_tipo_grafico.currentIndex()
        fechas = self.datos_grafica_actual['fechas']
        
        if indice == 0: # Dinero
            valores = self.datos_grafica_actual['dinero']
            tipo = "dinero"
        elif indice == 1: # Viajes
            valores = self.datos_grafica_actual['viajes']
            tipo = "viajes"
        else: # Horas
            valores = self.datos_grafica_actual['horas']
            tipo = "horas"
            
        self.mi_grafico.actualizar_grafico(fechas, valores, tipo)


    def registrar_nuevo_taxi_ui(self):
        numero = self.txt_nuevo_taxi.text().strip()
        if not numero: return
        
        # Registramos en BD (Por defecto entra a Base 12 - Fuera de Servicio)
        if self.db.registrar_nuevo_taxi(numero, id_base_inicial=12):
            self.txt_nuevo_taxi.clear()
            self.cargar_tabla_flota() # Recargamos la lista
            self.cargar_datos_en_tablero() # Recargamos el tablero principal para que aparezca la ficha
            print(f"Taxi {numero} dado de alta.")

    def alternar_estado_taxi(self, taxi_id, estado_actual):
        nuevo_estado = "INACTIVO" if estado_actual == "ACTIVO" else "ACTIVO"
        
        if self.db.cambiar_estado_taxi(taxi_id, nuevo_estado):
            self.cargar_tabla_flota()      # Actualiza esta tabla
            self.cargar_datos_en_tablero() # Actualiza el tablero visual (quita/pone la ficha)

    def mostrar_estadisticas_taxi(self, item=None):
        """ Muestra los datos en el panel derecho al seleccionar una fila """
        fila = self.tabla_flota.currentRow()
        if fila < 0: return
        
        # Obtenemos el ID del item de la columna 0
        item_num = self.tabla_flota.item(fila, 0)
        taxi_id = item_num.data(Qt.ItemDataRole.UserRole)
        numero = item_num.text()
        
        periodo = self.cmb_periodo_stats.currentText() # HOY, MES, etc.
        
        stats = self.db.obtener_estadisticas_unidad(taxi_id, periodo)
        
        # Actualizamos interfaz
        self.lbl_taxi_selec.setText(f"Taxi {numero}")
        self.lbl_stat_dinero.setText(f"${stats['ganancia']:.2f}")
        self.lbl_stat_viajes.setText(str(stats['viajes']))
        self.lbl_stat_horas.setText(f"{stats['horas']:.1f} hrs")



    def construir_pagina_bases(self, widget_padre):
        from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
                                     QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox)
        
        layout = QHBoxLayout(widget_padre)
        
        # --- ZONA IZQUIERDA: LISTA Y ALTA (Igual que antes) ---
        frame_izq = QFrame()
        frame_izq.setFixedWidth(400)
        lay_izq = QVBoxLayout(frame_izq)
        
        # 1. Alta
        frame_alta = QFrame()
        frame_alta.setStyleSheet("background-color: #1E293B; border-radius: 8px;")
        lay_alta = QVBoxLayout(frame_alta)
        lbl_new = QLabel("Nueva Base:")
        lbl_new.setStyleSheet("color: #FACC15; font-weight: bold;")
        h_alta = QHBoxLayout()
        self.txt_nueva_base = QLineEdit()
        self.txt_nueva_base.setPlaceholderText("Nombre (Ej. Hospital)")
        btn_add = QPushButton("➕ Agregar")
        btn_add.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; padding: 5px 15px;")
        btn_add.clicked.connect(self.agregar_nueva_base)
        h_alta.addWidget(self.txt_nueva_base)
        h_alta.addWidget(btn_add)
        lay_alta.addWidget(lbl_new)
        lay_alta.addLayout(h_alta)
        
        # 2. Tabla
        self.tabla_bases = QTableWidget()
        self.tabla_bases.setColumnCount(3)
        self.tabla_bases.setHorizontalHeaderLabels(["ID", "NOMBRE", "ACCION"])
        self.tabla_bases.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_bases.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_bases.setStyleSheet("""
            QTableWidget { background-color: #1E293B; color: white; border: none; }
            QHeaderView::section { background-color: #0F172A; color: #FACC15; font-weight: bold; }
        """)
        lay_izq.addWidget(frame_alta)
        lay_izq.addWidget(self.tabla_bases)
        
        # --- ZONA DERECHA: ESTADÍSTICAS (ACTUALIZADA) ---
        frame_der = QFrame()
        frame_der.setStyleSheet("background-color: #0F172A; border-left: 2px solid #334155;")
        lay_der = QVBoxLayout(frame_der)
        
        # CABECERA CON FILTRO
        header_stats = QHBoxLayout()
        
        lbl_stats = QLabel("📈 BASES MÁS CONCURRIDAS")
        lbl_stats.setStyleSheet("color: #00D1FF; font-size: 18px; font-weight: bold;")
        
        self.cmb_periodo_bases = QComboBox()
        self.cmb_periodo_bases.addItems(["SIEMPRE", "HOY", "MES", "AÑO"]) # Default SIEMPRE
        self.cmb_periodo_bases.setFixedWidth(120)
        self.cmb_periodo_bases.setStyleSheet("background-color: #1E293B; color: white; padding: 5px;")
        # Al cambiar filtro, recargamos solo la gráfica (o todo)
        self.cmb_periodo_bases.currentIndexChanged.connect(self.actualizar_grafico_bases)
        
        header_stats.addWidget(lbl_stats)
        header_stats.addStretch()
        header_stats.addWidget(self.cmb_periodo_bases)
        
        # GRÁFICO
        self.grafico_bases = LienzoGrafico(frame_der)
        
        lay_der.addLayout(header_stats)
        lay_der.addWidget(self.grafico_bases)
        
        layout.addWidget(frame_izq)
        layout.addWidget(frame_der, 1)



        
    # --- LÓGICA INTERNA DE BASES ---

    def cargar_tabla_bases(self):
        """ Llena la tabla y llama a actualizar el gráfico """
        self.tabla_bases.setRowCount(0)
        bases = self.db.obtener_bases_fisicas()
        
        for id_b, nombre in bases:
            row = self.tabla_bases.rowCount()
            self.tabla_bases.insertRow(row)
            
            self.tabla_bases.setItem(row, 0, QTableWidgetItem(str(id_b)))
            self.tabla_bases.setItem(row, 1, QTableWidgetItem(nombre))
            
            btn_del = QPushButton("🗑️ Baja")
            btn_del.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; border-radius: 4px;")
            btn_del.clicked.connect(lambda _, i=id_b: self.baja_base(i))
            self.tabla_bases.setCellWidget(row, 2, btn_del)
            
        # Actualizar Gráfico también
        self.actualizar_grafico_bases()

    def actualizar_grafico_bases(self):
        """ Función separada para recargar solo el gráfico al cambiar el combo """
        if not hasattr(self, 'cmb_periodo_bases'): return
        
        periodo = self.cmb_periodo_bases.currentText()
        nombres, viajes = self.db.obtener_ranking_bases(periodo)
        
        self.grafico_bases.actualizar_grafico(nombres, viajes, "viajes")


    def agregar_nueva_base(self):
        nombre = self.txt_nueva_base.text().strip()
        if not nombre: return
        
        if self.db.registrar_nueva_base(nombre):
            self.txt_nueva_base.clear()
            self.cargar_tabla_bases()       # Actualiza esta lista
            self.generar_bases_fisicas()    # <--- ¡ESTO ACTUALIZA EL TABLERO PRINCIPAL!
            self.cargar_datos_en_tablero()  # Y volvemos a poner los taxis en su lugar

    def baja_base(self, id_base):
        from PyQt6.QtWidgets import QMessageBox
        confirm = QMessageBox.question(self, "Dar de Baja", 
            "¿Seguro que deseas eliminar esta base?\nSi hay taxis en ella, se pasarán a 'Fuera de Servicio'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            if self.db.eliminar_base_fisica(id_base):
                self.cargar_tabla_bases()
                self.generar_bases_fisicas()   # Actualiza el tablero visualmente
                self.cargar_datos_en_tablero() # Reacomoda las fichas



    def filtrar_tabla_historial(self, texto):
        """ Oculta filas que no sean EXACTAMENTE el número buscado """
        busqueda = texto.lower().strip()
        
        for fila in range(self.tabla_reportes.rowCount()):
            item_unidad = self.tabla_reportes.item(fila, 3) # Columna 3 = UNIDAD
            
            if item_unidad:
                texto_celda = item_unidad.text().lower()
                
                # --- CAMBIO CLAVE ---
                # Si no hay búsqueda, mostramos todo.
                # Si hay búsqueda, TIENE que ser idéntico (==).
                if not busqueda or texto_celda == busqueda:
                    self.tabla_reportes.setRowHidden(fila, False)
                else:
                    self.tabla_reportes.setRowHidden(fila, True)



    def busqueda_unificada(self, texto):
        """ Router: Decide qué buscar dependiendo de dónde esté el usuario """
        indice_principal = self.tabs.currentIndex() # 0=Tablero, 1=Admin
        
        if indice_principal == 0:
            # Estamos en el Tablero -> Filtramos las fichas (Tu función vieja)
            self.filtrar_taxis_tablero(texto)
            
        elif indice_principal == 1:
            # Estamos en Administración
            indice_sub = self.paginas_admin.currentIndex() # 0=Historial, 1=Flota, 2=Bases
            
            if indice_sub == 0:
                # Estamos en Historial -> Filtramos la tabla
                self.filtrar_tabla_historial(texto)
                
            # (Opcional) Aquí podrías agregar elif indice_sub == 1 para filtrar la flota también
    

    def exportar_pdf_unidad(self):
        from PyQt6.QtWidgets import QMessageBox # <--- Importante para la alerta
        
        # 1. Validar taxi
        numero = self.txt_taxi_selec.text().strip()
        if not numero:
            QMessageBox.warning(self, "Atención", "Por favor selecciona o escribe un número de taxi.")
            return
            
        taxi_id = self.db.obtener_id_por_numero(numero)
        if not taxi_id: 
            QMessageBox.warning(self, "Error", "El taxi no existe en la base de datos.")
            return

        # 2. Obtener Datos (Usando la nueva lógica de fecha)
        periodo = self.cmb_periodo_stats.currentText()
        fecha_qdate = self.date_selector.date()
        fecha_str = fecha_qdate.toString("yyyy-MM-dd") # Formato para SQL
        
        # Necesitamos actualizar las funciones de BD para recibir fecha_str
        # (Mira el PASO 3 para ver cómo actualizar gestor_db.py)
        stats = self.db.obtener_estadisticas_unidad(taxi_id, periodo, fecha_ref=fecha_str)
        detalle_viajes = self.db.obtener_viajes_por_unidad_y_periodo(taxi_id, periodo, fecha_ref=fecha_str)
        
        if not detalle_viajes:
            # === VENTANA EMERGENTE DE ERROR ===
            QMessageBox.information(self, "Sin Información", f"No hay viajes registrados para el taxi {numero} en este periodo.")
            return

        # 3. Generar Texto Bonito para el PDF
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        dia = fecha_qdate.day()
        mes = meses[fecha_qdate.month()]
        anio = fecha_qdate.year()

        texto_fecha = ""
        if periodo == "DIA":
            texto_fecha = f"Reporte del Día: {dia} de {mes} de {anio}"
        elif periodo == "MES":
            texto_fecha = f"Reporte Mensual: {mes} {anio}"
        elif periodo == "AÑO":
            texto_fecha = f"Reporte Anual: {anio}"

        # 4. Generar PDF
        nombre_pdf = f"Taxi_{numero}_{periodo}_{fecha_str}.pdf"
        generador = GeneradorPDF(nombre_pdf)
        generador.generar_reporte_unidad(numero, texto_fecha, stats, detalle_viajes)


    def actualizar_formato_fecha(self):
        """ Cambia el aspecto del calendario según si eliges DIA, MES o AÑO """
        periodo = self.cmb_periodo_stats.currentText()
        
        if periodo == "DIA":
            # Muestra todo: 18/01/2026
            self.date_selector.setDisplayFormat("dd/MM/yyyy")
            self.date_selector.setCalendarPopup(True) # Calendario completo
            
        elif periodo == "MES":
            # Muestra solo mes y año: 01/2026
            self.date_selector.setDisplayFormat("MM/yyyy")
            # Truco: Si quisieras elegir febrero 2024, en el calendario seleccionas 
            # CUALQUIER dia de febrero 2024, y el sistema entiende que es todo el mes.
            
        elif periodo == "AÑO":
            # Muestra solo año: 2026
            self.date_selector.setDisplayFormat("yyyy")





    def construir_pagina_reportes_globales(self, widget_padre):
        from PyQt6.QtCore import QDate 

        layout = QVBoxLayout(widget_padre)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter) 

        # TARJETA CENTRAL
        frame_central = QFrame()
        frame_central.setFixedSize(500, 400)
        frame_central.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border-radius: 20px;
                border: 2px solid #334155;
            }
        """)
        lay_frame = QVBoxLayout(frame_central)
        lay_frame.setSpacing(20)
        lay_frame.setContentsMargins(40,40,40,40)

        # Icono o Título
        lbl_titulo = QLabel("GENERADOR DE REPORTES")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setStyleSheet("color: #FACC15; font-size: 24px; font-weight: bold; border: none;")

        lbl_sub = QLabel("Seleccione el periodo para analizar el rendimiento\nde toda la empresa (Ingresos, Bases y Unidades).")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("color: #94A3B8; font-size: 14px; border: none;")

        # CONTROLES (Fecha y Periodo)
        hbox_ctrl = QHBoxLayout()

        self.date_global = QDateEdit()
        self.date_global.setCalendarPopup(True)
        self.date_global.setDate(QDate.currentDate())
        self.date_global.setStyleSheet("background-color: #0F172A; color: white; padding: 10px; border-radius: 5px; font-size: 14px;")

        self.cmb_periodo_global = QComboBox()
        # === AQUI AGREGAMOS 'SIEMPRE' ===
        self.cmb_periodo_global.addItems(["DIA", "MES", "AÑO", "SIEMPRE"]) 
        self.cmb_periodo_global.setStyleSheet("background-color: #0F172A; color: white; padding: 10px; border-radius: 5px; font-size: 14px;")
        
        self.cmb_periodo_global.currentIndexChanged.connect(self.actualizar_formato_global)

        hbox_ctrl.addWidget(self.date_global)
        hbox_ctrl.addWidget(self.cmb_periodo_global)

        # BOTÓN GRANDE
        btn_generar = QPushButton("📄 DESCARGAR REPORTE GLOBAL")
        btn_generar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_generar.setStyleSheet("""
            QPushButton {
                background-color: #00D1FF;
                color: #0F172A;
                font-weight: bold;
                font-size: 16px;
                padding: 15px;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #38BDF8; }
        """)
        btn_generar.clicked.connect(self.generar_pdf_corporativo)

        lay_frame.addWidget(lbl_titulo)
        lay_frame.addWidget(lbl_sub)
        lay_frame.addSpacing(20)
        lay_frame.addLayout(hbox_ctrl)
        lay_frame.addStretch()
        lay_frame.addWidget(btn_generar)

        layout.addWidget(frame_central)
        self.actualizar_formato_global()

    def actualizar_formato_global(self):
        """ Cambia el aspecto del calendario """
        periodo = self.cmb_periodo_global.currentText()
        
        self.date_global.setEnabled(True) # Por defecto activado
        
        if periodo == "DIA": 
            self.date_global.setDisplayFormat("dd/MM/yyyy")
        elif periodo == "MES": 
            self.date_global.setDisplayFormat("MM/yyyy")
        elif periodo == "AÑO": 
            self.date_global.setDisplayFormat("yyyy")
        elif periodo == "SIEMPRE":
            # Si es siempre, deshabilitamos el calendario visualmente
            self.date_global.setDisplayFormat("---")
            self.date_global.setEnabled(False)

    def generar_pdf_corporativo(self):
        """ Acción del botón """
        periodo = self.cmb_periodo_global.currentText()
        qdate = self.date_global.date()
        fecha_str = qdate.toString("yyyy-MM-dd")

        # 1. Obtener Datos
        datos = self.db.obtener_datos_reporte_global(periodo, fecha_str)

        # 2. Texto Fecha Bonita
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        dia = qdate.day()
        mes = meses[qdate.month()]
        anio = qdate.year()

        texto_fecha = ""
        if periodo == "DIA": 
            texto_fecha = f"{dia} de {mes} de {anio}"
        elif periodo == "MES": 
            texto_fecha = f"{mes} {anio}"
        elif periodo == "AÑO": 
            texto_fecha = f"Año {anio}"
        elif periodo == "SIEMPRE":
            # === TEXTO ESPECIAL ===
            texto_fecha = "HISTÓRICO GENERAL (Desde el inicio de operaciones)"

        # 3. PDF
        nombre_pdf = f"Reporte_Global_{periodo}.pdf" # Quitamos fecha del nombre si es SIEMPRE
        if periodo != "SIEMPRE":
            nombre_pdf = f"Reporte_Global_{periodo}_{fecha_str}.pdf"
            
        generador = GeneradorPDF(nombre_pdf)
        generador.generar_reporte_global(periodo, texto_fecha, datos)



    


    
   


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- PANTALLA DE CARGA (SPLASH SCREEN) ---
    # Usamos el logo PNG porque se ve mejor (el ICO es muy pequeño)
    # Asegúrate de usar la función ruta_recurso si ya la implementaste, 
    # o pon el nombre directo si estás probando en código.
    import os
    
    # Truco para encontrar el logo tanto en .py como en .exe
    def ruta_recurso_simple(relativo):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relativo)

    ruta_logo = ruta_recurso_simple("LogoElZorropng.png") # Usa el PNG grande
    
    if os.path.exists(ruta_logo):
        pixmap = QPixmap(ruta_logo)
        
        # Opcional: Escalarlo si es GIGANTE (ej. limitarlo a 400x400)
        pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        splash = QSplashScreen(pixmap)
        splash.show()
        
        # Forzamos a que se pinte en pantalla
        app.processEvents()
        
        # (Opcional) Un pequeño sleep si carga demasiado rápido y quieres presumir el logo
        # import time
        # time.sleep(1.5) 
    else:
        splash = None

    # --- CARGA DE LA VENTANA PRINCIPAL ---
    # Mientras el splash se muestra, aquí Python trabaja cargando la BD y la interfaz
    ventana = VentanaPrincipal()
    ventana.showMaximized()

    # --- CERRAR SPLASH ---
    if splash:
        splash.finish(ventana) # Cierra el splash cuando la ventana esté lista

    sys.exit(app.exec())