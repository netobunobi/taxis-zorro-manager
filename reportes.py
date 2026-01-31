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

        titulo = "REPORTE OPERATIVO" if tipo_reporte == "PUBLICO" else "REPORTE GERENCIAL COMPLETO"
        self._agregar_encabezado(titulo, f"Periodo: {periodo} | {fecha_texto}")

        # Datos
        totales = datos_generales['totales']
        lista_flota = datos_generales.get('detalle_flota', [])
        inc_list = datos_generales.get('incidencias_lista', []) 
        incidencias = datos_generales['incidencias']

        # Detección de Reporte Diario
        import re
        es_reporte_diario = False
        periodo_str = str(periodo).upper().strip()
        if "TURNO" in periodo_str or "DÍA" in periodo_str or "DIA" in periodo_str:
            es_reporte_diario = True
        elif re.search(r'\d{4}-\d{2}-\d{2}', periodo_str):
            es_reporte_diario = True

        # 1. MÉTRICAS GLOBALES
        ausencias_reales = 0
        if inc_list:
            for item in inc_list:
                if "AUSENCIA" in str(item['tipo']).upper() or "FALTA" in str(item['tipo']).upper(): 
                    ausencias_reales += 1

        d_ops = [
            ["METRICAS GLOBALES", "CANTIDAD"],
            ["Viajes Totales Realizados", str(totales['viajes'])],
            ["Total Incidencias Registradas", str(incidencias['total_count'])],
            ["Ausencias / Faltas", str(ausencias_reales)] 
        ]
        t_ops = Table(d_ops, colWidths=[4*inch, 2*inch])
        t_ops.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        self.elementos.append(t_ops)
        self.elementos.append(Spacer(1, 15))

        # 2. SÁBANA DE LA FLOTA
        if lista_flota:
            self.elementos.append(Paragraph("RESUMEN DE ACTIVIDAD POR UNIDAD", self.estilo_sub))
            
            head_flota = ["TAXI", "VIAJES", "HORAS", "INGRESOS"]
            data_flota = [head_flota]
            lista_flota.sort(key=lambda x: int(x['numero']))

            sum_viajes = 0; sum_horas = 0.0; sum_dinero = 0.0

            for taxi in lista_flota:
                v = int(taxi.get('viajes', 0))
                h = float(taxi.get('horas', 0))
                d = float(taxi.get('dinero', 0))
                es_justif = taxi.get('es_justificado', False)
                motivo = taxi.get('motivo_inactividad', "JUSTIF")

                sum_viajes += v; sum_horas += h; sum_dinero += d
                
                if h == 0 and es_justif:
                    txt_dinero = motivo
                else:
                    txt_dinero = f"${d:,.2f}"

                data_flota.append([f"Unidad {taxi['numero']}", str(v), f"{h:.1f} h", txt_dinero])

            txt_total = f"${sum_dinero:,.2f}" if tipo_reporte == "ADMIN" else "---"
            data_flota.append(["TOTALES", str(sum_viajes), f"{sum_horas:.1f} h", txt_total])

            t_flota = Table(data_flota, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1.5*inch])
            
            estilo_flota = [
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0,1), (-2,-1), [colors.white, colors.HexColor("#F8FAFC")]),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#CBD5E1")),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ]

            # --- LÓGICA DE COLORES AJUSTADA ---
            if es_reporte_diario:
                for i, taxi in enumerate(lista_flota):
                    horas = float(taxi.get('horas', 0))
                    es_justificado = taxi.get('es_justificado', False)
                    idx = i + 1 

                    if es_justificado:
                        # GRIS: Justificado (Toda la fila gris suave para indicar inactividad permitida)
                        estilo_flota.append(('BACKGROUND', (0, idx), (-1, idx), colors.HexColor("#E2E8F0")))
                        estilo_flota.append(('TEXTCOLOR', (0, idx), (-1, idx), colors.gray))
                    
                    elif horas < 10.0:
                        # ALERTA: Trabajó poco o nada
                        # SOLO afectamos la celda de horas (Columna 2)
                        
                        estilo_flota.append(('BACKGROUND', (2, idx), (2, idx), colors.HexColor("#FECACA"))) # Fondo rosita
                        estilo_flota.append(('TEXTCOLOR', (2, idx), (2, idx), colors.red)) # Texto rojo
                        
                        # Si es prácticamente cero (< 1 hora), le ponemos NEGRITAS a la hora para que resalte más
                        if horas < 1.0:
                             estilo_flota.append(('FONTNAME', (2, idx), (2, idx), 'Helvetica-Bold'))
                             # NOTA: Ya NO tocamos el resto de la fila (0, idx) ni (-1, idx). Solo la (2).

            t_flota.setStyle(TableStyle(estilo_flota))
            self.elementos.append(t_flota)
            self.elementos.append(Spacer(1, 20))

        # 3. LISTADO DE INCIDENCIAS
        lista_multas = []
        if inc_list:
            for inc in inc_list:
                tipo = str(inc['tipo']).upper()
                desc = str(inc['descripcion']).upper()
                if "PISO" in tipo or "PISO" in desc:
                    continue
                lista_multas.append(inc)

        if lista_multas:
            self.elementos.append(Paragraph("DETALLE DE MULTAS Y OBSERVACIONES", self.estilo_sub))
            head_inc = ["TAXI", "TIPO", "DETALLE", "MONTO/ESTADO"]
            data_inc = [head_inc]
            
            for item in lista_multas:
                tipo_limpio = str(item['tipo']).replace("⚠️ ", "").replace("🛑 ", "").replace("🚩 ", "").replace("🚫 ", "").replace("💸 ", "")
                detalle = str(item['descripcion'])
                monto = float(item.get('monto', 0))
                col_fin = f"${monto:,.2f}" if monto > 0 else "REPORTE"
                
                fila = [
                    f"Taxi {item['unidad']}",
                    tipo_limpio,
                    Paragraph(detalle, self.estilo_normal),
                    col_fin
                ]
                data_inc.append(fila)

            t_inc = Table(data_inc, colWidths=[0.8*inch, 1.5*inch, 3.2*inch, 1.5*inch])
            t_inc.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F87171")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 9),
            ]))
            self.elementos.append(t_inc)
            self.elementos.append(Spacer(1, 20))
        else:
            self.elementos.append(Paragraph("Sin multas ni reportes disciplinarios en este periodo.", self.estilo_normal))
            self.elementos.append(Spacer(1, 20))

        # 4. TOTALES EMPRESA (SOLO ADMIN)
        if tipo_reporte == "ADMIN" and lista_flota:
            ganancia_total = sum(float(x['dinero']) for x in lista_flota)
            t_money = Table([["INGRESOS TOTALES (FLOTA + MULTAS)"], [f"${ganancia_total:,.2f}"]], colWidths=[4*inch])
            t_money.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#10B981")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white), 
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
                ('FONTSIZE', (0,1), (-1,1), 18)
            ]))
            self.elementos.append(Spacer(1, 15))
            self.elementos.append(t_money)

        self.elementos.append(Spacer(1, 30))
        txt_fin = "*** FIN DEL REPORTE ***"
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