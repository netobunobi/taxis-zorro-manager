from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import inch
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
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
        self.estilo_titulo = ParagraphStyle(name="Titulo", parent=self.estilos['Heading1'], alignment=TA_CENTER, fontSize=20, textColor=colors.HexColor("#0F172A"), spaceAfter=15)
        self.estilo_sub = ParagraphStyle(name="Subtitulo", parent=self.estilos['Heading2'], alignment=TA_LEFT, fontSize=12, textColor=colors.HexColor("#64748B"), spaceAfter=5)
        self.estilo_normal = ParagraphStyle(name="NormalC", parent=self.estilos['Normal'], alignment=TA_CENTER, fontSize=10)
        self.estilo_empresa = ParagraphStyle('Empresa', parent=self.estilos['Heading1'], fontSize=16, textColor=colors.HexColor("#1E293B"), alignment=TA_LEFT)
        self.estilo_programa = ParagraphStyle('Programa', parent=self.estilos['Normal'], fontSize=8, textColor=colors.HexColor("#64748B"), alignment=TA_LEFT)
        self.estilo_periodo = ParagraphStyle('PeriodoRep', parent=self.estilos['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.HexColor("#475569"))
        self.estilo_fecha_gen = ParagraphStyle('FechaGen', parent=self.estilos['Normal'], fontSize=8, alignment=TA_RIGHT, textColor=colors.HexColor("#94A3B8"))

    def _finalizar_reporte(self):
        try:
            self.doc.build(self.elementos)
        except Exception as e:
            print(f"Error al generar PDF: {e}")

    def _agregar_encabezado(self, titulo_reporte, subtitulo):
        logo = []
        nombre_logo = ruta_recurso("LogoElZorropng.png") 
        if os.path.exists(nombre_logo):
            img = Image(nombre_logo, width=1.2*inch, height=1.2*inch)
            img.hAlign = 'RIGHT'
            img.preserveAspectRatio = True 
            logo = img
        
        t_head = Table([[[Paragraph("<b>TAXIS EL ZORRO</b>", self.estilo_empresa), 
                          Paragraph("Sistema de Gestión", self.estilo_programa)], logo]], 
                        colWidths=[400, 150])
        t_head.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        self.elementos.append(t_head)
        self.elementos.append(Table([[""]], colWidths=[550], style=[('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#FACC15"))])) 
        self.elementos.append(Spacer(1, 10)) 

        self.elementos.append(Paragraph(titulo_reporte, self.estilo_titulo))
        self.elementos.append(Paragraph(subtitulo, self.estilo_periodo))
        
        fecha_gen = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.elementos.append(Paragraph(f"Reporte generado el: {fecha_gen}", self.estilo_fecha_gen))
        self.elementos.append(Spacer(1, 15))

    def generar_reporte_dual(self, tipo_reporte, periodo, fecha_texto, datos_generales, datos_admin=None, password=None):
        if password and tipo_reporte == "ADMIN":
            self.doc.encrypt = StandardEncryption(password, canPrint=1, canCopy=0, canModify=0)

        titulo = "INFORME OPERATIVO" if tipo_reporte == "PUBLICO" else "REPORTE GERENCIAL Y FINANCIERO"
        self._agregar_encabezado(titulo, f"Periodo: {periodo} | {fecha_texto}")

        # --- EXTRACCIÓN DE DATOS ---
        totales = datos_generales['totales']
        servicios = datos_generales['servicios'] 
        incidencias = datos_generales['incidencias']

        # ==========================================================
        # 1. TABLA DE MÉTRICAS OPERATIVAS (LO QUE PEDISTE CONSERVAR)
        # ==========================================================
        self.elementos.append(Paragraph("RESUMEN DE OPERACIONES", self.estilo_sub))
        
        d_ops = [
            ["INDICADOR", "CANTIDAD"],
            ["Total de Viajes Realizados", str(totales['viajes'])],
            ["Servicios de Base (Sitio)", str(servicios.get(1,0))],
            ["Servicios por Teléfono", str(servicios.get(2,0) + servicios.get(3,0))],
            ["Servicios Aéreos / Calle", str(servicios.get(4,0))],
            ["TOTAL INCIDENCIAS REGISTRADAS", str(incidencias['total_count'])]
        ]
        
        t_ops = Table(d_ops, colWidths=[4*inch, 2*inch])
        t_ops.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            # Fila de incidencias en amarillo suave
            ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#FFF7ED")),
            ('FONTNAME', (0,5), (-1,5), 'Helvetica-Bold'),
        ]))
        t_ops.hAlign = 'CENTER'
        self.elementos.append(t_ops)
        self.elementos.append(Spacer(1, 15))

        # ==========================================================
        # 2. DESGLOSE DE INCIDENCIAS (SI HAY)
        # ==========================================================
        if incidencias['total_count'] > 0:
            self.elementos.append(Paragraph("DETALLE DE DISCIPLINA", self.estilo_sub))
            head_inc = ["TIPO", "CANTIDAD"]
            if tipo_reporte == "ADMIN": head_inc.append("MULTAS ($)")
            
            d_inc = [head_inc]
            for tipo, cant, lana in incidencias['desglose']:
                row = [tipo, str(cant)]
                if tipo_reporte == "ADMIN": row.append(f"${lana:,.2f}")
                d_inc.append(row)
            
            anchos = [4*inch, 2*inch] if tipo_reporte == "PUBLICO" else [3*inch, 1.5*inch, 1.5*inch]
            t_inc = Table(d_inc, colWidths=anchos)
            t_inc.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#64748B")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            t_inc.hAlign = 'CENTER'
            self.elementos.append(t_inc)
            self.elementos.append(Spacer(1, 20))


        # ==========================================================
        # 3. SECCIÓN ADMINISTRATIVA (SOLO ADMIN)
        # ==========================================================
        if tipo_reporte == "ADMIN" and datos_admin:
            self.elementos.append(Paragraph("ANÁLISIS DE RENDIMIENTO", self.estilo_titulo))
            self.elementos.append(Spacer(1, 5))

            # --- A. GRÁFICA DE PASTEL (Si hay datos) ---
            # Solo se dibuja si hay viajes registrados
            raw_graf = datos_admin['grafica_servicios']
            if raw_graf:
                self.elementos.append(Paragraph("Distribución de Servicios:", self.estilo_sub))
                data_pie = []
                labels_pie = []
                for desc, cant in raw_graf:
                    data_pie.append(cant)
                    labels_pie.append(f"{desc} ({cant})")
                
                d = Drawing(400, 150) # Altura reducida
                pc = Pie()
                pc.x = 125
                pc.y = 10
                pc.width = 130 # Más grande
                pc.height = 130
                pc.data = data_pie
                pc.labels = labels_pie
                pc.sideLabels = 1
                pc.slices.strokeWidth = 0.5
                colores = [colors.HexColor("#00D1FF"), colors.HexColor("#10B981"), colors.HexColor("#FACC15"), colors.HexColor("#F87171")]
                for i in range(len(data_pie)):
                    pc.slices[i].fillColor = colores[i % len(colores)]
                d.add(pc)
                self.elementos.append(d)
                self.elementos.append(Spacer(1, 15))
            else:
                self.elementos.append(Paragraph("(Gráfica no disponible: Sin viajes registrados)", self.estilo_programa))
                self.elementos.append(Spacer(1, 15))


            # --- B. TABLAS DE MEJORES CHOFERES ---
            
            # Función interna para dibujar tablas sin emojis
            def crear_tabla_top(titulo, lista_datos, es_por_horas=False):
                self.elementos.append(Paragraph(titulo, self.estilo_sub))
                head = ["POS", "UNIDAD", "HORAS" if es_por_horas else "VIAJES", "DINERO", "REPORTES"]
                data = [head]
                
                for i, x in enumerate(lista_datos):
                    val_principal = f"{x['horas']:.1f} h" if es_por_horas else str(x['viajes'])
                    data.append([
                        f"#{i+1}",
                        f"Taxi {x['numero']}",
                        val_principal,
                        f"${x['dinero']:,.2f}",
                        str(x['reportes'])
                    ])
                
                if len(data) == 1: # Si no hay datos
                    data.append(["-", "-", "-", "-", "-"])

                t = Table(data, colWidths=[0.7*inch, 1.2*inch, 1.2*inch, 1.5*inch, 1*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('FONTNAME', (4,1), (-1,-1), 'Helvetica-Bold'), # Columna Reportes negrita
                ]))
                
                # Pintar de ROJO si hay reportes > 0 (Empezamos desde fila 1)
                for row_idx, row_data in enumerate(lista_datos):
                    if row_data['reportes'] > 0:
                        t.setStyle(TableStyle([
                            ('TEXTCOLOR', (4, row_idx+1), (4, row_idx+1), colors.red),
                            ('BACKGROUND', (4, row_idx+1), (4, row_idx+1), colors.HexColor("#FEE2E2"))
                        ]))
                
                t.hAlign = 'CENTER'
                self.elementos.append(t)
                self.elementos.append(Spacer(1, 15))

            # Tabla 1: Top Viajes (Quitamos emojis para evitar cuadraditos)
            crear_tabla_top(">> MAYOR PRODUCTIVIDAD (Por Viajes)", datos_admin['top_viajes'], es_por_horas=False)
            
            # Tabla 2: Top Horas
            crear_tabla_top(">> MAYOR DEDICACION (Por Horas)", datos_admin['top_horas'], es_por_horas=True)

            # --- C. CAJA DE DINERO FINAL (Letra Ajustada) ---
            self.elementos.append(Spacer(1, 10))
            ganancia_total = datos_admin['total_empresa']
            
            d_money = [["INGRESOS TOTALES (VIAJES)"], [f"${ganancia_total:,.2f}"]]
            t_money = Table(d_money, colWidths=[4*inch])
            t_money.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#10B981")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                
                # --- AQUÍ ESTÁ EL AJUSTE DE TAMAÑO ---
                ('FONTSIZE', (0,1), (-1,1), 18), # Bajamos de 24 a 18 para que quepa bien
                ('TOPPADDING', (0,1), (-1,1), 10),
                ('BOTTOMPADDING', (0,1), (-1,1), 10),
            ]))
            t_money.hAlign = 'CENTER'
            self.elementos.append(t_money)

            self.elementos.append(Spacer(1, 20))
            self.elementos.append(Paragraph("Documento Confidencial - Uso exclusivo Administración", self.estilo_programa))

        else:
            self.elementos.append(Spacer(1, 40))
            self.elementos.append(Paragraph("*** FIN DEL REPORTE PÚBLICO ***", self.estilo_periodo))

        self._finalizar_reporte()
        return self.nombre_archivo

    # (MANTENEMOS TUS OTRAS FUNCIONES IGUALES)
    def generar_reporte_unidad(self, numero, texto_fecha, stats, lista_viajes):
        self._agregar_encabezado(f"REPORTE DE UNIDAD - TAXI {numero}", texto_fecha)
        ganancia = stats.get('ganancia', 0.0) 
        viajes = stats.get('viajes', 0)
        horas = stats.get('horas', 0.0)
        d_res = [["INGRESOS", "VIAJES", "HORAS TRABAJADAS"], [f"${ganancia:,.2f}", str(viajes), f"{horas:,.1f} h"]]
        t_res = Table(d_res, colWidths=[2.5*inch, 2*inch, 2.5*inch])
        t_res.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 10),
            ('FONTSIZE', (0,1), (-1,1), 14), 
        ]))
        self.elementos.append(t_res)
        self.elementos.append(Spacer(1, 20))
        enc = ["FECHA", "HORA", "ORIGEN / BASE", "DESTINO", "COSTO"]
        dat = [enc]
        for v in lista_viajes:
            fh = str(v['fecha']).split(" ") 
            f_sola = fh[0]; h_sola = fh[1][:5] if len(fh)>1 else ""
            dat.append([f_sola, h_sola, v.get('origen','---'), Paragraph(str(v.get('destino','---')), self.estilo_normal), f"${v['precio']:,.2f}"])
        t_det = Table(dat, colWidths=[0.9*inch, 0.7*inch, 1.8*inch, 2.6*inch, 1*inch])
        t_det.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#475569")), 
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (-1,0), (-1,-1), 'RIGHT'), 
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F1F5F9")])
        ]))
        self.elementos.append(t_det)
        self._finalizar_reporte()

    def generar_ticket_incidencia(self, taxi, tipo, descripcion, monto, operadora):
        fecha_gen = datetime.now().strftime('%d/%m/%Y %H:%M')
        self._agregar_encabezado(f"REPORTE DE INCIDENCIA - TAXI {taxi}", fecha_gen)
        color_fondo = colors.HexColor("#FEE2E2") 
        if monto == 0: color_fondo = colors.HexColor("#FEF3C7") 
        datos = [["TIPO DE REPORTE:", tipo], ["DESCRIPCIÓN:", Paragraph(descripcion, self.estilo_normal)], ["REPORTADO POR:", operadora.upper()], ["MONTO A PAGAR:", f"${monto:,.2f}"]]
        t = Table(datos, colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), color_fondo),
            ('GRID', (0,0), (-1,-1), 1, colors.white),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), 
            ('PADDING', (0,0), (-1,-1), 12),
            ('TEXTCOLOR', (1,3), (1,3), colors.red if monto > 0 else colors.black), 
            ('FONTSIZE', (1,3), (1,3), 14), 
        ]))
        self.elementos.append(t)
        self.elementos.append(Spacer(1, 40))
        self.elementos.append(Paragraph("*** FIN DEL REPORTE ***", self.estilo_programa))
        self._finalizar_reporte()