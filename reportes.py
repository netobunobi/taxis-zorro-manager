from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.units import inch
from datetime import datetime
import os
import matplotlib.pyplot as plt
from io import BytesIO

class GeneradorPDF:
    def __init__(self, nombre_archivo):
        # Márgenes ajustados
        self.nombre_archivo = nombre_archivo
        self.doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, topMargin=30, bottomMargin=30, leftMargin=40, rightMargin=40)
        self.elementos = []
        self.estilos = getSampleStyleSheet()
        
        # Estilos Personalizados
        self.estilo_empresa = ParagraphStyle('Empresa', parent=self.estilos['Heading1'], fontSize=18, textColor=colors.HexColor("#1E293B"), alignment=TA_LEFT)
        self.estilo_programa = ParagraphStyle('Programa', parent=self.estilos['Normal'], fontSize=10, textColor=colors.HexColor("#64748B"), alignment=TA_LEFT)
        self.estilo_titulo = ParagraphStyle('TituloRep', parent=self.estilos['Heading2'], fontSize=16, alignment=TA_CENTER, spaceAfter=10, textColor=colors.HexColor("#0F172A"))
        self.estilo_sub = ParagraphStyle('SubTitulo', parent=self.estilos['Heading3'], fontSize=12, textColor=colors.HexColor("#334155"), spaceBefore=15)
        self.estilo_periodo = ParagraphStyle('PeriodoRep', parent=self.estilos['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor("#475569"))

    def _crear_grafico_barras(self, etiquetas, valores, titulo, color_barras, xlabel, ylabel):
        """ Gráfico de Barras Verticales (Para Horas Pico) """
        plt.figure(figsize=(7, 3))
        plt.bar(etiquetas, valores, color=color_barras, width=0.7)
        plt.title(titulo, fontsize=10, fontweight='bold', color="#333333")
        plt.xlabel(xlabel, fontsize=8)
        plt.ylabel(ylabel, fontsize=8)
        plt.xticks(fontsize=7, rotation=0)
        plt.yticks(fontsize=7)
        
        # Estilo limpio
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        plt.close()
        buffer.seek(0)
        
        img = Image(buffer, width=7*inch, height=3*inch)
        return img

    def _crear_grafico_pastel(self, etiquetas, valores, titulo):
        """ 
        Gráfico de Pastel MEJORADO:
        - Más grande.
        - Sin agujero (para mejor lectura).
        - Leyenda separada.
        """
        # Hacemos la figura más ancha (6x4 pulgadas)
        plt.figure(figsize=(6, 3.5))
        
        colores = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#6366F1', '#EC4899']
        
        # Pastel completo (sin dona)
        wedges, texts, autotexts = plt.pie(
            valores, 
            labels=None, # Quitamos etiquetas externas para que no se encimen
            autopct='%1.1f%%', 
            startangle=140, 
            colors=colores, 
            pctdistance=0.75, # Porcentajes más adentro
            shadow=False
        )
        
        # Estilo de los textos de porcentaje
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
        
        plt.title(titulo, fontsize=11, fontweight='bold', color="#333333")
        
        # Leyenda a la derecha para que no estorbe
        plt.legend(wedges, etiquetas, title="Bases", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8)
        
        plt.axis('equal') 
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        plt.close()
        buffer.seek(0)
        
        # Retornamos imagen grande
        img = Image(buffer, width=6*inch, height=3.5*inch)
        return img

    def generar_reporte_global(self, periodo, texto_fecha, datos):
        # 1. ENCABEZADO
        logo = []
        nombre_logo = "LogoElZorropng.png"
        if os.path.exists(nombre_logo):
            img = Image(nombre_logo, width=1.2*inch, height=1.2*inch)
            img.hAlign = 'RIGHT'
            logo = img
        
        header_data = [[[Paragraph("<b>TAXIS EL ZORRO</b>", self.estilo_empresa), 
                        Paragraph("Reporte Operativo Global", self.estilo_programa)], logo]]
        t_head = Table(header_data, colWidths=[350, 150])
        t_head.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        self.elementos.append(t_head)
        self.elementos.append(Table([[""]], colWidths=[500], style=[('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#FACC15"))])) 
        self.elementos.append(Spacer(1, 15))

        # TÍTULO
        self.elementos.append(Paragraph(f"REPORTE EJECUTIVO: {periodo}", self.estilo_titulo))
        self.elementos.append(Paragraph(texto_fecha, self.estilo_periodo))
        self.elementos.append(Spacer(1, 20))

        # 2. KPI Principales
        tot = datos['totales']
        promedio = tot['ganancia'] / tot['viajes'] if tot['viajes'] > 0 else 0
        
        fila_kpi = [
            [f"${tot['ganancia']:,.2f}", f"{tot['viajes']:,}", f"${promedio:,.2f}"]
        ]
        t_kpi = Table([["INGRESOS TOTALES", "VIAJES TOTALES", "TICKET PROMEDIO"]] + fila_kpi, colWidths=[170, 170, 170])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#FACC15")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,1), (-1,1), 16),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
        ]))
        self.elementos.append(t_kpi)
        self.elementos.append(Spacer(1, 20))

        # 3. GRÁFICO 1: HORAS PICO
        self.elementos.append(Paragraph("📊 Demanda por Hora (Horas Pico)", self.estilo_sub))
        horas_labels = [h[0] for h in datos['horas_pico']]
        horas_values = [h[1] for h in datos['horas_pico']]
        horas_visibles = [h if int(h)%2==0 else "" for h in horas_labels]
        
        grafico_horas = self._crear_grafico_barras(
            horas_visibles, horas_values, 
            "Viajes solicitados por hora del día", 
            "#00D1FF", "Hora (00-23)", "Cantidad Viajes"
        )
        self.elementos.append(grafico_horas)
        self.elementos.append(Spacer(1, 15))

        # 4. TABLAS DE RANKING
        self.elementos.append(Paragraph("Mejores Rendimientos", self.estilo_sub))
        self.elementos.append(Spacer(1, 10))

        def armar_tabla_top(titulo, lista_datos, color_header, simbolo_valor):
            data = [[titulo, "VALOR"]]
            for num, valor in lista_datos:
                val_fmt = f"{simbolo_valor}{valor:,.2f}" if simbolo_valor == "$" else f"{valor:,.1f} h" if simbolo_valor == "" and isinstance(valor, float) else f"{valor}"
                data.append([f"Taxi {num}", val_fmt])
            
            t = Table(data, colWidths=[130, 90])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor(color_header)),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F1F5F9")])
            ]))
            return t

        t_money = armar_tabla_top("MAYORES INGRESOS", datos['top_dinero'], "#10B981", "$")
        t_viajes = armar_tabla_top("MÁS VIAJES", datos['top_viajes'], "#3B82F6", "")
        t_horas = armar_tabla_top("MÁS TRABAJADORES", datos['top_horas'], "#F472B6", "")

        t_fila1 = Table([[t_money, Spacer(20, 10), t_viajes]], colWidths=[220, 30, 220])
        t_fila1.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        self.elementos.append(t_fila1)
        self.elementos.append(Spacer(1, 10))

        t_fila2 = Table([[Spacer(10,10), t_horas, Spacer(10,10)]], colWidths=[130, 220, 130])
        self.elementos.append(t_fila2)
        
        # Agregamos un salto de página si estamos muy abajo, o solo espacio
        self.elementos.append(Spacer(1, 20))

        # 5. ANÁLISIS DE BASES (MODIFICADO: Vertical)
        self.elementos.append(Paragraph("🏢 Bases Más Rentables", self.estilo_sub))
        
        labels_bases = [b[0] for b in datos['bases']]
        values_bases = [b[1] for b in datos['bases']]
        
        # 1. GRÁFICA PRIMERO (Grande y centrada)
        grafico_bases = self._crear_grafico_pastel(labels_bases, values_bases, "Distribución de Viajes por Base")
        self.elementos.append(grafico_bases)
        self.elementos.append(Spacer(1, 10))
        
        # 2. TABLA DESPUÉS (Centrada abajo)
        data_bases = [["POS.", "NOMBRE BASE", "VIAJES"]]
        for i, (nom, cant) in enumerate(datos['bases'], 1):
            data_bases.append([str(i), nom, str(cant)])
        
        t_bases_data = Table(data_bases, colWidths=[40, 200, 80])
        t_bases_data.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#64748B")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F1F5F9")])
        ]))
        
        self.elementos.append(t_bases_data)

        try:
            self.doc.build(self.elementos)
            print(f"PDF Global Generado: {self.nombre_archivo}")
            os.startfile(self.nombre_archivo)
        except Exception as e:
            print(f"Error PDF: {e}")

    # --- REPORTE INDIVIDUAL ---
    def generar_reporte_unidad(self, numero_taxi, texto_fecha, stats, lista_viajes):
        # 1. ENCABEZADO
        logo = []
        nombre_logo = "LogoElZorropng.png"
        if os.path.exists(nombre_logo):
            img = Image(nombre_logo, width=1.2*inch, height=1.2*inch)
            img.hAlign = 'RIGHT'
            logo = img
        
        datos_header = [[[Paragraph("<b>TAXIS EL ZORRO</b>", self.estilo_empresa), 
                         Paragraph("Sistema de Gestión v1.0", self.estilo_programa)], logo]]
        
        tabla_header = Table(datos_header, colWidths=[350, 150])
        tabla_header.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,0), 'LEFT'), ('ALIGN', (1,0), (1,0), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        self.elementos.append(tabla_header)
        self.elementos.append(Table([[""]], colWidths=[500], style=[('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#00D1FF"))]))
        self.elementos.append(Spacer(1, 20))

        # 2. TÍTULOS
        self.elementos.append(Paragraph(f"REPORTE DE UNIDAD #{numero_taxi}", self.estilo_titulo))
        self.elementos.append(Paragraph(f"{texto_fecha}", self.estilo_periodo))
        self.elementos.append(Spacer(1, 25))

        # 3. TARJETAS
        ingresos_fmt = f"${stats['ganancia']:,.2f}"
        viajes_fmt = f"{stats['viajes']:,}"
        horas_fmt = f"{stats['horas']:,.1f} hrs"

        datos_resumen = [["INGRESOS TOTALES", "VIAJES REALIZADOS", "HORAS TRABAJADAS"], [ingresos_fmt, viajes_fmt, horas_fmt]]
        tabla_resumen = Table(datos_resumen, colWidths=[160, 160, 160])
        tabla_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,1), (-1,1), 16),
            ('TEXTCOLOR', (0,1), (0,1), colors.HexColor("#10B981")), ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1"))
        ]))
        self.elementos.append(tabla_resumen)
        self.elementos.append(Spacer(1, 30))

        # 4. TABLA DETALLES
        self.elementos.append(Paragraph("Desglose de Operaciones", self.estilos['Heading3']))
        self.elementos.append(Spacer(1, 10))
        
        encabezados = ["FECHA", "HORA", "CONCEPTO", "ORIGEN", "DESTINO", "COSTO"]
        datos_tabla = [encabezados]
        
        for v in lista_viajes:
            fh = str(v['fecha_hora_inicio']).split(" ")
            fecha = fh[0]
            hora = fh[1][:5] if len(fh)>1 else ""
            precio_fmt = f"${v['precio']:,.2f}"
            fila = [fecha, hora, v.get('concepto', 'Viaje'), v.get('origen', '---'), 
                    Paragraph(v.get('destino', ''), self.estilos["Normal"]), precio_fmt]
            datos_tabla.append(fila)

        tabla_detalle = Table(datos_tabla, colWidths=[70, 50, 80, 80, 140, 70], repeatRows=1)
        tabla_detalle.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F1F5F9")]), ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ]))
        
        self.elementos.append(tabla_detalle)
        self.elementos.append(Spacer(1, 30))
        
        # 5. PIE
        fecha_gen = datetime.now().strftime("%d/%m/%Y %I:%M %p")
        self.elementos.append(Paragraph(f"Reporte generado el: {fecha_gen}", self.estilos["Normal"]))

        try:
            self.doc.build(self.elementos)
            print(f"PDF Creado: {self.nombre_archivo}")
            os.startfile(self.nombre_archivo)
        except Exception as e:
            print("Error generando PDF:", e)