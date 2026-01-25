import sys
import os
import shutil
import traceback
import sqlite3
import ctypes
import time
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
from datetime import datetime

# === IMPORTS DE INTERFAZ GRÁFICA (PyQt6) ===
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QLineEdit, 
    QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QListWidget, 
    QPushButton, QListWidgetItem, QDialog, QTableWidgetItem, 
    QComboBox, QDateEdit, QMessageBox, QFrame, QHeaderView,
    QLCDNumber, QStackedWidget, QSplashScreen, QFormLayout, QDialogButtonBox, QTableWidget,
    QScrollArea, QTextEdit,QInputDialog
)
from PyQt6.QtCore import Qt, QSize, QDate, QSharedMemory, QTimer, QTime
from PyQt6.QtGui import QFont, QColor, QPixmap, QPainter, QBrush, QIcon, QPen

# === IMPORTS DE LIBRERÍAS GRÁFICAS Y REPORTE ===
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from gestor_db import GestorBaseDatos
from reportes import GeneradorPDF

# ==========================================
# 1. UTILIDADES GLOBALES Y MANEJO DE ERRORES
# ==========================================

def log_excepciones(type, value, tb):
    texto_error = "".join(traceback.format_exception(type, value, tb))
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("errores_crash.txt", "a", encoding="utf-8") as f:
        f.write(f"\n\n--- ERROR REGISTRADO: {fecha} ---\n{texto_error}\n------------------\n")
    sys.__excepthook__(type, value, tb)

sys.excepthook = log_excepciones

def ruta_recurso(relativo):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relativo)

# ==========================================
# 2. CLASES AUXILIARES (GRÁFICOS E ITEMS)
# ==========================================

class LienzoGrafico(FigureCanvas):
    def __init__(self, parent=None, color_fondo='#1E293B'):
        self.fig = Figure(figsize=(4, 3), dpi=80, facecolor='#0F172A')
        self.axes = self.fig.add_subplot(111)
        self.color_fondo = color_fondo
        self.axes.set_facecolor(self.color_fondo) 
        super().__init__(self.fig)
        self.setParent(parent)
        self.setSizePolicy(self.sizePolicy().Policy.Expanding, self.sizePolicy().Policy.Expanding)

    def actualizar_grafico(self, etiquetas, valores, tipo="dinero"):
        self.axes.clear()
        self.axes.set_facecolor(self.color_fondo)
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
            self.axes.bar(etiquetas, valores, color=c["color"], width=0.6)
            self.axes.set_title(c['titulo'], color=c['color'], fontsize=11, fontweight='bold')
            self.axes.tick_params(axis='x', colors='#00D1FF', labelsize=9, labelrotation=15)
            for label in self.axes.get_xticklabels(): label.set_fontweight('bold')
            self.axes.tick_params(axis='y', colors='#94A3B8', labelsize=8)
            self.axes.spines['top'].set_visible(False)
            self.axes.spines['right'].set_visible(False)
            self.axes.spines['left'].set_visible(False)
            self.axes.spines['bottom'].set_color('#334155')

        self.fig.tight_layout()
        self.draw()

class TaxiItem(QListWidgetItem):
    def __lt__(self, other):
        try: return int(self.text()) < int(other.text())
        except: return self.text() < other.text()

# ==========================================
# 3. VENTANA PRINCIPAL
# ==========================================

class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Taxis El Zorro Manager")
        self.resize(1280, 720)
        
        #flag para que no haga cositas insanas (cuando cargamos los datos al abrirlo)
        self.cargando_datos = False
        
        self.db = GestorBaseDatos("taxis.db")
        self.listas_bases = {} 

        # ESTILOS GENERALES
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #0F172A; color: #E2E8F0; font-family: 'Segoe UI', sans-serif; }
            QTabWidget::pane { border-top: 2px solid #FACC15; background-color: #0F172A; }
            QTabBar::tab { background: #1E293B; color: #94A3B8; padding: 10px 25px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; font-size: 14px; }
            QTabBar::tab:selected { background: #0F172A; color: #FACC15; border-top: 2px solid #FACC15; }
            QLineEdit { background-color: #1E293B; border: 1px solid #334155; border-radius: 5px; color: #FACC15; padding: 5px 10px; font-size: 14px; font-weight: bold; }
            #cajaBase { background-color: #1E293B; border: 2px dashed #334155; border-radius: 10px; }
        """)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        tab_tablero = QWidget()
        tab_admin = QWidget()
        
        self.tabs.addTab(tab_tablero, "TABLERO DE CONTROL")
        self.tabs.addTab(tab_admin, "ADMINISTRACIÓN")
        
        self.init_tablero(tab_tablero)
        self.init_admin(tab_admin)
        
        self.cargar_datos_en_tablero()

        self.timer_semaforo = QTimer(self)
        self.timer_semaforo.timeout.connect(self.cargar_datos_en_tablero)
        self.timer_semaforo.start(60000)

    # ---------------------------------------------------------
    # PESTAÑA 1: TABLERO DE CONTROL (NO TOCAR - ESTÁ BIEN)
    # ---------------------------------------------------------
    def init_tablero(self, tab):
        # 1. BUSCADOR SUPERIOR
        container_buscador = QWidget()
        lc = QHBoxLayout(container_buscador)
        lc.setContentsMargins(0, 0, 10, 0)
        self.txt_buscar_taxi = QLineEdit()
        self.txt_buscar_taxi.setPlaceholderText("🔍 Buscar unidad...")
        self.txt_buscar_taxi.setFixedWidth(200)
        self.txt_buscar_taxi.setStyleSheet("background-color: #1E293B; border: 2px solid #00D1FF; border-radius: 8px; color: white; font-weight: bold;")
        self.txt_buscar_taxi.textChanged.connect(self.busqueda_unificada)
        lc.addWidget(self.txt_buscar_taxi)
        self.tabs.setCornerWidget(container_buscador, Qt.Corner.TopRightCorner)

        layout = QHBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 2. ZONA IZQUIERDA: GRID DE BASES
        zona_bases = QWidget()
        self.grid_bases = QGridLayout(zona_bases)
        self.grid_bases.setSpacing(10)
        self.generar_bases_fisicas()

        # 3. ZONA DERECHA: PANELES ESPECIALES (GRID 2x3)
        zona_derecha = QWidget()
        zona_derecha.setFixedWidth(400) # Ancho para que quepan 2 columnas
        
        scroll = QFrame()
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        # Usamos Grid Layout en lugar de VBox
        layout_derecha_grid = QGridLayout(scroll)
        layout_derecha_grid.setContentsMargins(0, 0, 0, 0)
        layout_derecha_grid.setSpacing(10)

        # Configuración: (ID, Título, Fondo, Borde, Fila, Columna, Span)
        config_cajas = [
            (93, "🏘️ LOCAL",   "#0C4A6E", "#0EA5E9", 0, 0, 1), # Fila 0, Izq
            (92, "🛣️ FORÁNEO", "#1E3A8A", "#3B82F6", 0, 1, 1), # Fila 0, Der
            (91, "🌮 Z2/DESC",  "#581C87", "#A855F7", 1, 0, 1), # Fila 1, Izq
            (90, "🛠️ TALLER",   "#713F12", "#EAB308", 1, 1, 1), # Fila 1, Der
            (12, "⛔ FUERA DE SERVICIO", "#450A0A", "#EF4444", 2, 0, 2) # Fila 2, Todo el ancho
        ]

        for id_bd, titulo, color_bg, color_border, fila, col, span in config_cajas:
            caja = QWidget()
            caja.setMinimumHeight(160) # Altura GRANDE
            caja.setStyleSheet(f"background-color: {color_bg}; border-radius: 12px; border: 3px solid {color_border};")
            
            l = QVBoxLayout(caja)
            l.setContentsMargins(2,5,2,5)
            
            lbl = QLabel(titulo)
            lbl.setStyleSheet(f"color: {color_border}; font-weight: bold; font-size: 15px; border: none; background: transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            lista = QListWidget()
            lista.setObjectName(f"lista_especial_{id_bd}")
            lista.setDragEnabled(True)
            lista.setAcceptDrops(True)
            lista.setDefaultDropAction(Qt.DropAction.MoveAction)
            lista.setDragDropMode(QListWidget.DragDropMode.DragDrop)
            
            lista.setIconSize(QSize(60, 60)) 
            lista.setViewMode(QListWidget.ViewMode.IconMode)
            lista.setResizeMode(QListWidget.ResizeMode.Adjust)
            lista.setSpacing(5)
            
            lista.setStyleSheet(f"""
                QListWidget {{ background: transparent; border: none; }} 
                QListWidget::item {{ 
                    color: white; border-bottom: 1px solid {color_border}; 
                    border-radius: 8px; padding: 2px; font-weight: bold; font-size: 14px; 
                }}
                QListWidget::item:selected {{ background-color: {color_border}; color: black; }}
            """)
            
            # --- CONEXIÓN HÍBRIDA ---
            # 1. Automática para movimientos normales (protegida por flag)
            lista.model().rowsInserted.connect(lambda p, f, l, w=lista: self.detectar_cambio_base(w, f))
            # 2. Manual para Rebotes (soltar en la misma caja)
            lista.dropEvent = lambda event, l=lista: self.evento_drop_especial(event, l)
            
            self.listas_bases[id_bd] = lista
            
            l.addWidget(lbl)
            l.addWidget(lista)
            layout_derecha_grid.addWidget(caja, fila, col, 1, span)

        scroll_area = QScrollArea()
        scroll_area.setWidget(scroll); scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        lay_d_final = QVBoxLayout(zona_derecha)
        lay_d_final.setContentsMargins(0,0,0,0)
        lay_d_final.addWidget(scroll_area)

        layout.addWidget(zona_bases, 1)
        layout.addWidget(zona_derecha, 0)


    def evento_drop_especial(self, event, lista_widget):
        # SI ES REBOTE (Origen == Destino)
        if event.source() == lista_widget:
            event.ignore() # No mover visualmente
            
            # Forzar lógica de "Ligar Viaje"
            item = lista_widget.currentItem() 
            if item:
                fila = lista_widget.row(item)
                # Llamada directa
                self._ejecutar_actualizacion_bd(lista_widget, fila)
        
        # SI ES MOVIMIENTO NORMAL
        else:
            # Dejar que Qt lo mueva y que 'rowsInserted' avise
            QListWidget.dropEvent(lista_widget, event)
            
        
    # ---------------------------------------------------------
    # PESTAÑA 2: ADMINISTRACIÓN
    # ---------------------------------------------------------
    def init_admin(self, tab):
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        
        menu = QWidget()
        menu.setFixedWidth(200)
        menu.setStyleSheet("background-color: #0F172A; border-right: 1px solid #334155;")
        lm = QVBoxLayout(menu)
        lm.setContentsMargins(10, 20, 10, 20)
        
        self.paginas_admin = QStackedWidget()
        
        self.btn_historial = self._crear_btn_menu("📜 Historial Viajes")
        self.btn_flota = self._crear_btn_menu("🚖 Gestión Taxis")
        self.btn_bases = self._crear_btn_menu("🏢 Gestión Bases")
        self.btn_incidencias = self._crear_btn_menu("👮 Reportes y Multas")
        self.btn_reportes = self._crear_btn_menu("📉 Reportes Globales")
        
        self.btn_historial.clicked.connect(lambda: self.cambiar_pagina(0))
        self.btn_flota.clicked.connect(lambda: self.cambiar_pagina(1))
        self.btn_bases.clicked.connect(lambda: self.cambiar_pagina(2))
        self.btn_reportes.clicked.connect(lambda: self.cambiar_pagina(3))
        self.btn_incidencias.clicked.connect(lambda: self.cambiar_pagina(4))
        
        lm.addWidget(self.btn_historial)
        lm.addWidget(self.btn_flota)
        lm.addWidget(self.btn_bases)
        lm.addWidget(self.btn_incidencias)
        lm.addWidget(self.btn_reportes)
        lm.addStretch()

        p1 = QWidget(); self.construir_pagina_historial(p1)
        p2 = QWidget(); self.construir_pagina_flota(p2)
        p3 = QWidget(); self.construir_pagina_bases(p3)
        p4 = QWidget(); self.construir_pagina_reportes_globales(p4)
        p5 = QWidget(); self.construir_pagina_incidencias(p5)
        
        self.paginas_admin.addWidget(p1)
        self.paginas_admin.addWidget(p2)
        self.paginas_admin.addWidget(p3)
        self.paginas_admin.addWidget(p4)
        self.paginas_admin.addWidget(p5)

        layout.addWidget(menu)
        layout.addWidget(self.paginas_admin)
        
        self.tabs.currentChanged.connect(self.al_cambiar_pestana_principal)
        self.btn_historial.setChecked(True)

    def _crear_btn_menu(self, texto):
        btn = QPushButton(texto)
        btn.setCheckable(True)
        btn.setStyleSheet("""
            QPushButton { text-align: left; padding: 10px; border-radius: 5px; color: #94A3B8; font-weight: bold; background: transparent; }
            QPushButton:checked { background-color: #1E293B; color: #FACC15; border-left: 3px solid #FACC15; }
            QPushButton:hover { background-color: #1E293B; color: white; }
        """)
        return btn

    def cambiar_pagina(self, idx):
        self.paginas_admin.setCurrentIndex(idx)
        self.btn_historial.setChecked(idx==0)
        self.btn_flota.setChecked(idx==1)
        self.btn_bases.setChecked(idx==2)
        self.btn_reportes.setChecked(idx==3)
        self.btn_incidencias.setChecked(idx==4)
        
        if idx == 0: self.cargar_historial_en_tabla()
        elif idx == 1: self.cargar_tabla_flota()
        elif idx == 2: self.cargar_tabla_bases()
        elif idx == 4: self.cargar_tabla_deudas()

    # ==========================================
    # LÓGICA DE TABLERO: FICHAS Y MOVIMIENTO
    # ==========================================

    def generar_bases_fisicas(self):
        bases_struct = self.db.obtener_bases_fisicas()
        for i in reversed(range(self.grid_bases.count())): 
            self.grid_bases.itemAt(i).widget().setParent(None)

        fila, columna = 0, 0
        # === CAMBIO: 3 COLUMNAS ===
        max_cols = 3 

        for id_base, nombre in bases_struct:
            # Filtro: Solo bases reales
            if id_base >= 12: continue 

            caja = QWidget()
            caja.setObjectName("cajaBase")
            l = QVBoxLayout(caja)
            l.setContentsMargins(2, 2, 2, 2)
            l.setSpacing(0)
            
            lbl = QLabel(nombre)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #FACC15; font-weight: bold; font-size: 15px; background: transparent;")
            l.addWidget(lbl)

            lista = QListWidget()
            lista.setObjectName(f"lista_base_{id_base}")
            lista.setDragEnabled(True)
            lista.setAcceptDrops(True)
            lista.setDefaultDropAction(Qt.DropAction.MoveAction)
            lista.setDragDropMode(QListWidget.DragDropMode.DragDrop)
            
            lista.model().rowsInserted.connect(lambda p,f,l,w=lista: self.detectar_cambio_base(w, f))
            
            lista.setViewMode(QListWidget.ViewMode.IconMode)
            lista.setResizeMode(QListWidget.ResizeMode.Adjust)
            lista.setIconSize(QSize(60, 50))
            lista.setSpacing(5)
            
            lista.setStyleSheet("""
                QListWidget { background: transparent; border: none; }
                QListWidget::item { border: 2px solid #475569; border-radius: 8px; color: white; font-weight: bold; font-size: 16px; }
            """)

            self.listas_bases[id_base] = lista
            l.addWidget(lista)
            self.grid_bases.addWidget(caja, fila, columna)
            
            columna += 1
            if columna == max_cols: columna = 0; fila += 1

    def cargar_datos_en_tablero(self):
        self.cargando_datos = True 
        
        # --- FABRICANTE DE FICHAS ---
        def crear_chip_visual(numero, color_hex, texto_negro=False):
            size = 85
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Fondo Redondeado
            color = QColor(color_hex)
            painter.setBrush(QBrush(color))
            # Borde sutil para definición
            painter.setPen(QPen(QColor("rgba(0,0,0,0.15)"), 1)) 
            painter.drawRoundedRect(2, 2, size-4, size-4, 14, 14)
            
            # Número
            painter.setPen(QColor("black") if texto_negro else QColor("white"))
            font = QFont("Segoe UI", 22, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, str(numero))
            
            painter.end()
            return QIcon(pixmap)

        # 1. LIMPIEZA
        for id_base, lista in self.listas_bases.items():
            lista.clear()
            lista.setStyleSheet("QListWidget { background: transparent; border: none; }")
            lista.setIconSize(QSize(85, 85)) 
            lista.setSpacing(4)

        taxis = self.db.obtener_taxis_activos()
        ahora = datetime.now()

        for taxi in taxis:
            bid = taxi['base_actual_id']
            if bid in self.listas_bases:
                num_taxi = str(taxi['numero_economico'])
                
                # --- REGLA DE ORO: SIEMPRE AMARILLO ---
                color_hex = "#FACC15" # Amarillo Taxi
                texto_negro = True    # Texto negro para contraste con amarillo
                tooltip_txt = "Normal"

                # Calcular Tiempo
                minutos = 0
                if taxi['fecha_movimiento']:
                    try:
                        dt_mov = datetime.strptime(taxi['fecha_movimiento'], "%Y-%m-%d %H:%M:%S")
                        minutos = (ahora - dt_mov).total_seconds() / 60
                    except: pass
                
                # --- SEMÁFORO (ÚNICA RAZÓN PARA CAMBIAR COLOR) ---
                
                # A) LOCAL (30m / 45m)
                if bid == 93: 
                    if minutos > 45: 
                        color_hex = "#EF4444"; texto_negro = False; tooltip_txt = "DEMORA CRÍTICA" # Rojo
                    elif minutos > 30: 
                        color_hex = "#F97316"; texto_negro = True; tooltip_txt = "Retraso Leve"    # Naranja

                # B) FORÁNEO (90m / 120m)
                elif bid == 92: 
                    if minutos > 120: 
                        color_hex = "#EF4444"; texto_negro = False; tooltip_txt = "URGENTE"
                    elif minutos > 90: 
                        color_hex = "#F97316"; texto_negro = True; tooltip_txt = "Retraso Leve"

                # C) DESCANSO (60m / 90m)
                elif bid == 91:
                    if minutos > 180: # Auto-cierre
                        self.db.actualizar_taxi_base(taxi['id'], 12)
                        self.db.cerrar_turno(taxi['id'])
                        continue
                    if minutos > 90: 
                        color_hex = "#EF4444"; texto_negro = False; tooltip_txt = "Exceso Descanso"
                    elif minutos > 60: 
                        color_hex = "#F97316"; texto_negro = True; tooltip_txt = "Tiempo Límite"

                # 4. CREAR FICHA
                icon_chip = crear_chip_visual(num_taxi, color_hex, texto_negro)
                
                item = TaxiItem("") 
                item.setIcon(icon_chip)
                item.setToolTip(f"Unidad {num_taxi}\n{tooltip_txt}\n{int(minutos)} min")
                
                # Datos ocultos
                item.setData(Qt.ItemDataRole.UserRole, taxi['id'])
                item.setText(num_taxi); item.setForeground(QColor("transparent")) 
                
                item.setSizeHint(QSize(90, 90)) 
                
                self.listas_bases[bid].addItem(item)

        self.cargando_datos = False

    def detectar_cambio_base(self, lista_destino, indice):
        # Si el sistema está cargando datos masivos, no interrumpir
        if self.cargando_datos: 
            return 

        # Usamos un timer muy corto para dejar que la animación de "soltar" termine
        # y luego procesamos la lógica y REFRESCOMOS EL TABLERO
        QTimer.singleShot(50, lambda: self._procesar_y_refrescar(lista_destino, indice))

    def _procesar_y_refrescar(self, lista_destino, indice_item):
        """ Función auxiliar que guarda el cambio y PINTA DE NUEVO EL TABLERO """
        
        # 1. EJECUTAR LA LÓGICA DE BASE DE DATOS (Lo que ya tenías)
        self._ejecutar_actualizacion_bd(lista_destino, indice_item)
        
        # 2. ¡EL SECRETO! FORZAR RE-PINTADO INMEDIATO
        # Esto hará que el taxi evalúe su nuevo estado (Base/Fuera) y se ponga Amarillo/Gris al instante.
        self.cargar_datos_en_tablero()



    def _ejecutar_actualizacion_bd(self, lista_destino, indice_item):
        item = lista_destino.item(indice_item)
        if not item: return

        taxi_id_bd = item.data(Qt.ItemDataRole.UserRole)
        taxi_num = item.text()
        
        # 1. IDENTIFICAR DESTINO
        id_base_nueva = None
        for id_b, w in self.listas_bases.items():
            if w == lista_destino: id_base_nueva = id_b; break
        
        if id_base_nueva and taxi_id_bd:
            # 2. IDENTIFICAR ORIGEN
            conn, cur = self.db._conectar()
            cur.execute("SELECT base_actual_id FROM taxis WHERE id=?", (taxi_id_bd,))
            res = cur.fetchone()
            conn.close()
            id_ant = res['base_actual_id'] if res else 12 
            
            # === LÓGICA DE TURNOS ===
            # Inactivos: 12 (Fuera), 90 (Taller), 91 (Descanso)
            inactivos = [12, 90, 91]
            
            # SALE A TRABAJAR (De Inactivo -> A Activo)
            if id_ant in inactivos and id_base_nueva not in inactivos:
                self.db.abrir_turno(taxi_id_bd)

            # DEJA DE TRABAJAR (De Activo -> A Inactivo)
            elif id_ant not in inactivos and id_base_nueva in inactivos:
                self.db.cerrar_turno(taxi_id_bd)
                self.db.registrar_fin_viaje(taxi_id_bd)

            # --- MANEJO DE VIAJES (Igual que antes) ---
            if id_base_nueva in [92, 93]: # Viajes
                if id_ant in [92, 93]:
                    ans = QMessageBox.question(self, "Ligar", "¿Nuevo viaje?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
                    if ans == QMessageBox.StandardButton.No:
                        lista_destino.sortItems(Qt.SortOrder.AscendingOrder); return
                    self.db.registrar_fin_viaje(taxi_id_bd)
                    self.abrir_ventana_nuevo_viaje(taxi_id_bd, taxi_num, id_ant)
                else:
                    self.abrir_ventana_nuevo_viaje(taxi_id_bd, taxi_num, id_ant)
            elif id_base_nueva <= 11:
                if id_ant in [92, 93]: self.db.registrar_fin_viaje(taxi_id_bd)

            # GUARDAR
            self.db.actualizar_taxi_base(taxi_id_bd, id_base_nueva)
        
        lista_destino.sortItems(Qt.SortOrder.AscendingOrder)

    def evento_drop_viajes(self, event):
        QListWidget.dropEvent(self.lista_viajes, event)
        f = self.lista_viajes.currentRow()
        self.detectar_cambio_base(self.lista_viajes, f)
        self.lista_viajes.sortItems(Qt.SortOrder.AscendingOrder)

    def abrir_ventana_nuevo_viaje(self, taxi_id, taxi_num, id_origen):
        d = QDialog(self)
        d.setWindowTitle(f"🚕 Nuevo Viaje - Unidad {taxi_num}")
        d.setMinimumWidth(350)
        d.setStyleSheet("QDialog { background-color: #1E293B; border: 2px solid #00D1FF; border-radius: 10px; } QLabel { color: #FACC15; font-weight: bold; font-size: 14px; } QLineEdit, QComboBox { background-color: #0F172A; color: white; border: 1px solid #334155; padding: 5px; border-radius: 5px; } QComboBox:disabled { background-color: #334155; color: #94A3B8; }")
        
        l = QVBoxLayout(d)
        f = QFormLayout()
        
        self.cmb_servicio = QComboBox()
        self.cmb_servicio.addItems(["Viaje en base", "Teléfono base", "Teléfono unidad", "Viaje aéreo"])
        
        self.cmb_origen = QComboBox()
        bases_info = self.db.obtener_bases_fisicas() + [(12,'Fuera'),(13,'Calle')]
        idx_def = 0
        for i, (bid, nom) in enumerate(bases_info):
            self.cmb_origen.addItem(nom, bid)
            if bid == id_origen: idx_def = i
        self.cmb_origen.setCurrentIndex(idx_def)
        
        self.cmb_servicio.currentIndexChanged.connect(lambda i: self.cmb_origen.setEnabled(i==0))
        
        self.txt_destino = QLineEdit(); self.txt_destino.setPlaceholderText("¿A dónde va?")
        self.txt_destino.setFocus()
        self.txt_costo = QLineEdit(); self.txt_costo.setPlaceholderText("0.00")
        
        f.addRow("🛠️ Concepto:", self.cmb_servicio)
        f.addRow("🚩 Base Salida:", self.cmb_origen)
        f.addRow("📍 Destino:", self.txt_destino)
        f.addRow("💰 Costo $:", self.txt_costo)
        
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(d.accept); bb.rejected.connect(d.reject)
        
        l.addLayout(f); l.addWidget(bb)
        
        if d.exec() == QDialog.DialogCode.Accepted:
            st = self.cmb_servicio.currentIndex() + 1
            orig = self.cmb_origen.currentData()
            dest = self.txt_destino.text().strip().title()
            try: cost = float(self.txt_costo.text().replace(',', '.'))
            except: cost = 0.0
            self.db.registrar_viaje(taxi_id, st, orig, dest, cost)
            self.db.actualizar_taxi_base(taxi_id, 13)
        else:
            self.cargar_datos_en_tablero()

    # ==========================================
    # LÓGICA DE BÚSQUEDA Y FILTROS
    # ==========================================


    def busqueda_unificada(self, texto):
        idx = self.tabs.currentIndex()
        texto = texto.lower().strip()
        
        # 1. TABLERO
        if idx == 0: 
            self.filtrar_taxis_tablero(texto)
            
        # 2. ADMIN > HISTORIAL
        elif idx == 1 and self.paginas_admin.currentIndex() == 0:
            self.filtrar_tabla_historial(texto)
            
        # 3. ADMIN > REPORTES/INCIDENCIAS (Nueva Lógica)
        elif idx == 1 and self.paginas_admin.currentIndex() == 4:
            self.filtrar_tablas_reportes(texto)

    def filtrar_tablas_reportes(self, texto):
        # Filtramos TABLA DE DEUDAS
        for r in range(self.tabla_deudas.rowCount()):
            taxi = self.tabla_deudas.item(r, 1).text().lower()
            oper = self.tabla_deudas.item(r, 4).text().lower()
            visible = (texto in taxi) or (texto in oper)
            self.tabla_deudas.setRowHidden(r, not visible)
            
        # Filtramos TABLA DE DISCIPLINA
        for r in range(self.tabla_morales.rowCount()):
            taxi = self.tabla_morales.item(r, 1).text().lower()
            fecha = self.tabla_morales.item(r, 4).text().lower() # Buscador por fecha!
            visible = (texto in taxi) or (texto in fecha)
            self.tabla_morales.setRowHidden(r, not visible)

    def filtrar_taxis_tablero(self, texto):
        busq = texto.lower().strip()
        for lista in self.listas_bases.values():
            for i in range(lista.count()):
                it = lista.item(i)
                # PROTECCIÓN ANTI-ERROR:
                if not busq:
                    it.setHidden(False) # Si está vacío, mostrar todo
                else:
                    # BÚSQUEDA EXACTA: "35" debe ser igual a "35"
                    # Si escribes "3", el "35" se oculta (hasta que completes el número)
                    es_igual = (it.text().lower() == busq)
                    it.setHidden(not es_igual)

    def filtrar_tabla_historial(self, texto):
        busq = texto.lower().strip()
        for r in range(self.tabla_reportes.rowCount()):
            it_unidad = self.tabla_reportes.item(r, 3) # Columna Unidad
            it_destino = self.tabla_reportes.item(r, 6) # Columna Destino
            
            if not it_unidad: continue

            if not busq:
                self.tabla_reportes.setRowHidden(r, False)
            else:
                txt_unidad = it_unidad.text().lower()
                txt_destino = it_destino.text().lower() if it_destino else ""

                # LOGICA MIXTA INTELIGENTE:
                # 1. Si es Unidad -> Búsqueda EXACTA (para evitar el problema del 35 vs 350)
                match_unidad = (txt_unidad == busq)
                
                # 2. Si es Destino -> Búsqueda PARCIAL (para encontrar "Tepeaca" escribiendo "tepea")
                match_destino = (busq in txt_destino)

                # Si coincide con alguno de los dos, se muestra. Si no, se oculta.
                self.tabla_reportes.setRowHidden(r, not (match_unidad or match_destino))

    # ==========================================
    # CONSTRUCTORES DE PÁGINAS (ADMIN)
    # ==========================================

    def construir_pagina_historial(self, parent):
        l = QVBoxLayout(parent); l.setContentsMargins(20,20,20,20)
        
        bar = QWidget(); bar.setStyleSheet("background-color: #1E293B; border-radius: 8px;")
        lb = QHBoxLayout(bar)
        
        lbl = QLabel("📅 Mostrar:"); lbl.setStyleSheet("color: #94A3B8; font-weight: bold;")
        self.cmb_filtro_historial = QComboBox()
        self.cmb_filtro_historial.addItems(["HOY", "MES", "AÑO", "SIEMPRE"])
        self.cmb_filtro_historial.setFixedWidth(120)
        self.cmb_filtro_historial.setStyleSheet("QComboBox { background-color: #0F172A; color: white; padding: 5px; border: 1px solid #475569; }")
        self.cmb_filtro_historial.currentIndexChanged.connect(self.cargar_historial_en_tabla)
        
        btn_r = QPushButton("🔄 Actualizar"); btn_r.clicked.connect(self.cargar_historial_en_tabla)
        btn_r.setStyleSheet("color: white; border: 1px solid #475569; padding: 5px; background-color: #334155;")
        
        btn_d = QPushButton("🗑️ Eliminar"); btn_d.clicked.connect(self.eliminar_viaje_seleccionado)
        btn_d.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; padding: 5px 15px;")
        
        lb.addWidget(lbl); lb.addWidget(self.cmb_filtro_historial); lb.addSpacing(10); lb.addWidget(btn_r); lb.addStretch(); lb.addWidget(btn_d)
        
        self.tabla_reportes = QTableWidget()
        self.tabla_reportes.setColumnCount(8)
        self.tabla_reportes.setHorizontalHeaderLabels(["ID","FECHA","HORA","UNIDAD","CONCEPTO","BASE","DESTINO","COSTO"])
        self.tabla_reportes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_reportes.setColumnHidden(0, True)
        self.tabla_reportes.setStyleSheet("QTableWidget { background-color: #1E293B; color: white; border: none; } QHeaderView::section { background-color: #0F172A; color: #FACC15; padding: 5px; } QTableWidget::item:selected { background-color: #334155; }")
        self.tabla_reportes.cellChanged.connect(self.guardar_edicion_tabla)
        
        l.addWidget(bar); l.addWidget(self.tabla_reportes)

    def cargar_historial_en_tabla(self):
        # Desconectamos señal para evitar bucles al limpiar
        try: self.tabla_reportes.cellChanged.disconnect()
        except: pass
        
        self.tabla_reportes.setRowCount(0)
        f = self.cmb_filtro_historial.currentText()
        viajes = self.db.obtener_historial_viajes(f)
        
        # Diccionario para traducir IDs a texto
        servs = {1:"Viaje Base", 2:"Tel Base", 3:"Tel Unidad", 4:"Aéreo"}
        
        for d in viajes:
            r = self.tabla_reportes.rowCount()
            self.tabla_reportes.insertRow(r)
            
            # --- CORRECCIÓN DEL ERROR ---
            # Usamos acceso directo [] en lugar de .get()
            # La columna 'tipo_servicio_id' SIEMPRE viene de la BD
            ids = d['tipo_servicio_id']
            
            # Lógica para mostrar nombre de base solo si es 'Viaje en Base' (ID 1)
            nom_b = d['nombre_base'] if ids == 1 else "////"
            
            # Formato de Fecha y Hora
            fh = str(d['fecha_hora_inicio']).split(" ")
            f_date = fh[0]
            h_time = fh[1][:5] if len(fh)>1 else ""
            
            # Llenado de columnas (Protegemos con str() por si algo es None)
            self.tabla_reportes.setItem(r, 0, QTableWidgetItem(str(d['id'])))
            self.tabla_reportes.setItem(r, 1, QTableWidgetItem(f_date))
            self.tabla_reportes.setItem(r, 2, QTableWidgetItem(h_time))
            self.tabla_reportes.setItem(r, 3, QTableWidgetItem(str(d['numero_economico'])))
            self.tabla_reportes.setItem(r, 4, QTableWidgetItem(servs.get(ids, "-"))) # servs es dict normal, aquí si sirve .get
            self.tabla_reportes.setItem(r, 5, QTableWidgetItem(str(nom_b or "")))
            self.tabla_reportes.setItem(r, 6, QTableWidgetItem(str(d['destino'] or "")))
            self.tabla_reportes.setItem(r, 7, QTableWidgetItem(str(d['precio'])))
            
        # Reconectamos la señal de edición
        self.tabla_reportes.cellChanged.connect(self.guardar_edicion_tabla)
        
    def guardar_edicion_tabla(self, r, c):
        vid = self.tabla_reportes.item(r,0).text()
        val = self.tabla_reportes.item(r,c).text()
        col = "destino" if c==6 else "precio" if c==7 else None
        if col: self.db.actualizar_viaje(vid, col, val)

    def eliminar_viaje_seleccionado(self):
        r = self.tabla_reportes.currentRow()
        if r >= 0:
            vid = self.tabla_reportes.item(r,0).text()
            if self.db.eliminar_viaje(vid): self.tabla_reportes.removeRow(r)

    def al_cambiar_pestana_principal(self, i):
        if i == 1: self.cargar_historial_en_tabla()

    # ---------------------------------------------------------
    # GESTIÓN FLOTA - ARREGLADO VISUALMENTE
    # ---------------------------------------------------------
    def construir_pagina_flota(self, parent):
        layout = QHBoxLayout(parent)
        
        # Izquierda (Tabla)
        frame_t = QFrame(); frame_t.setFixedWidth(420) # Un poco más ancho para que quepan 4 columnas
        lt = QVBoxLayout(frame_t); lt.setContentsMargins(0,0,10,0)
        
        fa = QFrame(); fa.setStyleSheet("background-color: #1E293B; border-radius: 5px;")
        la = QHBoxLayout(fa)
        self.txt_nuevo_taxi = QLineEdit(); self.txt_nuevo_taxi.setPlaceholderText("Nuevo #")
        btn_add = QPushButton("➕ Alta"); btn_add.setStyleSheet("background-color: #10B981; color: white; padding: 5px;")
        btn_add.clicked.connect(self.registrar_nuevo_taxi_ui)
        la.addWidget(self.txt_nuevo_taxi); la.addWidget(btn_add)
        
        # === CAMBIO: 4 COLUMNAS (UNIDAD, ESTADO, ACT/DES, BAJA) ===
        self.tabla_flota = QTableWidget(); self.tabla_flota.setColumnCount(4)
        self.tabla_flota.setHorizontalHeaderLabels(["UNIDAD","ESTADO","ACT/DES","BAJA"])
        self.tabla_flota.setStyleSheet("QTableWidget { background-color: #1E293B; color: white; border: none; } QHeaderView::section { background-color: #0F172A; color: #FACC15; }")
        self.tabla_flota.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_flota.itemClicked.connect(self.al_clic_tabla_flota)
        
        lt.addWidget(fa); lt.addWidget(self.tabla_flota)
        
        # Derecha (Reporte)
        frame_s = QFrame(); frame_s.setStyleSheet("background-color: #0F172A; border-left: 2px solid #334155;")
        ls = QVBoxLayout(frame_s); ls.setContentsMargins(20,20,20,20)
        
        # Header Stats
        hs = QHBoxLayout()
        hs.addWidget(QLabel("Fecha Ref:"))
        
        # === CAMBIO: PREDETERMINADO SIEMPRE HOY ===
        self.date_selector = QDateEdit(); self.date_selector.setCalendarPopup(True)
        self.date_selector.setDate(QDate.currentDate()) # Siempre hoy al abrir
        self.date_selector.setStyleSheet("background-color: #1E293B; color: white; padding: 5px;")
        self.date_selector.dateChanged.connect(self.buscar_stats_por_input)
        
        self.cmb_periodo_stats = QComboBox(); self.cmb_periodo_stats.addItems(["DIA","MES","AÑO"])
        self.cmb_periodo_stats.setCurrentIndex(0) # Siempre "DIA" al abrir (Index 0)
        self.cmb_periodo_stats.setStyleSheet("background-color: #1E293B; color: white; padding: 5px;")
        self.cmb_periodo_stats.currentIndexChanged.connect(self.actualizar_formato_fecha_unit)
        self.cmb_periodo_stats.currentIndexChanged.connect(self.buscar_stats_por_input)
        
        hs.addWidget(self.date_selector); hs.addWidget(self.cmb_periodo_stats)
        
        # Input Taxi
        hi = QHBoxLayout()
        lbl_t = QLabel("Taxi:"); lbl_t.setStyleSheet("color: #00D1FF; font-size: 40px; font-weight: bold;")
        self.txt_taxi_selec = QLineEdit(); self.txt_taxi_selec.setPlaceholderText("#"); self.txt_taxi_selec.setFixedWidth(180)
        self.txt_taxi_selec.setStyleSheet("color: #00D1FF; font-size: 40px; border: none; border-bottom: 3px solid #334155; background: transparent;")
        self.txt_taxi_selec.textChanged.connect(self.buscar_stats_por_input)
        
        btn_pdf = QPushButton("🖨️ PDF"); btn_pdf.setFixedSize(80,50)
        btn_pdf.setStyleSheet("background-color: #F87171; color: white; font-weight: bold; border-radius: 8px;")
        btn_pdf.clicked.connect(self.exportar_pdf_unidad)
        
        hi.addWidget(lbl_t); hi.addWidget(self.txt_taxi_selec); hi.addSpacing(10); hi.addWidget(btn_pdf); hi.addStretch()
        
        # Tarjetas
        ht = QHBoxLayout(); ht.setSpacing(15)
        def mk_card(tit, col, ico):
            f = QFrame(); f.setStyleSheet(f"background-color: #1E293B; border-radius: 10px; border-left: 10px solid {col};")
            f.setMinimumHeight(110)
            vl = QVBoxLayout(f)
            lt = QLabel(f"{ico} {tit}"); lt.setStyleSheet(f"color: {col}; font-size: 16px; font-weight: bold; border: none; background: transparent;")
            v = QLabel("0"); v.setAlignment(Qt.AlignmentFlag.AlignRight); v.setStyleSheet("color: white; font-size: 45px; font-weight: bold; border: none; background: transparent;")
            vl.addWidget(lt); vl.addWidget(v)
            return f, v
            
        c1, self.lbl_stat_dinero = mk_card("GANANCIAS", "#FACC15", "💰")
        c2, self.lbl_stat_viajes = mk_card("VIAJES", "#10B981", "🚖")
        c3, self.lbl_stat_horas = mk_card("HORAS", "#F472B6", "⏱️")
        ht.addWidget(c1); ht.addWidget(c2); ht.addWidget(c3)
        
        zg = QFrame(); zg.setStyleSheet("border-radius: 10px; background-color: #0F172A;")
        hg = QHBoxLayout(zg); hg.setContentsMargins(0,0,0,0)
        self.grafico_dinero = LienzoGrafico(zg); self.grafico_viajes = LienzoGrafico(zg); self.grafico_horas = LienzoGrafico(zg)
        hg.addWidget(self.grafico_dinero); hg.addWidget(self.grafico_viajes); hg.addWidget(self.grafico_horas)
        
        ls.addLayout(hs); ls.addLayout(hi); ls.addLayout(ht); ls.addSpacing(20); ls.addWidget(zg, 1)
        layout.addWidget(frame_t); layout.addWidget(frame_s, 1)
        self.actualizar_formato_fecha_unit()


    def cargar_tabla_flota(self):
        self.tabla_flota.setRowCount(0)
        flota = self.db.obtener_toda_la_flota()
        try: flota.sort(key=lambda x: int(x['numero_economico']))
        except: pass
        
        for t in flota:
            r = self.tabla_flota.rowCount()
            self.tabla_flota.insertRow(r)
            
            # Col 0: Unidad
            it = QTableWidgetItem(str(t['numero_economico'])); it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_flota.setItem(r,0,it)
            
            # Col 1: Estado
            est = t['estado_sistema']
            ie = QTableWidgetItem(est); ie.setForeground(QColor("green") if est=="ACTIVO" else QColor("red"))
            ie.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.tabla_flota.setItem(r,1,ie)
            
            # Col 2: Activar/Desactivar
            b_act = QPushButton("APAGAR" if est=="ACTIVO" else "ENCENDER")
            b_act.setStyleSheet(f"background-color: {'#334155' if est=='ACTIVO' else '#10B981'}; color: {'#94A3B8' if est=='ACTIVO' else 'white'}; font-weight: bold; border: none;")
            b_act.clicked.connect(lambda _, tid=t['id'], e=est: self.alternar_estado_taxi(tid, e))
            self.tabla_flota.setCellWidget(r,2,b_act)

            # Col 3: ELIMINAR (Nuevo)
            b_del = QPushButton("X")
            b_del.setFixedWidth(40)
            b_del.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; border-radius: 4px;")
            b_del.clicked.connect(lambda _, tid=t['id'], num=t['numero_economico']: self.eliminar_taxi_ui(tid, num))
            self.tabla_flota.setCellWidget(r,3,b_del)


    def al_clic_tabla_flota(self, item):
        r = self.tabla_flota.currentRow()
        if r>=0: self.txt_taxi_selec.setText(self.tabla_flota.item(r,0).text())

    def buscar_stats_por_input(self):
        num = self.txt_taxi_selec.text().strip()
        per = self.cmb_periodo_stats.currentText()
        fstr = self.date_selector.date().toString("yyyy-MM-dd")
        
        # 1. LIMPIEZA: Si no hay número escrito...
        if not num:
            self.lbl_stat_dinero.setText("$0.00")
            self.lbl_stat_viajes.setText("0")
            self.lbl_stat_horas.setText("0.0 h")
            
            # Limpiamos gráficas
            self.grafico_dinero.actualizar_grafico([],[],"dinero")
            self.grafico_viajes.actualizar_grafico([],[],"viajes") 
            self.grafico_horas.actualizar_grafico([],[],"horas")
            
            # RESTAURAR COLORES ORIGINALES EN LA TABLA (Quitar resaltado)
            for r in range(self.tabla_flota.rowCount()):
                self.tabla_flota.setRowHidden(r, False) # Asegurar que todos se vean
                for c in range(3):
                    it = self.tabla_flota.item(r, c)
                    if it:
                        it.setBackground(QColor("#1E293B")) # Fondo original oscuro
                        # Restaurar color de texto según columna
                        if c == 1: # Columna Estado (Verde/Rojo)
                            est = it.text()
                            it.setForeground(QColor("green") if est=="ACTIVO" else QColor("red"))
                        else:
                            it.setForeground(QColor("white"))
            return
        
        # 2. BÚSQUEDA DE DATOS (BD)
        tid = self.db.obtener_id_por_numero(num)
        if tid:
            stats = self.db.obtener_estadisticas_unidad(tid, per, fecha_ref=fstr)
            self.lbl_stat_dinero.setText(f"${stats['ganancia']:,.2f}")
            self.lbl_stat_viajes.setText(str(stats['viajes']))
            self.lbl_stat_horas.setText(f"{stats['horas']:.1f} h")
            
            pg = "AÑO" if per=="SIEMPRE" else per
            d = self.db.obtener_datos_tres_graficas(tid, pg, fecha_ref=fstr)
            self.grafico_dinero.actualizar_grafico(d["etiquetas"], d["dinero"], "dinero")
            self.grafico_viajes.actualizar_grafico(d["etiquetas"], d["viajes"], "viajes")
            self.grafico_horas.actualizar_grafico(d["etiquetas"], d["horas"], "horas")
        else:
             self.lbl_stat_dinero.setText("ERROR")

        # 3. RESALTADO VISUAL EN LA TABLA (NUEVA LÓGICA)
        for r in range(self.tabla_flota.rowCount()):
            it = self.tabla_flota.item(r, 0) # Item con el número del taxi
            self.tabla_flota.setRowHidden(r, False) # Siempre mostrar la fila
            
            if it and it.text() == num:
                # ¡COINCIDENCIA! -> PINTAR DE AMARILLO Y TEXTO NEGRO
                for c in range(3):
                    cell = self.tabla_flota.item(r, c)
                    if cell: 
                        cell.setBackground(QColor("#FACC15")) # Amarillo Neón
                        cell.setForeground(QColor("black"))   # Contraste
                
                # Hacer scroll automático hacia el taxi encontrado
                self.tabla_flota.scrollToItem(it)
                
            else:
                # NO COINCIDE -> RESTAURAR COLOR ORIGINAL OSCURO
                for c in range(3):
                    cell = self.tabla_flota.item(r, c)
                    if cell: 
                        cell.setBackground(QColor("#1E293B")) # Fondo Original
                        # Respetar colores de texto (Verde/Rojo en estado)
                        if c == 1:
                            est = cell.text()
                            cell.setForeground(QColor("green") if est=="ACTIVO" else QColor("red"))
                        else:
                            cell.setForeground(QColor("white"))


    def registrar_nuevo_taxi_ui(self):
        n = self.txt_nuevo_taxi.text().strip()
        if n and self.db.registrar_nuevo_taxi(n, id_base_inicial=12):
            self.txt_nuevo_taxi.clear()
            self.cargar_tabla_flota(); self.cargar_datos_en_tablero()

    def alternar_estado_taxi(self, tid, est):
        n = "INACTIVO" if est=="ACTIVO" else "ACTIVO"
        if self.db.cambiar_estado_taxi(tid, n):
            self.cargar_tabla_flota(); self.cargar_datos_en_tablero()

    def eliminar_taxi_ui(self, taxi_id, numero):
        # Creamos una caja de mensaje personalizada para tener control total
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Critical) # Icono de ERROR rojo
        msg.setWindowTitle("⚠️ PELIGRO - ELIMINACIÓN PERMANENTE")
        
        # Texto con formato HTML para que sea GRANDE y ROJO
        texto_alerta = f"""
        <h2 style='color: #EF4444;'>¡ALTO! ¿ESTÁS SEGURO?</h2>
        <p style='font-size: 14px; color: white;'>
            Estás a punto de eliminar definitivamente el <b>TAXI {numero}</b>.
        </p>
        <ul style='font-size: 13px; color: #E2E8F0;'>
            <li>❌ Se borrarán todos sus <b>VIAJES HISTÓRICOS</b>.</li>
            <li>❌ Se borrarán sus <b>GANANCIAS Y MULTAS</b>.</li>
            <li>❌ Desaparecerá de los <b>REPORTES</b>.</li>
        </ul>
        <p style='font-size: 15px; color: #EF4444; font-weight: bold;'>
            ESTA ACCIÓN ES IRREVERSIBLE.<br>NO SE PUEDE RECUPERAR.
        </p>
        """
        msg.setText(texto_alerta)
        
        # Botones personalizados
        # El rol 'DestructiveRole' le dice al sistema que es un botón peligroso
        btn_borrar = msg.addButton("💀 SÍ, BORRAR DEFINITIVAMENTE", QMessageBox.ButtonRole.DestructiveRole)
        btn_cancelar = msg.addButton("CANCELAR OPERACIÓN", QMessageBox.ButtonRole.RejectRole)
        
        # ESTILO DEL POPUP (Para que combine con tu tema oscuro y resalte la alerta)
        msg.setStyleSheet("""
            QMessageBox { background-color: #1E293B; border: 2px solid #EF4444; }
            QLabel { color: white; }
            QPushButton { padding: 10px; font-weight: bold; border-radius: 5px; }
            QPushButton[text*="CANCELAR"] { background-color: #10B981; color: white; min-width: 120px; }
            QPushButton[text*="BORRAR"] { background-color: #7F1D1D; color: #FECACA; border: 1px solid #EF4444; }
            QPushButton[text*="BORRAR"]:hover { background-color: #EF4444; color: white; }
        """)

        # TRUCO DE SEGURIDAD:
        # Ponemos el foco en "CANCELAR". Si dan Enter rápido, se cancela.
        msg.setDefaultButton(btn_cancelar)
        msg.setEscapeButton(btn_cancelar)

        msg.exec()

        # Solo si hizo clic explícitamente en el botón de borrar
        if msg.clickedButton() == btn_borrar:
            if self.db.eliminar_taxi(taxi_id):
                self.txt_taxi_selec.clear()
                self.cargar_tabla_flota()
                self.cargar_datos_en_tablero()
                QMessageBox.information(self, "Eliminado", f"El taxi {numero} ha sido borrado del sistema.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo eliminar el taxi.")          

    def actualizar_formato_fecha_unit(self):
        p = self.cmb_periodo_stats.currentText()
        self.date_selector.setDisplayFormat("dd/MM/yyyy" if p=="DIA" else "MM/yyyy" if p=="MES" else "yyyy")

    def exportar_pdf_unidad(self):
        # 1. Obtener datos de la UI
        idx = self.combo_taxi_reporte.currentIndex()
        if idx < 0: return
        taxi_id = self.combo_taxi_reporte.itemData(idx)
        taxi_num = self.combo_taxi_reporte.currentText()
        
        periodo_idx = self.combo_periodo_reporte.currentIndex() # 0=Dia, 1=Mes
        periodo = "DIA" if periodo_idx == 0 else "MES"
        
        # Fecha correcta
        fecha_dt = self.date_reporte.date().toPyDate()
        fecha_str = fecha_dt.strftime("%Y-%m-%d")

        # 2. Generar nombre de archivo único (con Hora-Minuto-Segundo para evitar choques)
        timestamp = datetime.now().strftime("%H%M%S")
        nombre_pdf = f"Reporte_{taxi_num}_{timestamp}.pdf"
        
        # Carpeta de Documentos
        ruta_docs = os.path.join(os.path.expanduser("~"), "Documents", "Reportes Taxis El Zorro")
        if not os.path.exists(ruta_docs): os.makedirs(ruta_docs)
        
        ruta_completa = os.path.join(ruta_docs, nombre_pdf)

        # 3. Obtener datos de la BD
        datos = self.db.obtener_viajes_por_unidad_y_periodo(taxi_id, periodo, fecha_ref=fecha_str)
        stats = self.db.obtener_estadisticas_unidad(taxi_id, periodo, fecha_ref=fecha_str)

        if not datos and stats['viajes'] == 0:
            QMessageBox.warning(self, "Sin datos", "No hay viajes registrados para este periodo.")
            return

        # 4. CREAR EL PDF (Blindado contra errores de escritura)
        try:
            c = canvas.Canvas(ruta_completa, pagesize=letter)
            ancho, alto = letter

            # --- ENCABEZADO ---
            c.setFont("Helvetica-Bold", 18)
            c.drawString(50, alto - 50, f"REPORTE DE UNIDAD: TAXI {taxi_num}")
            
            c.setFont("Helvetica", 10)
            c.drawString(50, alto - 70, f"Fecha de Corte: {fecha_str}")
            c.drawString(50, alto - 85, f"Periodo: {periodo}")
            c.drawString(400, alto - 50, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            # --- RESUMEN ---
            c.setStrokeColorRGB(0, 0, 0)
            c.rect(50, alto - 140, 500, 40)
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(70, alto - 125, f"Viajes Totales: {stats['viajes']}")
            c.drawString(250, alto - 125, f"Ingreso Total: ${stats['ganancia']:.2f}")
            c.drawString(450, alto - 125, f"Horas Activas: {stats['horas']:.1f}h")

            # --- TABLA DE VIAJES ---
            y = alto - 180
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y, "HORA")
            c.drawString(150, y, "ORIGEN")
            c.drawString(300, y, "DESTINO")
            c.drawString(500, y, "PRECIO")
            c.line(50, y-5, 550, y-5)
            y -= 20

            c.setFont("Helvetica", 9)
            for d in datos:
                if y < 50: # Salto de página simple
                    c.showPage()
                    y = alto - 50
                
                # Formato de hora (solo hora si es reporte diario)
                try:
                    hora_show = d['fecha'].split(" ")[1][:5] # "14:30"
                except: hora_show = d['fecha']

                c.drawString(50, y, hora_show)
                c.drawString(150, y, str(d['origen'])[:25]) # Recortar si es largo
                c.drawString(300, y, str(d['destino'])[:35])
                c.drawString(500, y, f"${d['precio']:.2f}")
                y -= 15

            c.save() # Aquí se guarda y cierra el archivo
            
        except PermissionError:
            QMessageBox.critical(self, "Error", "No se pudo guardar el PDF.\nEs posible que el archivo esté abierto en otro programa.")
            return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generando PDF: {e}")
            return

        # 5. ABRIR EL ARCHIVO AUTOMÁTICAMENTE (Intento seguro)
        try:
            os.startfile(ruta_completa)
        except Exception as e:
            # Si falla abrirlo (porque no hay lector PDF o permisos), solo avisamos en consola y seguimos.
            print(f"Aviso: El PDF se creó pero no se pudo abrir automáticamente: {e}")
            QMessageBox.information(self, "PDF Creado", f"Reporte guardado en:\n{ruta_completa}")
    # ---------------------------------------------------------
    # GESTIÓN reportes (Página 4 Admin)
    # ---------------------------------------------------------

    def construir_pagina_incidencias(self, parent):
        layout = QHBoxLayout(parent)
        
        # --- LADO IZQUIERDO: FORMULARIO ---
        frame_form = QFrame()
        frame_form.setFixedWidth(400) # Un poco más ancho para que se vea bien
        frame_form.setStyleSheet("background-color: #1E293B; border-radius: 10px;")
        lf = QVBoxLayout(frame_form)
        lf.setSpacing(15) # Más espacio entre elementos
        
        # Estilo para etiquetas grandes
        estilo_lbl = "font-size: 14px; font-weight: bold; color: #94A3B8;"
        estilo_in = "font-size: 14px; padding: 5px; background-color: #0F172A; color: white; border: 1px solid #334155; border-radius: 5px;"

        # Banderola
        banderola_hoy = self.db.calcular_banderola_del_dia()
        lbl_banderola = QLabel(f"🚩 BANDEROLA HOY: TAXI {banderola_hoy}")
        lbl_banderola.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_banderola.setStyleSheet("background-color: #F59E0B; color: black; font-weight: bold; font-size: 18px; padding: 10px; border-radius: 5px;")
        lf.addWidget(lbl_banderola)
        lf.addSpacing(10)

        lf.addWidget(QLabel("📝 LEVANTAR REPORTE", styleSheet="font-size: 18px; color: white; font-weight: bold;"))
        
        self.txt_taxi_reporte = QLineEdit(); self.txt_taxi_reporte.setPlaceholderText("Número Taxi")
        self.txt_taxi_reporte.setStyleSheet(estilo_in)
        
        self.cmb_tipo_incidencia = QComboBox()
        self.cmb_tipo_incidencia.addItems(["⚠️ Reporte Disciplina", "🛑 Multa Horas", "🚩 Falta Banderolas", "🚫 Ausencia", "💸 Deuda"])
        self.cmb_tipo_incidencia.setStyleSheet(estilo_in)
        
        # --- CAMBIO IMPORTANTE: CUADRO GRANDE ---
        self.txt_desc_reporte = QTextEdit() 
        self.txt_desc_reporte.setPlaceholderText("Escribe aquí los detalles del reporte...")
        self.txt_desc_reporte.setMaximumHeight(120) # Altura fija grande
        self.txt_desc_reporte.setStyleSheet(estilo_in)
        
        self.txt_monto_multa = QLineEdit(); self.txt_monto_multa.setPlaceholderText("Monto $ (0 si es reporte)")
        self.txt_monto_multa.setText("0")
        self.txt_monto_multa.setStyleSheet(estilo_in)
        
        self.txt_operadora = QLineEdit(); self.txt_operadora.setPlaceholderText("Tu Nombre")
        self.txt_operadora.setStyleSheet(estilo_in)
        
        btn_guardar = QPushButton("💾 GUARDAR INCIDENCIA")
        btn_guardar.clicked.connect(self.guardar_incidencia)
        btn_guardar.setStyleSheet("background-color: #EF4444; color: white; padding: 12px; font-weight: bold; font-size: 14px; border-radius: 5px;")
        
        # Agregamos widgets con etiquetas
        lf.addWidget(QLabel("Unidad:", styleSheet=estilo_lbl)); lf.addWidget(self.txt_taxi_reporte)
        lf.addWidget(QLabel("Tipo de Problema:", styleSheet=estilo_lbl)); lf.addWidget(self.cmb_tipo_incidencia)
        lf.addWidget(QLabel("Detalles / Observaciones:", styleSheet=estilo_lbl)); lf.addWidget(self.txt_desc_reporte)
        lf.addWidget(QLabel("Monto a Cobrar ($):", styleSheet=estilo_lbl)); lf.addWidget(self.txt_monto_multa)
        lf.addWidget(QLabel("Firma Operadora:", styleSheet=estilo_lbl)); lf.addWidget(self.txt_operadora)
        lf.addSpacing(10); lf.addWidget(btn_guardar); lf.addStretch()
        
        # --- LADO DERECHO: PESTAÑAS ---
        frame_list = QFrame()
        ll = QVBoxLayout(frame_list)
        
        h_aud = QHBoxLayout()
        self.date_auditoria = QDateEdit(); self.date_auditoria.setCalendarPopup(True); self.date_auditoria.setDate(QDate.currentDate().addDays(-1))
        self.date_auditoria.setStyleSheet(estilo_in)
        btn_auditar = QPushButton("📋 REVISIÓN DE JORNADA")
        btn_auditar.setStyleSheet("background-color: #00D1FF; color: black; font-weight: bold; padding: 8px; font-size: 13px;")
        btn_auditar.clicked.connect(self.ejecutar_auditoria_horas)
        h_aud.addWidget(QLabel("Revisar día:", styleSheet=estilo_lbl)); h_aud.addWidget(self.date_auditoria); h_aud.addWidget(btn_auditar)
        
        # SISTEMA DE PESTAÑAS
        self.tabs_incidencias_panel = QTabWidget()
        self.tabs_incidencias_panel.setStyleSheet("QTabWidget::pane { border: 1px solid #334155; } QTabBar::tab { font-size: 13px; }")
        
        # Pestaña 1: COBROS (La que tenías antes)
        self.tabla_deudas = QTableWidget(); self.tabla_deudas.setColumnCount(6)
        self.tabla_deudas.setHorizontalHeaderLabels(["ID", "TAXI", "TIPO", "MONTO", "OPER", "COBRAR"])
        self.tabla_deudas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_deudas.setStyleSheet("QTableWidget { background-color: #0F172A; color: white; font-size: 13px; }")

        # Pestaña 2: DISCIPLINA (Nueva)
        self.tabla_morales = QTableWidget(); self.tabla_morales.setColumnCount(5)
        self.tabla_morales.setHorizontalHeaderLabels(["ID", "TAXI", "TIPO", "DETALLES", "FECHA"])
        self.tabla_morales.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_morales.setStyleSheet("QTableWidget { background-color: #0F172A; color: white; font-size: 13px; }")

        self.tabs_incidencias_panel.addTab(self.tabla_deudas, "💰 COBROS PENDIENTES")
        self.tabs_incidencias_panel.addTab(self.tabla_morales, "📋 DISCIPLINA / AUSENCIAS")
        
        ll.addLayout(h_aud)
        ll.addWidget(self.tabs_incidencias_panel)
        
        layout.addWidget(frame_form); layout.addWidget(frame_list)
        
        # Conexión automática de texto
        self.cmb_tipo_incidencia.currentTextChanged.connect(self.auto_llenar_descripcion_incidencia)
    

    def ejecutar_auditoria_horas(self):
        # --- PROTECCIÓN: VERIFICAR SI YA SE HIZO HOY ---
        if self.db.ya_se_hizo_auditoria_hoy():
            QMessageBox.warning(self, "🛑 Alto ahí", "La auditoría automática YA se ejecutó el día de hoy.\n\nNo es necesario volver a correrla para evitar duplicar multas.")
            return
        # -----------------------------------------------
        fecha = self.date_auditoria.date().toString("yyyy-MM-dd")
        candidatos = self.db.auditoria_inteligente(fecha)
        
        if not candidatos:
            QMessageBox.information(self, "Excelente", "¡Todos cumplieron sus horas ese día!")
            return
            
        ausentes = [c for c in candidatos if c['tipo'] == 'AUSENCIA']
        multas = [c for c in candidatos if c['tipo'] == 'MULTA']
        
        msg = f"<b>RESULTADOS DE LA AUDITORÍA:</b><br><br>"
        msg += f"🔴 <b>{len(multas)} Multas por Horas</b> (Se cobrarán automáticamente)<br>"
        msg += f"🟡 <b>{len(ausentes)} Ausencias</b> (Se generará reporte administrativo)<br><br>"
        msg += "¿Deseas aplicar estos reportes en el sistema?"
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Auditoría Finalizada")
        msg_box.setText(msg)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            # Procesar Multas (Cobro)
            for m in multas:
                self.db.registrar_incidencia(m['taxi_id'], "🛑 Multa Horas", m['motivo'], m['monto'], "SISTEMA")
            
            # Procesar Ausencias (Solo reporte)
            for a in ausentes:
                self.db.registrar_incidencia(a['taxi_id'], "🚫 Ausencia", a['motivo'], 0.0, "SISTEMA")
                
            self.cargar_tabla_deudas()
            QMessageBox.information(self, "Aplicado", "Se han generado todos los cargos y reportes.")

    def guardar_incidencia(self):
        num = self.txt_taxi_reporte.text()
        tid = self.db.obtener_id_por_numero(num)
        if not tid:
            QMessageBox.warning(self, "Error", "Taxi no encontrado")
            return
            
        tipo = self.cmb_tipo_incidencia.currentText()
        
        # --- CAMBIO: USAMOS .toPlainText() PARA EL CUADRO GRANDE ---
        desc = self.txt_desc_reporte.toPlainText() 
        
        oper = self.txt_operadora.text()
        if not desc or not oper:
            QMessageBox.warning(self, "Faltan datos", "Debes poner descripción y tu nombre.")
            return

        try: monto = float(self.txt_monto_multa.text())
        except: monto = 0.0
        
        if self.db.registrar_incidencia(tid, tipo, desc, monto, oper):
            QMessageBox.information(self, "Registrado", "Reporte guardado con éxito.")
            
            # Limpiar
            self.txt_desc_reporte.clear(); self.txt_monto_multa.setText("0")
            self.cargar_tabla_deudas() # Recarga ambas pestañas

    def auto_llenar_descripcion_incidencia(self, texto):
        descripciones = {
            "🛑 Multa Horas": "Incumplimiento de jornada laboral mínima (10 horas).",
            
            # --- NUEVA DESCRIPCIÓN OPERATIVA ESPECÍFICA ---
            "🚩 Falta Banderolas": "No colocó la banderola metálica en la base designada (5, 6 u 11) para apartar el lugar autorizado.",
            
            "🚫 Ausencia": "Ausencia injustificada del chofer en su turno asignado.",
            "⚠️ Reporte Disciplina": "",
            "💸 Deuda": "Adeudo registrado manualmente."
        }
        self.txt_desc_reporte.setPlainText(descripciones.get(texto, ""))


    def cargar_tabla_deudas(self):
        # 1. Limpiamos AMBAS tablas
        self.tabla_deudas.setRowCount(0)
        self.tabla_morales.setRowCount(0)
        
        # Ajustamos columnas para que quepa el botón PDF
        # Tabla Deudas: ID, TAXI, TIPO, MONTO, OPER, COBRAR, PDF
        self.tabla_deudas.setColumnCount(7) 
        self.tabla_deudas.setHorizontalHeaderLabels(["ID", "TAXI", "TIPO", "MONTO", "OPER", "COBRAR", "PDF"])
        self.tabla_deudas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Tabla Morales: ID, TAXI, TIPO, DETALLES, FECHA, PDF
        self.tabla_morales.setColumnCount(6)
        self.tabla_morales.setHorizontalHeaderLabels(["ID", "TAXI", "TIPO", "DETALLES", "FECHA", "PDF"])
        self.tabla_morales.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_morales.setColumnHidden(0, True) # Ocultar ID
        self.tabla_deudas.setColumnHidden(0, True)  # Ocultar ID

        # Obtenemos datos
        pendientes = self.db.obtener_incidencias_pendientes() 
        
        for p in pendientes:
            try: monto = float(p['monto'])
            except: monto = 0.0
            
            # Recuperamos datos clave para el PDF
            taxi = str(p['numero_economico'])
            tipo = p['tipo']
            desc = p['descripcion']
            oper = p['operador_id'] # NOMBRE DE LA OPERADORA
            fecha = str(p['fecha_registro'])

            # === BOTÓN PDF (Común para ambos) ===
            btn_pdf = QPushButton("📄 PDF")
            btn_pdf.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; border-radius: 4px;")
            # Usamos lambda para pasar TODOS los datos necesarios al generador
            btn_pdf.clicked.connect(lambda _, t=taxi, ti=tipo, d=desc, m=monto, o=oper, f=fecha: self.reimprimir_ticket(t, ti, d, m, o, f))

            # === TABLA 1: DINERO ($$$) ===
            if monto > 0:
                r = self.tabla_deudas.rowCount(); self.tabla_deudas.insertRow(r)
                self.tabla_deudas.setItem(r, 0, QTableWidgetItem(str(p['id'])))
                self.tabla_deudas.setItem(r, 1, QTableWidgetItem(taxi))
                self.tabla_deudas.setItem(r, 2, QTableWidgetItem(tipo))
                
                item_monto = QTableWidgetItem(f"${monto:,.2f}")
                item_monto.setForeground(QColor("#EF4444")) 
                self.tabla_deudas.setItem(r, 3, item_monto)
                
                self.tabla_deudas.setItem(r, 4, QTableWidgetItem(oper))
                
                btn_pagar = QPushButton("💵 COBRAR")
                btn_pagar.setStyleSheet("background-color: #10B981; color: white; font-weight: bold;")
                btn_pagar.clicked.connect(lambda _, x=p['id']: self.cobrar_deuda(x))
                self.tabla_deudas.setCellWidget(r, 5, btn_pagar)
                self.tabla_deudas.setCellWidget(r, 6, btn_pdf) # Botón PDF
            
            # === TABLA 2: DISCIPLINA ($0) ===
            else:
                r = self.tabla_morales.rowCount(); self.tabla_morales.insertRow(r)
                self.tabla_morales.setItem(r, 0, QTableWidgetItem(str(p['id'])))
                self.tabla_morales.setItem(r, 1, QTableWidgetItem(taxi))
                
                t_show = tipo
                if "Banderola" in tipo: t_show = "🚩 " + tipo
                elif "Ausencia" in tipo: t_show = "🚫 " + tipo
                self.tabla_morales.setItem(r, 2, QTableWidgetItem(t_show))
                
                self.tabla_morales.setItem(r, 3, QTableWidgetItem(desc))
                self.tabla_morales.setItem(r, 4, QTableWidgetItem(fecha[:16])) # Fecha Corta
                self.tabla_morales.setCellWidget(r, 5, btn_pdf) # Botón PDF
                

    def cobrar_deuda(self, id_incidencia):
        if QMessageBox.question(self, "Cobrar", "¿Confirmar que se recibió el pago?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.db.marcar_incidencia_pagada(id_incidencia)
            self.cargar_tabla_deudas()

    def reimprimir_ticket(self, taxi, tipo, desc, monto, oper, fecha_orig):
        # Generar nombre de archivo único
        nombre = f"Copia_Reporte_{taxi}_{datetime.now().strftime('%H%M%S')}.pdf"
        
        try:
            gen = GeneradorPDF(nombre)
            # Pasamos fecha_orig para que salga la fecha real del incidente
            gen.generar_ticket_incidencia(taxi, tipo, desc, monto, oper, fecha_personalizada=fecha_orig)
            
            QMessageBox.information(self, "PDF Generado", f"Se ha reimpreso el reporte de la unidad {taxi}.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo crear el PDF: {e}")

    
    def generar_pdf_incidencia(self, taxi, tipo, desc, monto, oper):
        # Aquí llamaríamos a la clase de reportes
        nombre = f"Reporte_{taxi}_{datetime.now().strftime('%H%M%S')}.pdf"
        try:
            gen = GeneradorPDF(nombre)
            gen.generar_ticket_incidencia(taxi, tipo, desc, monto, oper)
        except Exception as e:
            QMessageBox.warning(self, "PDF", f"No se pudo generar PDF: {e}")    



    # ---------------------------------------------------------
    # GESTIÓN BASES (Página 3 Admin)
    # ---------------------------------------------------------
    def construir_pagina_bases(self, parent):
        l = QHBoxLayout(parent)
        fi = QFrame(); fi.setFixedWidth(400)
        li = QVBoxLayout(fi)
        
        fa = QFrame(); fa.setStyleSheet("background-color: #1E293B; border-radius: 8px;")
        la = QVBoxLayout(fa)
        ha = QHBoxLayout()
        self.txt_nueva_base = QLineEdit(); self.txt_nueva_base.setPlaceholderText("Nombre Base")
        btn = QPushButton("➕ Agregar"); btn.setStyleSheet("background-color: #10B981; color: white; padding: 5px;")
        btn.clicked.connect(self.agregar_nueva_base)
        ha.addWidget(self.txt_nueva_base); ha.addWidget(btn)
        la.addWidget(QLabel("Nueva Base:")); la.addLayout(ha)
        
        self.tabla_bases = QTableWidget(); self.tabla_bases.setColumnCount(3)
        self.tabla_bases.setHorizontalHeaderLabels(["ID","NOMBRE","ACCION"])
        self.tabla_bases.setStyleSheet("QTableWidget { background-color: #1E293B; color: white; }")
        li.addWidget(fa); li.addWidget(self.tabla_bases)
        
        fd = QFrame(); fd.setStyleSheet("background-color: #0F172A; border-left: 2px solid #334155;")
        ld = QVBoxLayout(fd)
        h = QHBoxLayout()
        self.cmb_periodo_bases = QComboBox(); self.cmb_periodo_bases.addItems(["SIEMPRE","HOY","MES","AÑO"])
        self.cmb_periodo_bases.setStyleSheet("background-color: #1E293B; color: white;")
        self.cmb_periodo_bases.currentIndexChanged.connect(self.actualizar_grafico_bases)
        h.addWidget(QLabel("📈 BASES MÁS CONCURRIDAS")); h.addStretch(); h.addWidget(self.cmb_periodo_bases)
        
        self.grafico_bases = LienzoGrafico(fd)
        ld.addLayout(h); ld.addWidget(self.grafico_bases)
        
        l.addWidget(fi); l.addWidget(fd, 1)

    def cargar_tabla_bases(self):
        self.tabla_bases.setRowCount(0)
        for i, n in self.db.obtener_bases_fisicas():
            r = self.tabla_bases.rowCount(); self.tabla_bases.insertRow(r)
            self.tabla_bases.setItem(r,0,QTableWidgetItem(str(i)))
            self.tabla_bases.setItem(r,1,QTableWidgetItem(n))
            b = QPushButton("🗑️ Baja"); b.setStyleSheet("background-color: #EF4444; color: white;")
            b.clicked.connect(lambda _, x=i: self.baja_base(x))
            self.tabla_bases.setCellWidget(r,2,b)
        self.actualizar_grafico_bases()

    def actualizar_grafico_bases(self):
        p = self.cmb_periodo_bases.currentText()
        n, v = self.db.obtener_ranking_bases(p)
        self.grafico_bases.actualizar_grafico(n, v, "viajes")

    def agregar_nueva_base(self):
        n = self.txt_nueva_base.text().strip()
        if n and self.db.registrar_nueva_base(n):
            self.txt_nueva_base.clear(); self.cargar_tabla_bases(); self.generar_bases_fisicas(); self.cargar_datos_en_tablero()

    def baja_base(self, bid):
        if QMessageBox.question(self, "Baja", "¿Eliminar base?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self.db.eliminar_base_fisica(bid):
                self.cargar_tabla_bases(); self.generar_bases_fisicas(); self.cargar_datos_en_tablero()

    # ---------------------------------------------------------
    # REPORTES GLOBALES - ARREGLADO VISUALMENTE (Letra Grande)
    # ---------------------------------------------------------
    # --- REEMPLAZAR EN interfaz.py ---

    def construir_pagina_reportes_globales(self, parent):
        l = QVBoxLayout(parent); l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        f = QFrame(); f.setFixedSize(600, 550) 
        f.setStyleSheet("background-color: #1E293B; border-radius: 20px; border: 2px solid #334155;")
        fl = QVBoxLayout(f); fl.setSpacing(20); fl.setContentsMargins(40,40,40,40)
        
        lbl = QLabel("CENTRO DE REPORTES"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #FACC15; font-size: 28px; font-weight: bold; border: none;")
        
        # Filtros
        h = QHBoxLayout()
        self.date_global = QDateEdit(); self.date_global.setCalendarPopup(True); self.date_global.setDate(QDate.currentDate())
        self.date_global.setStyleSheet("background-color: #0F172A; color: white; padding: 12px; font-size: 16px;")
        
        self.cmb_periodo_global = QComboBox(); self.cmb_periodo_global.addItems(["DIA","MES","AÑO","SIEMPRE"])
        self.cmb_periodo_global.setStyleSheet("background-color: #0F172A; color: white; padding: 12px; font-size: 16px;")
        self.cmb_periodo_global.currentIndexChanged.connect(self.actualizar_formato_global)
        
        h.addWidget(self.date_global); h.addWidget(self.cmb_periodo_global)
        
        # --- BOTÓN 1: PÚBLICO ---
        btn_publico = QPushButton("📄 REPORTE PÚBLICO (Operativo)")
        btn_publico.setStyleSheet("background-color: #10B981; color: white; font-weight: bold; font-size: 16px; padding: 15px; border-radius: 10px;")
        btn_publico.clicked.connect(lambda: self.preparar_reporte("PUBLICO"))

        # --- BOTÓN 2: PRIVADO (Con candado) ---
        btn_admin = QPushButton("🔐 REPORTE ADMINISTRACIÓN (Completo)")
        btn_admin.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold; font-size: 16px; padding: 15px; border-radius: 10px;")
        btn_admin.clicked.connect(lambda: self.preparar_reporte("ADMIN"))
        
        fl.addWidget(lbl)
        fl.addLayout(h)
        fl.addSpacing(20)
        fl.addWidget(QLabel("Seleccione el tipo de informe:", styleSheet="color:#94A3B8; font-size:14px; border:none;"))
        fl.addWidget(btn_publico)
        fl.addWidget(btn_admin)
        fl.addStretch()
        
        l.addWidget(f); self.actualizar_formato_global()

    def preparar_reporte(self, tipo):
        periodo = self.cmb_periodo_global.currentText()
        qdate = self.date_global.date()
        fecha_str = qdate.toString("yyyy-MM-dd")
        
        # 1. SEGURIDAD PARA ADMIN
        password_pdf = None
        
        if tipo == "ADMIN":
            pwd, ok = QInputDialog.getText(self, "Seguridad", "🔒 Ingrese contraseña de ADMINISTRADOR:", QLineEdit.EchoMode.Password)
            if not ok or not pwd: return 
            
            # --- CAMBIO: VALIDACIÓN DE CONTRASEÑA REAL ---
            # Define aquí la contraseña única de administración
            CLAVE_MAESTRA = "ZORRO2026" # <--- ¡CAMBIA ESTO POR LA CONTRASEÑA QUE QUIERAS!
            
            if pwd != CLAVE_MAESTRA:
                # Si la contraseña no coincide, mostramos error y cancelamos todo
                QMessageBox.warning(self, "Acceso Denegado", "⛔ Contraseña incorrecta.\nNo tienes autorización para ver datos financieros.")
                return
            
            # Si llegó aquí, la contraseña es correcta.
            # Usamos esa misma clave para encriptar el PDF, así el archivo final 
            # tendrá la misma contraseña que acabas de escribir.
            password_pdf = pwd 

        # 2. OBTENER DATOS
        datos_gral = self.db.obtener_datos_reporte_global(periodo, fecha_str)
        datos_admin = None
        if tipo == "ADMIN":
            datos_admin = self.db.obtener_top_taxis_admin(periodo, fecha_str)

        # 3. GENERAR PDF
        nombre_pdf = f"Reporte_{tipo}_{periodo}_{datetime.now().strftime('%H%M')}.pdf"
        texto_fecha = fecha_str 

        try:
            gen = GeneradorPDF(nombre_pdf)
            # Pasamos la contraseña (que ya validamos que es la real)
            ruta = gen.generar_reporte_dual(tipo, periodo, texto_fecha, datos_gral, datos_admin, password_pdf)
            
            # Mensaje de éxito
            msg = f"Reporte generado exitosamente.\nUbicación: {ruta}"
            if password_pdf:
                msg += f"\n\n🔐 NOTA: El archivo está encriptado con la contraseña de administración."
            
            QMessageBox.information(self, "Éxito", msg)
            
            if ruta:
                os.startfile(ruta)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear el reporte: {e}")
    def actualizar_formato_global(self):
        p = self.cmb_periodo_global.currentText()
        self.date_global.setEnabled(p != "SIEMPRE")
        self.date_global.setDisplayFormat("dd/MM/yyyy" if p=="DIA" else "MM/yyyy" if p=="MES" else "yyyy" if p=="AÑO" else "---")

    def generar_pdf_corporativo(self):
        periodo = self.cmb_periodo_global.currentText()
        qdate = self.date_global.date()
        fecha_str = qdate.toString("yyyy-MM-dd")

        datos = self.db.obtener_datos_reporte_global(periodo, fecha_str)
        if not datos:
            QMessageBox.warning(self, "Sin Datos", "No hay información.")
            return

        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        dia, mes, anio = qdate.day(), meses[qdate.month()], qdate.year()
        
        texto_fecha = ""
        if periodo == "DIA": texto_fecha = f"{dia} de {mes} de {anio}"
        elif periodo == "MES": texto_fecha = f"{mes} {anio}"
        elif periodo == "AÑO": texto_fecha = f"Año {anio}"
        elif periodo == "SIEMPRE": texto_fecha = "HISTÓRICO GENERAL"
        else: texto_fecha = f"Ref: {fecha_str}"

        nombre_pdf = f"Reporte_Global_{periodo}.pdf"
        if periodo != "SIEMPRE": nombre_pdf = f"Reporte_Global_{periodo}_{fecha_str}.pdf"

        try:
            generador = GeneradorPDF(nombre_pdf)
            generador.generar_reporte_global(periodo, texto_fecha, datos)
        except Exception as e:
            QMessageBox.critical(self, "Error Fatal", f"No se pudo crear el PDF:\n{e}")

# 4. INICIALIZACIÓN BD Y MAIN
# ==========================================

def verificar_y_crear_db():
    nombre_db = "taxis.db"
    if os.path.exists(nombre_db):
        try: ctypes.windll.kernel32.SetFileAttributesW(nombre_db, 0x80) # Visible (0x80) para que la encuentres
        except: pass
        return True

    if QMessageBox.question(None, "BD No Encontrada", "¿Crear nueva base de datos?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
        return False

    try:
        conn = sqlite3.connect(nombre_db)
        c = conn.cursor()
        c.execute("PRAGMA foreign_keys = ON;")
        c.execute("CREATE TABLE IF NOT EXISTS cat_tipos_servicio (id INTEGER PRIMARY KEY AUTOINCREMENT, descripcion TEXT UNIQUE NOT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS cat_bases (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_base TEXT UNIQUE NOT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS taxis (id INTEGER PRIMARY KEY AUTOINCREMENT, numero_economico TEXT NOT NULL, estado_sistema TEXT DEFAULT 'ACTIVO', fecha_alta TEXT, fecha_baja TEXT, base_actual_id INTEGER DEFAULT 12, FOREIGN KEY(base_actual_id) REFERENCES cat_bases(id))")
        c.execute("CREATE TABLE IF NOT EXISTS viajes (id INTEGER PRIMARY KEY AUTOINCREMENT, taxi_id INTEGER NOT NULL, tipo_servicio_id INTEGER NOT NULL, base_salida_id INTEGER, destino TEXT, precio REAL DEFAULT 0.0, fecha_hora_inicio TEXT, fecha_hora_fin TEXT, FOREIGN KEY(taxi_id) REFERENCES taxis(id))")
        
        c.executemany("INSERT OR IGNORE INTO cat_tipos_servicio (id, descripcion) VALUES (?, ?)", [(1,'Viaje en base'),(2,'Telefono base'),(3,'Telefono unidad'),(4,'Viaje aereo')])
        c.executemany("INSERT OR IGNORE INTO cat_bases (id, nombre_base) VALUES (?, ?)", [(1,'Cessa'),(2,'Licuor'),(3,'Santiagito'),(4,'Aurrera'),(5,'Mercado'),(6,'Caros'),(7,'Survi'),(8,'Capulin'),(9,'Zocalo'),(10,'16 de septiembre'),(11,'Parada principal'),(12,'Fuera de Servicio'),(13,'En Viaje')])
        c.executemany("INSERT INTO taxis (numero_economico, estado_sistema, base_actual_id) VALUES (?, ?, ?)", [(str(n), 'ACTIVO', 12) for n in range(35, 101)])
        
        conn.commit(); conn.close()
        try: ctypes.windll.kernel32.SetFileAttributesW(nombre_db, 0x80)
        except: pass
        return True
    except Exception as e:
        QMessageBox.critical(None, "Error", f"No se pudo crear BD:\n{e}")
        return False

def realizar_respaldo_seguridad():
    """ Crea una copia de la base de datos en la carpeta /RESPALDOS al iniciar """
    if os.path.exists("taxis.db"):
        carpeta = "RESPALDOS_AUTO"
        if not os.path.exists(carpeta):
            os.makedirs(carpeta)
            # Ocultar carpeta en Windows para que no la borren por error
            try: ctypes.windll.kernel32.SetFileAttributesW(carpeta, 0x02) 
            except: pass

        # Nombre del archivo con fecha: taxis_backup_2026-01-25.db
        fecha = datetime.now().strftime("%Y-%m-%d")
        destino = os.path.join(carpeta, f"taxis_backup_{fecha}.db")
        
        # Solo copiamos si no existe ya el respaldo de hoy (para no alentar el inicio)
        if not os.path.exists(destino):
            try:
                import shutil
                shutil.copy2("taxis.db", destino)
                print(f"✅ Respaldo de seguridad creado: {destino}")
            except Exception as e:
                print(f"⚠️ No se pudo crear respaldo: {e}")



    

    
# ==========================================
# 4. INICIALIZACIÓN BD Y MAIN
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Anti-doble instancia (Esto está bien, déjalo)
    mem = QSharedMemory("SistemaTaxisZorro_Unique_Key_v1")
    if not mem.create(1):
        QMessageBox.warning(None, "Sistema", "El sistema ya se está ejecutando.")
        sys.exit(0)

    realizar_respaldo_seguridad()

    # 2. Splash Screen (Opcional, si tienes el logo se ve bonito)
    splash = None
    ruta_logo = ruta_recurso("LogoElZorropng.png")
    if os.path.exists(ruta_logo):
        p = QPixmap(ruta_logo).scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        splash = QSplashScreen(p); splash.show(); app.processEvents(); time.sleep(1.5)

    # 3. INICIO DE LA APP
    # Al crear VentanaPrincipal, ella llama al GestorBaseDatos.
    # El GestorBaseDatos detecta que no hay archivo y lo CREA AUTOMÁTICAMENTE.
    v = VentanaPrincipal()
    v.showMaximized()
    
    if splash: splash.finish(v)
    sys.exit(app.exec())