from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.units import inch
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
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
        
        # Estilos personalizados (Diseño Profesional)
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
            return self.nombre_archivo
        except Exception as e:
            print(f"Error al generar PDF: {e}")
            return None

    def _agregar_encabezado(self, titulo_reporte, subtitulo):
        logo = []
        # BÚSQUEDA ROBUSTA DEL LOGO (PNG o JPG)
        nombre_logo = ruta_recurso("LogoElZorropng.png")
        if not os.path.exists(nombre_logo):
            nombre_logo = ruta_recurso("LogoElZorropng.jpg")

        if os.path.exists(nombre_logo):
            img = Image(nombre_logo, width=1.3*inch, height=1.3*inch)
            img.hAlign = 'RIGHT'
            img.preserveAspectRatio = True 
            logo = img
        else:
            # Si no hay logo, poner un espacio vacío para que no falle
            logo = Paragraph("", self.estilo_normal)
        
        # Tabla encabezado: Texto Izquierda | Logo Derecha
        t_head = Table([[[Paragraph("<b>TAXIS EL ZORRO</b>", self.estilo_empresa), 
                          Paragraph("Sistema Integral de Gestión", self.estilo_programa)], logo]], 
                        colWidths=[400, 150])
        t_head.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'), 
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,0), 'RIGHT') # Logo a la derecha
        ]))
        self.elementos.append(t_head)
        
        # Línea Dorada
        self.elementos.append(Table([[""]], colWidths=[550], style=[('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#FACC15"))])) 
        self.elementos.append(Spacer(1, 10)) 

        self.elementos.append(Paragraph(titulo_reporte, self.estilo_titulo))
        self.elementos.append(Paragraph(subtitulo, self.estilo_periodo))
        
        fecha_gen = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.elementos.append(Paragraph(f"Generado el: {fecha_gen}", self.estilo_fecha_gen))
        self.elementos.append(Spacer(1, 15))

    def generar_reporte_dual(self, tipo_reporte, periodo, fecha_texto, datos_generales, datos_admin=None, password=None):
        if password and tipo_reporte == "ADMIN":
            self.doc.encrypt = StandardEncryption(password, canPrint=1, canCopy=0, canModify=0)

        titulo = "REPORTE OPERATIVO DIARIO" if tipo_reporte == "PUBLICO" else "REPORTE GERENCIAL COMPLETO"
        self._agregar_encabezado(titulo, f"Periodo: {periodo} | {fecha_texto}")

        # --- EXTRACCIÓN DE DATOS ---
        totales = datos_generales['totales']
        servicios = datos_generales['servicios'] 
        incidencias = datos_generales['incidencias']
        lista_flota = datos_generales.get('detalle_flota', [])

        # CALCULAR AUSENCIAS ESPECÍFICAS
        # Buscamos en el desglose cuántas incidencias contienen la palabra "Ausencia" o "Falta"
        total_ausencias = 0
        for tipo, cant, _ in incidencias.get('desglose', []):
            if "Ausencia" in tipo or "Falta" in tipo or "Ausentismo" in tipo:
                total_ausencias += cant

        # ==========================================================
        # 1. TABLA RESUMEN GENERAL (INCLUYE AUSENCIAS AHORA)
        # ==========================================================
        d_ops = [
            ["METRICAS GLOBALES", "CANTIDAD"],
            ["Viajes Totales Realizados", str(totales['viajes'])],
            ["Servicios de Base", str(servicios.get(1,0))],
            ["Servicios Teléfono", str(servicios.get(2,0) + servicios.get(3,0))],
            ["Total Incidencias", str(incidencias['total_count'])],
            # --- NUEVA FILA SOLICITADA ---
            ["AUSENCIAS / FALTAS", str(total_ausencias)] 
        ]
        
        t_ops = Table(d_ops, colWidths=[4*inch, 2*inch])
        t_ops.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            # Resaltar la fila de Ausencias en Rojo suave si hay faltas
            ('BACKGROUND', (0,5), (-1,5), colors.HexColor("#FECACA") if total_ausencias > 0 else colors.white),
            ('TEXTCOLOR', (0,5), (-1,5), colors.red if total_ausencias > 0 else colors.black),
            ('FONTNAME', (0,5), (-1,5), 'Helvetica-Bold'),
        ]))
        self.elementos.append(t_ops)
        self.elementos.append(Spacer(1, 15))

        # ==========================================================
        # 2. SÁBANA DE LA FLOTA (AHORA EN PUBLICO Y ADMIN)
        # ==========================================================
        if lista_flota:
            self.elementos.append(Paragraph("RESUMEN DE ACTIVIDAD POR UNIDAD", self.estilo_sub))
            
            # Encabezados
            head_flota = ["TAXI", "VIAJES", "HORAS", "INGRESOS"]
            data_flota = [head_flota]
            
            # Ordenamos por número de taxi
            lista_flota.sort(key=lambda x: int(x['numero']))

            for taxi in lista_flota:
                data_flota.append([
                    f"Unidad {taxi['numero']}",
                    str(taxi['viajes']),
                    f"{taxi['horas']:.1f} h",
                    f"${taxi['dinero']:,.2f}"
                ])

            t_flota = Table(data_flota, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1.5*inch])
            
            estilo_flota = [
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")])
            ]

            # ALERTAS VISUALES (Rojo si trabajó menos de 8 horas)
            for i, taxi in enumerate(lista_flota):
                fila_idx = i + 1 
                if taxi['horas'] < 8.0:
                    estilo_flota.append(('BACKGROUND', (2, fila_idx), (2, fila_idx), colors.HexColor("#FECACA")))
                    estilo_flota.append(('TEXTCOLOR', (2, fila_idx), (2, fila_idx), colors.red))
                if taxi['viajes'] == 0:
                     estilo_flota.append(('TEXTCOLOR', (1, fila_idx), (1, fila_idx), colors.grey))

            t_flota.setStyle(TableStyle(estilo_flota))
            self.elementos.append(t_flota)
            self.elementos.append(Paragraph("* Celdas rojas indican jornada incompleta (< 8h).", self.estilo_programa))
            self.elementos.append(Spacer(1, 20))


        # ==========================================================
        # 3. INCIDENCIAS DETALLADAS
        # ==========================================================
        if incidencias['total_count'] > 0:
            self.elementos.append(Paragraph("DETALLE DE INCIDENCIAS / DISCIPLINA", self.estilo_sub))
            head_inc = ["TIPO", "CANTIDAD"]
            if tipo_reporte == "ADMIN": head_inc.append("MONTO ($)")
            
            d_inc = [head_inc]
            for tipo, cant, lana in incidencias['desglose']:
                row = [tipo, str(cant)]
                if tipo_reporte == "ADMIN": row.append(f"${lana:,.2f}")
                d_inc.append(row)
            
            anchos = [3*inch, 1.5*inch]
            if tipo_reporte == "ADMIN": anchos.append(1.5*inch)

            t_inc = Table(d_inc, colWidths=anchos)
            t_inc.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EF4444")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            self.elementos.append(t_inc)
            self.elementos.append(Spacer(1, 20))

        # ==========================================================
        # 4. EXCLUSIVO ADMIN (GRÁFICAS Y TOPs)
        # ==========================================================
        if tipo_reporte == "ADMIN" and datos_admin:
            self.elementos.append(Paragraph("ANÁLISIS ESTADÍSTICO (Privado)", self.estilo_titulo))
            self.elementos.append(Spacer(1, 10))

            # Gráfica Pastel
            raw_graf = datos_admin.get('grafica_servicios', [])
            if raw_graf:
                self.elementos.append(Paragraph("Distribución de Servicios:", self.estilo_sub))
                data_pie, labels_pie = [], []
                for desc, cant in raw_graf:
                    data_pie.append(cant)
                    labels_pie.append(f"{desc}")
                
                d = Drawing(400, 150)
                pc = Pie(); pc.x = 100; pc.y = 10; pc.width = 130; pc.height = 130
                pc.data = data_pie; pc.labels = labels_pie; pc.sideLabels = 1
                colores = [colors.HexColor("#00D1FF"), colors.HexColor("#10B981"), colors.HexColor("#FACC15"), colors.HexColor("#F87171")]
                for i in range(len(data_pie)): pc.slices[i].fillColor = colores[i % len(colores)]
                d.add(pc)
                self.elementos.append(d)
                self.elementos.append(Spacer(1, 15))

            # Tablas TOP
            def crear_tabla_top(titulo, lista_datos, es_por_horas=False):
                self.elementos.append(Paragraph(titulo, self.estilo_sub))
                head = ["POS", "UNIDAD", "HORAS" if es_por_horas else "VIAJES", "DINERO"]
                data = [head]
                for i, x in enumerate(lista_datos):
                    val = f"{x['horas']:.1f} h" if es_por_horas else str(x['viajes'])
                    data.append([f"#{i+1}", f"Taxi {x['numero']}", val, f"${x['dinero']:,.2f}"])
                
                if len(data) == 1: data.append(["-", "-", "-", "-"])
                t = Table(data, colWidths=[0.7*inch, 1.2*inch, 1.2*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER')
                ]))
                self.elementos.append(t)
                self.elementos.append(Spacer(1, 10))

            if 'top_viajes' in datos_admin:
                crear_tabla_top(">> TOP 5: MAYOR PRODUCTIVIDAD", datos_admin['top_viajes'][:5], False)
            if 'top_horas' in datos_admin:
                crear_tabla_top(">> TOP 5: MAYOR DEDICACIÓN", datos_admin['top_horas'][:5], True)

            # Dinero Total Grande
            ganancia_total = datos_admin.get('total_empresa', 0)
            t_money = Table([["INGRESOS TOTALES DEL PERIODO"], [f"${ganancia_total:,.2f}"]], colWidths=[4*inch])
            t_money.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#10B981")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTSIZE', (0,1), (-1,1), 18)
            ]))
            self.elementos.append(Spacer(1, 15)); self.elementos.append(t_money)

        # Pie de página final
        self.elementos.append(Spacer(1, 20))
        txt_fin = "*** FIN DEL REPORTE ***" if tipo_reporte == "PUBLICO" else "DOCUMENTO CONFIDENCIAL - ADMINISTRACIÓN"
        self.elementos.append(Paragraph(txt_fin, self.estilo_periodo))
        
        return self._finalizar_reporte()

    # --- REPORTE INDIVIDUAL (ESTILOS ARREGLADOS) ---
    # Nota: Agregamos el nuevo parámetro 'lista_incidencias=None' al final
    def generar_reporte_unidad(self, numero, texto_fecha, stats, lista_viajes, lista_incidencias=None):
        # 1. LOGO
        nombre_logo = ruta_recurso("LogoElZorropng.png")
        if not os.path.exists(nombre_logo): nombre_logo = ruta_recurso("LogoElZorropng.jpg")
        
        logo_img = []
        if os.path.exists(nombre_logo):
            img = Image(nombre_logo, width=1.3*inch, height=1.3*inch); img.hAlign = 'RIGHT'; logo_img = img
        else:
            logo_img = Paragraph("", self.estilo_normal)

        # 2. ENCABEZADO
        ahora = datetime.now()
        
        # Estilos alineados a la IZQUIERDA
        estilo_titulo_taxi = ParagraphStyle('TaxiTit', parent=self.estilos['Heading1'], fontSize=22, textColor=colors.HexColor("#0F172A"), spaceAfter=2, alignment=TA_LEFT)
        estilo_datos_head = ParagraphStyle('HeadDat', parent=self.estilos['Normal'], fontSize=11, textColor=colors.HexColor("#334155"), leading=14, alignment=TA_LEFT)

        datos_izq = [
            [Paragraph(f"REPORTE: TAXI {numero}", estilo_titulo_taxi)],
            [Paragraph(f"<b>Reporte del día:</b> {texto_fecha}", estilo_datos_head)],
            [Paragraph(f"<b>Corte:</b> {ahora.strftime('%H:%M')} hrs", estilo_datos_head)],
        ]
        
        t_head = Table([[Table(datos_izq, colWidths=[4.5*inch]), logo_img]], colWidths=[5*inch, 2*inch])
        t_head.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'), 
            ('LEFTPADDING', (0,0), (-1,-1), 0), 
            ('ALIGN', (0,0), (0,0), 'LEFT'),
        ]))
        
        self.elementos.append(t_head)
        self.elementos.append(Table([[""]], colWidths=[7*inch], style=[('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#FACC15"))]))
        self.elementos.append(Spacer(1, 20))

        # 3. RESUMEN
        d_res = [["INGRESOS", "VIAJES", "HORAS"], [f"${stats.get('ganancia',0):,.2f}", str(stats.get('viajes',0)), f"{stats.get('horas',0):.1f} h"]]
        t_res = Table(d_res, colWidths=[2.3*inch]*3)
        t_res.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")), ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#94A3B8")),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor("#F1F5F9")), ('TEXTCOLOR', (0,1), (-1,1), colors.HexColor("#0F172A")),
            ('FONTSIZE', (0,1), (-1,1), 16), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('PADDING', (0,0), (-1,-1), 10)
        ]))
        self.elementos.append(t_res)
        self.elementos.append(Spacer(1, 25))

        # 4. LISTA VIAJES
        estilo_celda_izq = ParagraphStyle('CeldaIzq', parent=self.estilos['Normal'], fontSize=10, alignment=TA_LEFT)

        dat = [["HORA", "ORIGEN", "DESTINO", "COSTO"]]
        for v in lista_viajes:
            hora = str(v['fecha']).split(" ")[1][:5] if " " in str(v['fecha']) else str(v['fecha'])
            dat.append([
                hora, 
                str(v.get('origen',''))[:20], 
                Paragraph(str(v.get('destino','')), estilo_celda_izq),
                f"${v['precio']:,.2f}"
            ])
        
        t_det = Table(dat, colWidths=[1*inch, 1.8*inch, 3*inch, 1.2*inch])
        t_det.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
            ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#CBD5E1")),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),  
            ('ALIGN', (0,0), (0,-1), 'CENTER'), 
            ('ALIGN', (-1,0), (-1,-1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")])
        ]))
        self.elementos.append(t_det)

        # ==========================================================
        # 5. SECCIÓN: HISTORIAL DE ADEUDOS Y REPORTES ACTIVOS
        # ==========================================================
        if lista_incidencias and len(lista_incidencias) > 0:
            self.elementos.append(Spacer(1, 30))
            
            estilo_sub_rojo = ParagraphStyle('SubRojo', parent=self.estilos['Heading2'], fontSize=12, textColor=colors.HexColor("#EF4444"), spaceAfter=5)
            self.elementos.append(Paragraph("ADEUDOS Y REPORTES PENDIENTES", estilo_sub_rojo))
            
            # Encabezados con columnas separadas
            head_inc = ["FECHA", "CONCEPTO", "DESCRIPCION", "MONTO"]
            data_inc = [head_inc]
            
            total_deuda_periodo = 0.0
            
            for inc in lista_incidencias:
                try:
                    # Limpieza de texto para evitar errores de PDF (eliminando emojis manuales)
                    tipo = str(inc['tipo']).replace("⚠️ ", "").replace("🛑 ", "").replace("🚩 ", "").replace("🚫 ", "").replace("💸 ", "").replace("💰 ", "")
                    desc = str(inc['descripcion'])
                    monto = inc['monto']
                    fecha = str(inc['fecha_registro'])[:10]
                    estado = inc['resuelto']
                except:
                    tipo = str(inc[0]); desc = str(inc[1]); monto = inc[2]; fecha = str(inc[3])[:10]; estado = inc[4]
                
                if estado in ['PENDIENTE', 'INFORMATIVO']:
                    total_deuda_periodo += monto
                    data_inc.append([
                        fecha,
                        tipo.upper(),
                        Paragraph(desc, self.estilos['Normal']),
                        f"${monto:,.2f}"
                    ])

            # Tabla con anchos ajustados para la descripción
            t_inc = Table(data_inc, colWidths=[1.0*inch, 1.5*inch, 3.5*inch, 1.0*inch])
            
            t_inc.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EF4444")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (1,-1), 'LEFT'),
                ('ALIGN', (-1,0), (-1,-1), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,1), (-1,-1), 9),
            ]))

            self.elementos.append(t_inc)
            # ... resto del pie de página ...
            
            # Total Deuda
            if total_deuda_periodo > 0:
                self.elementos.append(Spacer(1, 10))
                p_deuda = Paragraph(f"<b>ADEUDO PENDIENTE: ${total_deuda_periodo:,.2f}</b>", 
                                    ParagraphStyle('Alerta', parent=self.estilos['Normal'], textColor=colors.red, alignment=TA_RIGHT, fontSize=12))
                self.elementos.append(p_deuda)
        # ==========================================================

        # 6. PIE DE PÁGINA Y CIERRE
        self.elementos.append(Spacer(1, 40))
        
        # Obtenemos fecha actual para el pie
        fecha_consulta = datetime.now().strftime("%d/%m/%Y %H:%M")
        estilo_pie = ParagraphStyle('Pie', parent=self.estilos['Normal'], fontSize=8, alignment=TA_RIGHT, textColor=colors.HexColor("#94A3B8"))
        self.elementos.append(Paragraph(f"Documento consultado el: {fecha_consulta}", estilo_pie))
        
        return self._finalizar_reporte()
    

    
    def generar_ticket_incidencia(self, taxi, tipo, descripcion, monto, operadora, fecha_personalizada=None):
        if fecha_personalizada: fecha_texto = fecha_personalizada; titulo = f"COPIA REPORTE - TAXI {taxi}"
        else: fecha_texto = datetime.now().strftime('%d/%m/%Y %H:%M'); titulo = f"INCIDENCIA - TAXI {taxi}"

        self._agregar_encabezado(titulo, fecha_texto)
        color = colors.HexColor("#FEE2E2") if monto > 0 else colors.HexColor("#FEF3C7")
        t = Table([["TIPO:", tipo], ["DETALLE:", Paragraph(descripcion, self.estilo_normal)], ["MONTO:", f"${monto:,.2f}"]], colWidths=[2*inch, 4*inch])
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), color), ('GRID', (0,0), (-1,-1), 1, colors.white), ('PADDING', (0,0), (-1,-1), 12)]))
        self.elementos.append(t)
        self._finalizar_reporte()