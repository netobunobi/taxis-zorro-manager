<div align="center">

# 🚖 Taxis Zorro Manager

**Sistema Integral de Gestión de Flotilla, Despacho y Business Intelligence**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?style=for-the-badge&logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/Data-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/Estado-Terminado%20(v1.0)-success?style=for-the-badge)
![Platform](https://img.shields.io/badge/Plataforma-Windows-blueviolet?style=for-the-badge&logo=windows&logoColor=white)

</div>

---

## 📄 Descripción

**Taxis Zorro Manager** es una solución de software "llave en mano" diseñada para digitalizar la operación de bases de taxis. El sistema elimina el uso de bitácoras en papel, optimiza la asignación de viajes y provee inteligencia de negocios para maximizar los ingresos de la flotilla.

A diferencia de una simple hoja de cálculo, este sistema ofrece un entorno visual con **fichas interactivas**, gestión de estados en tiempo real y generación automática de reportes financieros y operativos.

## 🚀 Características y Funcionalidades

### 🎮 Control Operativo Visual (Semáforo Inteligente)
El sistema utiliza un código de colores automatizado para alertar a las operadoras sobre demoras sin necesidad de revisar el reloj:

* **Sistema Drag & Drop:** Asignación de unidades arrastrando fichas visuales (estilo neón) entre bases físicas, zonas de viaje y talleres.
* 🟨 **Amarillo (Estándar):** Unidad operativa y en tiempo correcto.
* 🌑 **Gris Acero:** Unidad en "Fuera de Servicio" (No disponible).
* 🟧 **Naranja (Alerta):** Retraso leve (ej. >30 min en viaje local).
* 🟥 **Rojo (Crítico):** Demora excesiva (ej. >45 min en viaje local).
* **Tooltips Vivos:** Al pasar el mouse sobre una unidad, se despliega una tarjeta con el tiempo exacto transcurrido y su estado detallado.

### 🧠 Inteligencia de Negocios (BI)
* **Heatmaps de Horas Pico:** Gráficos que muestran las horas de mayor demanda para optimizar la disponibilidad de choferes.
* **Estrategia Operativa:** Identificación automática de qué base vende más en qué día y a qué hora (ej. *Mercado - Sábado - 12:00 PM*).
* **Salón de la Fama:** Rankings automáticos con los top 3 conductores por ingresos generados, número de viajes y horas trabajadas.

### 🛡️ Seguridad y Administrativo
* **Multas Automáticas:** Detección de incumplimiento de horarios laborales con generación automática de adeudos.
* **Reimpresión de Tickets:** Recuperación de reportes históricos con fecha original y firma digital de la operadora (Audit Trail).
* **Respaldo Automático (Backup):** Sistema de seguridad silencioso que crea una copia de la base de datos cada vez que se inicia el programa en la carpeta oculta `/RESPALDOS_AUTO`.

### 📉 Reportes Corporativos
* **Reportes PDF Ejecutivos:** Generación de documentos listos para imprimir con resumen financiero, ticket promedio y gráficos de pastel/barras (Matplotlib).
* **Filtros Temporales:** Generación de reportes por Día, Mes, Año o Histórico completo ("Siempre").
* **Diseño Profesional:** Documentos membretados con logotipo corporativo y diseño limpio.

---

## 🛠️ Stack Tecnológico

Este proyecto ha sido desarrollado utilizando herramientas modernas y librerías robustas de Python:

| Categoría | Tecnología | Uso |
| :--- | :--- | :--- |
| **Lenguaje** | ![Python](https://img.shields.io/badge/-Python-black?style=flat&logo=python) | Lógica de negocio y backend. |
| **Interfaz (GUI)** | ![PyQt](https://img.shields.io/badge/-PyQt6-green?style=flat&logo=qt) | Ventanas, eventos, Drag & Drop y estilos CSS. |
| **Base de Datos** | ![SQLite](https://img.shields.io/badge/-SQLite-blue?style=flat&logo=sqlite) | Almacenamiento local de viajes, taxis y catálogos. |
| **Reportes** | **ReportLab** | Motor de generación de PDFs pixel-perfect. |
| **Gráficos** | **Matplotlib** | Visualización de estadísticas y métricas en reportes. |

---

## 📥 Guía de Instalación

### 1. Clonar el repositorio
(Ejecutar esta línea en tu terminal/consola git):
`git clone https://github.com/netobunobi/taxis-zorro-manager.git`
`cd taxis-zorro-manager`

### 2. Crear entorno virtual (Opcional pero recomendado)
(Ejecutar estas líneas en consola):
`python -m venv venv`
`venv\Scripts\activate`

### 3. Instalar dependencias
(Ejecutar esta línea en consola para bajar las librerías):
`pip install -r requirements.txt`

### 4. Ejecutar el Sistema
(Ejecutar esta línea para abrir el programa):
`python interfaz.py`

*(Nota: Al abrir por primera vez, el sistema creará automáticamente el archivo `taxis.db` vacío).*

### 5. Cargar Datos de Prueba (Opcional)
Para ver el sistema lleno de vida (viajes, multas, alertas de colores), ejecuta el script inyector incluido:
`python generar_datos_final.py`

---

## 🛡️ Licencia y Términos de Uso

**Copyright © 2026 Ernesto Velez Ortega. Todos los derechos reservados.**

Este software es **PROPIEDAD PRIVADA** y ha sido desarrollado exclusivamente para la operación interna de **Taxis El Zorro**.

### 1. Restricciones de Uso
El código fuente publicado en este repositorio se exhibe únicamente con fines de **portafolio profesional, educativos y de auditoría técnica**.
* **Queda estrictamente prohibido:** La copia, descarga, redistribución, modificación, venta, uso comercial o uso privado de este software (total o parcial) sin la autorización expresa y por escrito del autor.
* No se concede ninguna licencia implícita ni derechos de propiedad intelectual a terceros que visualicen este repositorio.

### 2. Exención de Responsabilidad (Disclaimer)
ESTE SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO, EXPRESA O IMPLÍCITA. EN NINGÚN CASO EL AUTOR SERÁ RESPONSABLE DE NINGUNA RECLAMACIÓN QUE SURJA DEL USO DEL SOFTWARE.

---
<div align="center">
    <sub>Desarrollado con dedicación por Ernesto Velez Ortega</sub>
</div>