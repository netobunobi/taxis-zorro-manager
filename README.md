<div align="center">

# 🚖 Taxis Zorro Manager

**Sistema de Gestión de Flotilla y Despacho de Unidades**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green?style=for-the-badge&logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/Data-SQLite3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Status](https://img.shields.io/badge/Estado-En%20Desarrollo-orange?style=for-the-badge)

</div>

---

## 📄 Descripción

**Taxis Zorro Manager** es una aplicación de escritorio diseñada para modernizar y facilitar la administración de bases de taxis. Sustituye las bitácoras en papel y hojas de cálculo complejas con una interfaz visual intuitiva basada en **Arrastrar y Soltar (Drag & Drop)**.

El sistema permite a las operadoras asignar viajes, controlar tiempos de descanso y generar reportes financieros en tiempo real, minimizando errores humanos en el cobro y registro de datos.

## 🚀 Características Principales

* **🎛️ Tablero Visual Interactivo:** Gestión de unidades mediante sistema Drag & Drop. Mueve taxis visualmente entre las zonas de "Base", "Viaje" y "Taller".
* **⏱️ Control de Tiempos Reales:** Cálculo automático de horas trabajadas vs. horas de descanso/taller.
* **✏️ Corrección de Errores:** Sistema de bitácora editable para corregir tarifas mal ingresadas (ej. *$1500* vs *$150*) recalculando los totales al instante.
* **📊 Reportes y Gráficos:**
    * Generación de reportes PDF para corte de caja.
    * Gráficos estadísticos (Matplotlib) para analizar ingresos por unidad, base con más ventas y tipos de servicio (Teléfono, Aéreo, Base).
* **💾 Base de Datos Local:** Almacenamiento seguro y rápido con SQLite, sin necesidad de conexión a internet constante.

## 🛠️ Stack Tecnológico

Este proyecto ha sido desarrollado utilizando herramientas modernas y librerías robustas de Python:

| Categoría | Tecnología | Uso |
| :--- | :--- | :--- |
| **Lenguaje** | ![Python](https://img.shields.io/badge/-Python-black?style=flat&logo=python) | Lógica del sistema y backend. |
| **Interfaz (GUI)** | ![PyQt](https://img.shields.io/badge/-PyQt6-green?style=flat&logo=qt) | Ventanas, eventos y Drag & Drop. |
| **Base de Datos** | ![SQLite](https://img.shields.io/badge/-SQLite-blue?style=flat&logo=sqlite) | Persistencia de datos local. |
| **Reportes PDF** | **ReportLab / FPDF** | Generación de tickets y reportes impresos. |
| **Gráficos** | **Matplotlib** | Visualización de estadísticas y métricas. |
| **IDE** | ![VS Code](https://img.shields.io/badge/-VS%20Code-007ACC?style=flat&logo=visual-studio-code) | Entorno de desarrollo. |

## 📸 Capturas de Pantalla (Preview)

*(Próximamente: Aquí se mostrará el tablero visual y los gráficos de rendimiento)*

> *El proyecto se encuentra en fase activa de desarrollo de la interfaz gráfica.*

## 🔧 Instalación y Uso (Para Desarrolladores)

Si deseas clonar y probar este proyecto localmente:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/netobunobi/taxis-zorro-manager.git](https://github.com/netobunobi/taxis-zorro-manager.git)
    cd taxis-zorro-manager
    ```

2.  **Crear entorno virtual (Recomendado):**
    ```bash
    python -m venv venv
    # En Windows:
    venv\Scripts\activate
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install PyQt6 matplotlib reportlab
    ```

4.  **Inicializar Base de Datos:**
    ```bash
    python crear_bd.py
    ```

5.  **Ejecutar la aplicación:**
    ```bash
    python main.py
    ```

## 🛡️ Licencia

Este proyecto es privado y propietario para uso exclusivo de **Taxis El Zorro**. Todos los derechos reservados.

---
<div align="center">
    <sub>Desarrollado con dedicación y Python por Ernesto Velez Ortega</sub>
</div>
