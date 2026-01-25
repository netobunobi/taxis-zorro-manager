from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import inch
from datetime import datetime
import os
import sys

def ruta_recurso(relativo):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relativo)

def obtener_ruta_segura(nombre_archivo):
    try:
        usuario = os.path.expanduser("~")
        ruta_base = os.path.join(usuario, "Documents") 
        carpeta_reportes = os.path.join(ruta_base, "Reportes Taxis El Zorro")
        if not os.path.exists(carpeta_reportes):
            os.makedirs(carpeta_reportes)
        return os.path.join(carpeta_reportes, nombre_archivo)
    except Exception:
        return os.path.abspath(nombre_archivo)

class GeneradorPDF:
    def __init__(self, nombre_archivo_simple):
        self.nombre_archivo = obtener_ruta_segura(nombre_archivo_simple)
        self.doc = SimpleDocTemplate(self.nombre_archivo, pagesize=letter, 
                                     topMargin=30, bottomMargin=30, 
                                     leftMargin=30, rightMargin=30)
        self.elementos = []
        self.estilos = getSampleStyleSheet()
        
        # Estilos personalizados
        self.estilo_titulo = ParagraphStyle(name="Titulo", parent=self.estilos['Heading1'], alignment=TA_CENTER, fontSize=24, textColor=colors.HexColor("#0F172A"), spaceAfter=20)
        self.estilo_sub = ParagraphStyle(name="Subtitulo", parent=self.estilos['Heading2'], alignment=TA_LEFT, fontSize=14, textColor=colors.HexColor("#64748B"), spaceAfter=10)
        self.estilo_normal = ParagraphStyle(name="NormalC", parent=self.estilos['Normal'], alignment=TA_CENTER, fontSize=10)
        self.estilo_empresa = ParagraphStyle('Empresa', parent=self.estilos['Heading1'], fontSize=16, textColor=colors.HexColor("#1E293B"), alignment=TA_LEFT)
        self.estilo_programa = ParagraphStyle('Programa', parent=self.estilos['Normal'], fontSize=9, textColor=colors.HexColor("#64748B"), alignment=TA_LEFT)
        self.estilo_periodo = ParagraphStyle('PeriodoRep', parent=self.estilos['Normal'], fontSize=11, alignment=TA_CENTER, textColor=colors.HexColor("#475569"))
        self.estilo_fecha_gen = ParagraphStyle('FechaGen', parent=self.estilos['Normal'], fontSize=9, alignment=TA_RIGHT, textColor=colors.HexColor("#94A3B8"))

    def _finalizar_reporte(self):
        try:
            self.doc.build(self.elementos)
            # Abrir archivo automáticamente en Windows
            if os.name == 'nt':
                os.startfile(self.nombre_archivo)
        except Exception as e:
            print(f"Error al generar PDF: {e}")

    def _agregar_encabezado(self, titulo_reporte, subtitulo):
        logo = []
        nombre_logo = ruta_recurso("LogoElZorropng.png") 
        if os.path.exists(nombre_logo):
            # LOGO MEJORADO: Más alto y conservando proporción
            img = Image(nombre_logo, width=1.4*inch, height=1.4*inch)
            img.hAlign = 'RIGHT'
            img.preserveAspectRatio = True # ¡Esto evita que se vea aplastado!
            logo = img
        
        t_head = Table([[[Paragraph("<b>TAXIS EL ZORRO</b>", self.estilo_empresa), 
                          Paragraph("Sistema de Gestión", self.estilo_programa)], logo]], 
                        colWidths=[400, 150])
        t_head.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        self.elementos.append(t_head)
        self.elementos.append(Table([[""]], colWidths=[550], style=[('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#FACC15"))])) 
        self.elementos.append(Spacer(1, 10)) 

        # Títulos
        self.elementos.append(Paragraph(titulo_reporte, self.estilo_titulo))
        self.elementos.append(Paragraph(subtitulo, self.estilo_periodo))
        
        # Fecha de generación
        fecha_gen = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.elementos.append(Paragraph(f"Reporte generado el: {fecha_gen}", self.estilo_fecha_gen))
        self.elementos.append(Spacer(1, 20))

    def generar_reporte_global(self, periodo, texto_fecha, datos):
        self._agregar_encabezado(f"REPORTE OPERATIVO - {periodo}", texto_fecha)
        # (Lógica placeholder para el futuro reporte global)
        self._finalizar_reporte()

    def generar_reporte_unidad(self, numero, texto_fecha, stats, lista_viajes):
        self._agregar_encabezado(f"REPORTE DE UNIDAD - TAXI {numero}", texto_fecha)
        
        # 1. TABLA RESUMEN
        ganancia = stats.get('ganancia', 0.0) 
        viajes = stats.get('viajes', 0)
        horas = stats.get('horas', 0.0)
        
        d_res = [["INGRESOS", "VIAJES", "HORAS TRABAJADAS"],
                 [f"${ganancia:,.2f}", str(viajes), f"{horas:,.1f} h"]]
        
        t_res = Table(d_res, colWidths=[2.5*inch, 2*inch, 2.5*inch])
        t_res.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('FONTSIZE', (0,1), (-1,1), 14), # Datos más grandes
        ]))
        self.elementos.append(t_res)
        self.elementos.append(Spacer(1, 20))
        
        # 2. TABLA DE DETALLES
        enc = ["FECHA", "HORA", "ORIGEN / BASE", "DESTINO", "COSTO"]
        dat = [enc]
        
        for v in lista_viajes:
            # === CORRECCIÓN DEL ERROR ===
            # Usamos v['fecha'] que es como viene de la nueva DB
            fh = str(v['fecha']).split(" ") 
            f_sola = fh[0]
            h_sola = fh[1][:5] if len(fh)>1 else ""
            
            dat.append([
                f_sola, 
                h_sola, 
                v.get('origen','---'), 
                Paragraph(str(v.get('destino','---')), self.estilo_normal), 
                f"${v['precio']:,.2f}"
            ])
        
        # Ajustamos anchos para que quepa bien
        t_det = Table(dat, colWidths=[0.9*inch, 0.7*inch, 1.8*inch, 2.6*inch, 1*inch])
        t_det.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#475569")), 
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (-1,0), (-1,-1), 'RIGHT'), # Costo a la derecha
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F1F5F9")])
        ]))
        
        self.elementos.append(t_det)
        self._finalizar_reporte()