from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.units import inch
from datetime import datetime
import os
import sys  # <--- IMPORTANTE PARA EL EXE
import matplotlib.pyplot as plt
from io import BytesIO

# ==========================================
# FUNCIÓN MÁGICA PARA ENCONTRAR ARCHIVOS EN EL .EXE
# ==========================================
def ruta_recurso(relativo):
    """ Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relativo)


class GeneradorPDF:
    def __init__(self, nombre_archivo):
        self.nombre_archivo = nombre_archivo
        self.doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, 
                                     topMargin=30, bottomMargin=30, 
                                     leftMargin=30, rightMargin=30)
        self.elementos = []
        self.estilos = getSampleStyleSheet()
        
        # Estilos Compactos
        self.estilo_empresa = ParagraphStyle('Empresa', parent=self.estilos['Heading1'], fontSize=16, textColor=colors.HexColor("#1E293B"), alignment=TA_LEFT)
        self.estilo_programa = ParagraphStyle('Programa', parent=self.estilos['Normal'], fontSize=9, textColor=colors.HexColor("#64748B"), alignment=TA_LEFT)
        self.estilo_titulo = ParagraphStyle('TituloRep', parent=self.estilos['Heading2'], fontSize=14, alignment=TA_CENTER, spaceAfter=5, textColor=colors.HexColor("#0F172A"))
        self.estilo_periodo = ParagraphStyle('PeriodoRep', parent=self.estilos['Normal'], fontSize=11, alignment=TA_CENTER, textColor=colors.HexColor("#475569"))
        self.estilo_sub = ParagraphStyle('SubTitulo', parent=self.estilos['Heading3'], fontSize=11, textColor=colors.HexColor("#334155"), spaceBefore=10, spaceAfter=2)

    def _crear_grafico_barras(self, etiquetas, valores, titulo, color_barras, xlabel, ylabel, ancho=7.5, alto=2.2):
        plt.figure(figsize=(ancho, alto))
        plt.bar(etiquetas, valores, color=color_barras, width=0.6)
        
        plt.title(titulo, fontsize=9, fontweight='bold', color="#333333", pad=4)
        plt.xlabel(xlabel, fontsize=7, labelpad=2)
        plt.ylabel(ylabel, fontsize=7, labelpad=2)
        plt.xticks(fontsize=7, rotation=0)
        plt.yticks(fontsize=7)
        
        plt.gca().spines['top'].set_visible(False)
        plt.gca().spines['right'].set_visible(False)
        plt.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout(pad=0.5) 
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        plt.close()
        buffer.seek(0)
        return Image(buffer, width=ancho*inch, height=alto*inch)

    def _crear_grafico_pastel(self, etiquetas, valores, titulo):
        plt.figure(figsize=(4, 3)) 
        colores = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#6366F1', '#EC4899']
        
        wedges, texts, autotexts = plt.pie(
            valores, labels=None, autopct='%1.1f%%', startangle=140, 
            colors=colores, pctdistance=0.75, shadow=False
        )
        for t in autotexts:
            t.set_color('white')
            t.set_fontweight('bold')
            t.set_fontsize(8)
            
        plt.title(titulo, fontsize=10, fontweight='bold', color="#333333")
        plt.legend(wedges, etiquetas, title="Bases", loc="center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=7)
        plt.axis('equal') 
        plt.tight_layout()
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        plt.close()
        buffer.seek(0)
        return Image(buffer, width=3.5*inch, height=2.6*inch)

    def generar_reporte_global(self, periodo, texto_fecha, datos):
        # === 1. ENCABEZADO (AQUÍ ESTÁ EL CAMBIO DEL LOGO) ===
        logo = []
        
        # Usamos la función mágica para buscar la ruta correcta
        nombre_logo = ruta_recurso("LogoElZorropng.png") 
        
        if os.path.exists(nombre_logo):
            img = Image(nombre_logo, width=1.0*inch, height=1.0*inch)
            img.hAlign = 'RIGHT'
            logo = img
        
        t_head = Table([[[Paragraph("<b>TAXIS EL ZORRO</b>", self.estilo_empresa), 
                          Paragraph("Reporte Operativo Global", self.estilo_programa)], logo]], 
                       colWidths=[400, 150])
        t_head.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        self.elementos.append(t_head)
        self.elementos.append(Table([[""]], colWidths=[550], style=[('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#FACC15"))])) 
        self.elementos.append(Spacer(1, 10)) 

        # TÍTULO
        self.elementos.append(Paragraph(f"REPORTE EJECUTIVO: {periodo}", self.estilo_titulo))
        self.elementos.append(Paragraph(texto_fecha, self.estilo_periodo))
        self.elementos.append(Spacer(1, 10))

        # === 2. KPI ===
        tot = datos['totales']
        prom = tot['ganancia'] / tot['viajes'] if tot['viajes'] > 0 else 0
        t_kpi = Table([["INGRESOS", "VIAJES", "TICKET PROM."], 
                       [f"${tot['ganancia']:,.2f}", f"{tot['viajes']:,}", f"${prom:,.2f}"]], 
                       colWidths=[180, 180, 180])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")), ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#FACC15")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,1), (-1,1), 14),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")), ('BOTTOMPADDING', (0,0), (-1,-1), 6), ('TOPPADDING', (0,0), (-1,-1), 6)
        ]))
        self.elementos.append(t_kpi)
        self.elementos.append(Spacer(1, 15))

        # === 3. GRÁFICAS DE TIEMPO ===
        elementos_graficos = []
        
        if datos['semana']:
            elementos_graficos.append(Paragraph("📅 Ritmo Semanal", self.estilo_sub))
            dias_labels = [x[0] for x in datos['semana']]
            dias_vals = [x[1] for x in datos['semana']]
            elementos_graficos.append(self._crear_grafico_barras(dias_labels, dias_vals, "Viajes por Día", "#8B5CF6", "", "", ancho=7.5, alto=2.0))
            elementos_graficos.append(Spacer(1, 5))

        elementos_graficos.append(Paragraph("⏰ Demanda por Hora", self.estilo_sub))
        h_labels = [h[0] for h in datos['horas_pico']]
        h_vals = [h[1] for h in datos['horas_pico']]
        h_visibles = [h if int(h)%2==0 else "" for h in h_labels]
        elementos_graficos.append(self._crear_grafico_barras(h_visibles, h_vals, "Viajes por Hora (0-23h)", "#00D1FF", "Hora", "Viajes", ancho=7.5, alto=2.0))
        
        self.elementos.append(KeepTogether(elementos_graficos))
        self.elementos.append(Spacer(1, 15))

        # === 4. TABLAS TOP ===
        self.elementos.append(Paragraph("🏆 Salón de la Fama", self.estilo_sub))
        self.elementos.append(Spacer(1, 5))

        def armar_tabla_top(titulo, lista, color, simbolo):
            d = [[titulo, "VALOR"]]
            for n, v in lista:
                val = f"{simbolo}{v:,.2f}" if simbolo == "$" else f"{v:,.1f} h" if simbolo == "" and isinstance(v, float) else f"{v}"
                d.append([f"Taxi {n}", val])
            t = Table(d, colWidths=[120, 80])
            t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor(color)), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                                   ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 8),
                                   ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F1F5F9")]), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
            return t

        t1 = armar_tabla_top("MAYORES INGRESOS", datos['top_dinero'], "#10B981", "$")
        t2 = armar_tabla_top("MÁS VIAJES", datos['top_viajes'], "#3B82F6", "")
        t3 = armar_tabla_top("MÁS TRABAJADORES", datos['top_horas'], "#F472B6", "")
        
        t_tops_safe = Table([[t1, Spacer(10,10), t2], [Spacer(5,5), t3, Spacer(5,5)]], colWidths=[200, 20, 200])
        t_tops_safe.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (0,1), (-1,1), 'CENTER')]))
        self.elementos.append(t_tops_safe)
        self.elementos.append(Spacer(1, 15))

        # === 5. ESTRATEGIA DE BASES ===
        self.elementos.append(Paragraph("🎯 Estrategia de Bases", self.estilo_sub))
        self.elementos.append(Spacer(1, 5))

        l_bases = [b[0] for b in datos['bases']]
        v_bases = [b[1] for b in datos['bases']]
        grafico_bases = self._crear_grafico_pastel(l_bases, v_bases, "Distribución")

        data_picos = [["BASE", "DÍA", "HORA", "V."]]
        for b in datos['bases_pico']:
            data_picos.append([b[0], b[1], b[2], str(b[3])])
            
        t_picos = Table(data_picos, colWidths=[120, 60, 50, 40])
        t_picos.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F46E5")), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#EEF2FF")]), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C7D2FE"))
        ]))
        
        tabla_final = Table([[grafico_bases, t_picos]], colWidths=[280, 270])
        tabla_final.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'CENTER'), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        self.elementos.append(tabla_final)

        try:
            self.doc.build(self.elementos)
            print(f"PDF Generado: {self.nombre_archivo}")
            os.startfile(self.nombre_archivo)
        except Exception as e: print(e)

    # --- REPORTE INDIVIDUAL (ACTUALIZADO CON RUTA RECURSO TAMBIÉN) ---
    def generar_reporte_unidad(self, numero_taxi, texto_fecha, stats, lista_viajes):
        self._generar_reporte_unidad_existente(numero_taxi, texto_fecha, stats, lista_viajes)

    def _generar_reporte_unidad_existente(self, numero_taxi, texto_fecha, stats, lista_viajes):
        logo = []
        
        # CAMBIO AQUÍ TAMBIÉN
        nombre_logo = ruta_recurso("LogoElZorropng.png") 
        
        if os.path.exists(nombre_logo):
            img = Image(nombre_logo, width=1.0*inch, height=1.0*inch)
            img.hAlign = 'RIGHT'
            logo = img
        
        t_h = Table([[[Paragraph("<b>TAXIS EL ZORRO</b>", self.estilo_empresa), Paragraph("Reporte Individual", self.estilo_programa)], logo]], colWidths=[400, 150])
        self.elementos.append(t_h)
        self.elementos.append(Table([[""]], colWidths=[550], style=[('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#00D1FF"))]))
        self.elementos.append(Spacer(1, 10))
        self.elementos.append(Paragraph(f"UNIDAD #{numero_taxi}", self.estilo_titulo))
        self.elementos.append(Paragraph(f"{texto_fecha}", self.estilo_periodo))
        self.elementos.append(Spacer(1, 15))

        d_res = [["INGRESOS", "VIAJES", "HORAS"], [f"${stats['ganancia']:,.2f}", f"{stats['viajes']:,}", f"{stats['horas']:,.1f} h"]]
        t_res = Table(d_res, colWidths=[180, 180, 180])
        t_res.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                                   ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('FONTSIZE', (0,1), (-1,1), 14), ('TEXTCOLOR', (0,1), (0,1), colors.HexColor("#10B981"))]))
        self.elementos.append(t_res)
        self.elementos.append(Spacer(1, 20))

        self.elementos.append(Paragraph("Desglose de Viajes", self.estilo_sub))
        enc = ["FECHA", "HORA", "CONCEPTO", "ORIGEN", "DESTINO", "COSTO"]
        dat = [enc]
        for v in lista_viajes:
            fh = str(v['fecha_hora_inicio']).split(" ")
            dat.append([fh[0], fh[1][:5] if len(fh)>1 else "", v.get('concepto',''), v.get('origen',''), Paragraph(v.get('destino',''), self.estilos["Normal"]), f"${v['precio']:,.2f}"])
        
        t_det = Table(dat, colWidths=[70, 40, 80, 80, 200, 70], repeatRows=1)
        t_det.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                                   ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F1F5F9")]), ('FONTSIZE', (0,0), (-1,-1), 8)]))
        self.elementos.append(t_det)
        
        try:
            self.doc.build(self.elementos)
            os.startfile(self.nombre_archivo)
        except Exception as e: print(e)