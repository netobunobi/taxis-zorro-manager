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

### 🎮 Control Operativo Visual
* **Sistema Drag & Drop:** Asignación de unidades arrastrando fichas visuales (estilo neón) entre bases físicas, zonas de viaje y talleres.
* **Lógica de Rebote:** Detección automática de viajes consecutivos y validaciones de seguridad para evitar errores de captura.
* **Gestión de Flota:** Base de datos pre-cargada con unidades del 35 al 100, con capacidad de altas y bajas administrativas.
* **Manejo de Estados:** Control visual inmediato de unidades: *En Base* (Amarillo), *En Viaje* (Verde) y *Fuera de Servicio/Taller* (Rojo).

### 🧠 Inteligencia de Negocios (BI)
* **Heatmaps de Horas Pico:** Gráficos que muestran las horas de mayor demanda para optimizar la disponibilidad de choferes.
* **Estrategia Operativa:** Identificación automática de qué base vende más en qué día y a qué hora (ej. *Mercado - Sábado - 12:00 PM*).
* **Salón de la Fama:** Rankings automáticos con los top 3 conductores por ingresos generados, número de viajes y horas trabajadas.

### 📉 Reportes Corporativos
* **Reportes PDF Ejecutivos:** Generación de documentos PDF listos para imprimir con:
    * Resumen financiero (Ingresos Totales, Ticket Promedio).
    * Gráficos de pastel y barras integrados (Matplotlib).
    * Tablas de desglose detallado.
* **Filtros Temporales:** Generación de reportes por Día, Mes, Año o Histórico completo ("Siempre").
* **Diseño Profesional:** Documentos membretados con logotipo corporativo y diseño limpio.

### 🛠️ Detalles Técnicos
* **Pantalla de Carga (Splash Screen):** Inicio profesional con logotipo corporativo mientras carga la base de datos.
* **Base de Datos Unificada:** SQLite local optimizada con llaves foráneas e integridad referencial.
* **Portable:** Compilado en un ejecutable `.exe` independiente que no requiere instalación de Python en el equipo del cliente.

## 🛠️ Stack Tecnológico

Este proyecto ha sido desarrollado utilizando herramientas modernas y librerías robustas de Python:

| Categoría | Tecnología | Uso |
| :--- | :--- | :--- |
| **Lenguaje** | ![Python](https://img.shields.io/badge/-Python-black?style=flat&logo=python) | Lógica de negocio y backend. |
| **Interfaz (GUI)** | ![PyQt](https://img.shields.io/badge/-PyQt6-green?style=flat&logo=qt) | Ventanas, eventos, Drag & Drop y estilos CSS. |
| **Base de Datos** | ![SQLite](https://img.shields.io/badge/-SQLite-blue?style=flat&logo=sqlite) | Almacenamiento local de viajes, taxis y catálogos. |
| **Reportes** | **ReportLab** | Motor de generación de PDFs pixel-perfect. |
| **Gráficos** | **Matplotlib** | Visualización de estadísticas y métricas en reportes. |
| **Empaquetado** | **PyInstaller** | Compilación a binario (.exe) para distribución en Windows. |

## 📥 Descarga e Instalación (Usuario Final)

1. Ve a la sección de **[Releases](https://github.com/netobunobi/taxis-zorro-manager/releases)** de este repositorio.
2. Descarga el archivo `.zip` de la última versión (v1.0).
3. Descomprime la carpeta en tu Escritorio.
4. Ejecuta `SistemaTaxisZorro.exe`.
   * *Nota: Asegúrate de que el archivo `taxis.db` esté siempre en la misma carpeta que el ejecutable.*

## 🔧 Instalación y Desarrollo (Para Programadores)

Si deseas clonar y modificar el código fuente:

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/netobunobi/taxis-zorro-manager.git
   cd taxis-zorro-manager
   ```
   2. **Crear entorno virtual (Recomendado):**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   ```
   3. **Instalar dependencias:**
   ```bash
   pip install PyQt6 matplotlib reportlab pyinstaller
   ```
   4. **Inicializar Base de Datos:**
   ```bash
   python reset_db.py
   ```
   5. **Ejecutar la interfaz:**
   ```bash
   python interfaz.py
   ```
   ## 🛡️ Licencia

**Copyright © 2026 Ernesto Velez Ortega.**

Este proyecto es privado y propietario para uso exclusivo de **Taxis El Zorro**. Todos los derechos reservados.

---
<div align="center">
    <sub>Desarrollado con dedicación por Ernesto Velez Ortega</sub>
</div>  
