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

**Taxis Zorro Manager** es una solución de software "llave en mano" diseñada para digitalizar la operación de bases de taxis. El sistema elimina el uso de papel, optimiza la asignación de viajes y provee inteligencia de negocios para maximizar los ingresos de la flotilla.

A diferencia de una simple hoja de cálculo, este sistema ofrece un entorno visual con **fichas interactivas**, gestión de estados en tiempo real y generación automática de reportes financieros y operativos.

## 🚀 Características y Funcionalidades

### 🎮 Control Operativo Visual
* **Sistema Drag & Drop:** Asignación de unidades arrastrando fichas visuales (estilo neón) entre bases físicas, zonas de viaje y talleres.
* **Lógica de Rebote:** Detección automática de viajes consecutivos y validaciones de seguridad para evitar errores de captura.
* **Gestión de Flota:** Base de datos pre-cargada con unidades del 35 al 100, con capacidad de altas y bajas administrativas.

### 🧠 Inteligencia de Negocios (BI)
* **Heatmaps de Horas Pico:** Gráficos que muestran las horas de mayor demanda para optimizar la disponibilidad de choferes.
* **Análisis "Momentos de Oro":** Identificación automática de qué base vende más en qué día y a qué hora (ej. *Mercado - Sábado - 12:00 PM*).
* **Rankings de Desempeño:** "Salón de la Fama" con los top 3 conductores por ingresos, número de viajes y horas trabajadas.

### 📉 Reportes Corporativos
* **Reportes PDF Ejecutivos:** Generación de documentos PDF listos para imprimir con:
    * Resumen financiero (Ingresos, Ticket Promedio).
    * Gráficos de pastel y barras integrados.
    * Tablas de desglose detallado.
* **Filtros Temporales:** Reportes por Día, Mes, Año o Histórico completo ("Siempre").

### 🛠️ Detalles Técnicos
* **Pantalla de Carga (Splash Screen):** Inicio profesional con logotipo corporativo.
* **Base de Datos Unificada:** SQLite local optimizada con llaves foráneas e integridad referencial.
* **Portable:** Compilado en un ejecutable `.exe` independiente que no requiere instalación de Python en el cliente.

## 🛠️ Stack Tecnológico

| Categoría | Tecnología | Uso |
| :--- | :--- | :--- |
| **Lenguaje** | ![Python](https://img.shields.io/badge/-Python-black?style=flat&logo=python) | Lógica de negocio y backend. |
| **Interfaz (GUI)** | ![PyQt](https://img.shields.io/badge/-PyQt6-green?style=flat&logo=qt) | Ventanas, eventos, Drag & Drop y estilos CSS. |
| **Base de Datos** | ![SQLite](https://img.shields.io/badge/-SQLite-blue?style=flat&logo=sqlite) | Almacenamiento local de viajes y catálogos. |
| **Reportes** | **ReportLab** | Motor de generación de PDFs pixel-perfect. |
| **Análisis** | **Matplotlib** | Generación de gráficos estadísticos para reportes. |
| **Empaquetado** | **PyInstaller** | Compilación a binario (.exe) para Windows. |

## 📥 Descarga e Instalación (Usuario Final)

1. Ve a la sección de **[Releases](https://github.com/netobunobi/taxis-zorro-manager/releases)** de este repositorio.
2. Descarga el archivo `.zip` de la última versión.
3. Descomprime la carpeta en tu Escritorio.
4. Ejecuta `SistemaTaxisZorro.exe`.
   * *Nota: Asegúrate de que el archivo `taxis.db` esté en la misma carpeta que el ejecutable.*

## 🔧 Instalación y Desarrollo (Para Programadores)

Si deseas clonar y modificar el código fuente:

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/netobunobi/taxis-zorro-manager.git](https://github.com/netobunobi/taxis-zorro-manager.git)
   cd taxis-zorro-manager