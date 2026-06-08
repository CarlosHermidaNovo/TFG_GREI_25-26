# Prompt para v0 by Vercel

Copia y pega el siguiente texto en v0.dev para generar el frontend de tu proyecto:

---

**Rol:** Actúa como un experto desarrollador Frontend y diseñador UX/UI especializado en dashboards de datos y visualización.

**Objetivo:** Crear una interfaz de usuario moderna y minimalista para un proyecto de **Seguridad Alimentaria y Agricultura** llamado "SOS Food". La aplicación debe ser una SPA (Single Page Application) construida con **React**, **Next.js**, **Tailwind CSS** y **Lucide React** para los iconos.

**Estilo Visual:**
*   **Minimalista**: Diseño limpio, mucho espacio en blanco, tipografía moderna (Inter o similar).
*   **Paleta de Colores**:
    *   Principal: Verdes (tonos naturaleza, seguridad, crecimiento, ej: `#16a34a`).
    *   Acento: Naranjas (tonos cálidos, alerta, energía, ej: `#f97316`).
    *   Fondo: Blanco (`#ffffff`) o gris muy claro (`#f8fafc`) para el contenido principal.
*   **Bordes**: Redondeados suaves (`rounded-lg` o `rounded-xl`).
*   **Sombras**: Sutiles para dar profundidad a las tarjetas (`shadow-sm`, `shadow-md`).

**Estructura del Layout:**
La pantalla debe dividirse en áreas principales usando Grid o Flexbox:

1.  **Sidebar / Header (Navegación)**:
    *   Logo "SOS Food" (texto estilizado o icono relacionado con comida/mundo).
    *   Menú de navegación simple (Inicio, Dashboard, Ajustes).

2.  **Área Principal (Dashboard & Chat)**:
    Esta área debe estar optimizada para visualización de datos.

    *   **A. Dashboard Fijo (Panel Superior - Integración Externa)**:
        *   Esta sección debe ser un **contenedor `iframe`** (o div placeholder) diseñado para alojar un dashboard de **Grafana** existente.
        *   Debe ocupar todo el ancho disponible y tener una altura considerable (ej: `h-[600px]`).
        *   Incluye un borde sutil y sombra para integrarlo visualmente.
        *   Usa un placeholder visual temporal (un recuadro gris con el logo de Grafana o texto "Grafana Dashboard Placeholder") para simularlo.

    *   **B. Área Interactiva (Panel Inferior - Chatbot y Visualización On-Demand)**:
        *   Dividida en dos columnas: Izquierda (Chatbot) y Derecha (Visualización Dinámica).
        
        *   **Columna Izquierda: Chatbot (40% ancho)**:
            *   Interfaz de chat moderna tipo ChatGPT.
            *   Historial de mensajes visible.
            *   Mensajes del usuario (alineados dcha, burbuja verde suave).
            *   Respuestas del bot (alineadas izq, burbuja gris/blanca).
            *   Input de texto fijo abajo con botón enviar.
            
        *   **Columna Derecha: Visualización Dinámica (60% ancho)**:
            *   Un contenedor grande ("Canvas") donde se renderizan los gráficos que el usuario pide por el chat.
            *   Por defecto: Un mensaje de bienvenida "Pídeme cualquier dato sobre seguridad alimentaria".
            *   Cuando el usuario pida en el chat "Muéstrame la evolución de la población rural", este contenedor debe actualizarse para mostrar ese gráfico específico en grande.
            *   Simula un gráfico de ejemplo al inicio o tras una interacción.

**Funcionalidad Simulada:**
*   Simula un flujo donde el usuario escribe "Hola, ¿cómo ha evolucionado la población rural?" y el bot responde mostrando un gráfico de línea descendente en el área dinámica.

**Requisitos Técnicos:**
*   Usa componentes funcionales de React (`const Dashboard = () => ...`).
*   Usa Tailwind CSS para todo el estilado (clases utilitarias).
*   Diseño Responsivo (Desktop First).
*   Código limpio y modular.
*   Prepara el `iframe` para ser responsive.

---
