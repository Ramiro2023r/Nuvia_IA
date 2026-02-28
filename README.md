# Nuvia IA — Desktop Assistant ☁️✨

Nuvia es una asistente virtual avanzada para Windows con una interfaz minimalista, transparente y "siempre escuchando". Está diseñada para ser una compañera de escritorio que responde de forma natural sin necesidad de palabras de activación.

## 🚀 Características Principales

- **Escucha Continua**: Nuvia procesa tus comandos directamente. No necesitas decir "Nuevi" ni una wake-word. Solo habla y ella te escuchará.
- **Interfaz Kawaii Pro**: Una nube flotante transparente que se integra perfectamente en Windows (vía Tkinter + PIL).
- **Animaciones Inteligentes**:
  - **Mouth Sync**: La boca se mueve de forma sutil y real sincronizada con el audio.
  - **Blink & Float**: Parpadeo automático y movimiento de flotación senoidal.
  - **Sparkles**: Partículas dinámicas de colores que añaden vida a la nube.
- **Detección de Contexto**: Analiza la ventana activa y lo que estás haciendo para dar respuestas más precisas.
- **Integración con Gemini**: Utiliza la potencia de los modelos de Google para razonar y generar respuestas.

## 📁 Estructura del Proyecto

- `main.py`: Punto de entrada y saludo inicial sincronizado.
- `core/orchestrator.py`: El "cerebro" que coordina visión, voz y lógica.
- `ui/nube.py`: Motor gráfico de la nube y gestión de transparencia real.
- `voice/listen.py`: Listener persistente configurado para escucha continua.
- `voice/speak.py`: Motor TTS con hilos y cola de prioridad.
- `plugins/`: Acciones locales (abrir apps, buscar archivos, etc.).

## 🛠️ Requisitos e Instalación

1. Tener Python 3.10+ instalado.
2. Instalar dependencias: `pip install -r requirements.txt`.
3. Configurar tu `.env` con la API key de Gemini.
4. Ejecutar: `python main.py`.

## 🎮 Interacción

- **Hablar**: Simplemente di lo que necesites después de que ella se presente.
- **Mover**: Haz clic izquierdo y arrastra la nube a cualquier posición.
- **Estados**:
  - 🔵 **Azul**: Escuchando.
  - 🟣 **Violeta**: Pensando.
  - 🟠 **Naranja**: Hablando (Animación de boca activa).
