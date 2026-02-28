# Nuvia_IA
NuviaIA es un asistente virtual de escritorio con estilo kawaii que flota como una nube en Windows gracias a Tkinter. Incluye animaciones realistas, boca sincronizada con la voz, partículas de humo, efectos de brillo y sparkles, y escucha continua sin wake-word, siendo totalmente interactivo y escalable.

NuviaIA ☁️



<img width="397" height="658" alt="image" src="https://github.com/user-attachments/assets/f7cf93b4-c376-4bac-add2-0438130fba55" />

<img width="343" height="618" alt="image" src="https://github.com/user-attachments/assets/d2453a64-60a0-4dee-bca3-b4526d33dee2" />



Descripción:
NuviaIA es un asistente virtual de escritorio con estilo kawaii, que flota como una nube sobre Windows gracias a una GUI nativa desarrollada en Tkinter. Ofrece animaciones realistas, boca sincronizada con la voz, partículas de humo, efectos visuales de brillo y sparkles, y escucha continua sin necesidad de wake-word. Su diseño está inspirado en la estética “Kawaii Pro” y está pensado para ser escalable y totalmente interactivo.

🌟 Características

GUI transparente en Windows: la nube flota sobre el escritorio sin bordes molestos usando wm_attributes("-transparentcolor", "#FF00FF").

Animaciones avanzadas: parpadeo automático, flotación senoidal, boca que se mueve al hablar.

Renderizado de alta fidelidad con PIL: gradientes, bumps kawaii, ojos, mejillas rosadas, sparkles y glow violeta.

Escucha continua: sin wake-word, completamente conversacional.

Integración con lógica de IA: la API mantiene métodos como set_state y start_mouth, garantizando compatibilidad.

Arrastrable: se puede mover a cualquier lugar de la pantalla haciendo clic y arrastrando.

🛠️ Instalación

Clona este repositorio:

git clone https://github.com/tu-usuario/NuviaIA.git
cd NuviaIA

Instala dependencias:

pip install -r requirements.txt

Ejecuta la aplicación:

python main.py

⚠️ Requiere Python 3.9+ y sistema operativo Windows para la transparencia nativa.

📂 Estructura del Proyecto
NuviaIA/
│
├─ main.py                 # Punto de entrada
├─ core/
│   └─ orchestrator.py     # Orquestador de la lógica de IA y voz
├─ ui/
│   └─ nube.py             # Clase CloudWindow con Tkinter y animaciones
├─ assets/                 # Imágenes, íconos y recursos visuales
├─ README.md
├─ IMPROVEMENTS.md         # Roadmap de mejoras futuras
└─ requirements.txt
🎨 Personalización

Cambia colores, gradientes o efectos de la nube editando ui/nube.py.

Ajusta animaciones y sincronización de boca desde core/orchestrator.py.

📖 Uso

Ejecuta main.py para iniciar NuviaIA.

Haz clic y arrastra la nube para moverla por la pantalla.

Habla con NuviaIA sin necesidad de wake-word; responderá automáticamente.

🚀 Mejoras Futuras

Integración con servicios en la nube.

Soporte multi-plataforma (Linux/macOS).

Personalización de voz y expresiones.

Añadir más interacciones visuales y mini-juegos.

🌬️ Guía de Funciones y Comandos de Nuvia
Nuvia es tu asistente personal de IA, diseñada para interactuar de forma natural mediante voz y chat. A continuación, se detallan todas sus capacidades y las palabras clave que puedes usar para interactuar con ella.

🎙️ Cómo interactuar con Nuvia
Voz: Nuvia escucha de forma continua. Puedes hablarle directamente. Aunque no requiere una "palabra de activación" estricta, responderá mejor si mencionas su nombre ("Nuvia").
Chat: Puedes escribirle directamente abriendo el panel de chat.
🛠️ Funciones Principales y Palabras Clave
1. Control de Aplicaciones
Nuvia puede abrir y cerrar programas en tu sistema.

Abrir: "Abre [Programa]", "Lanza [Programa]", "Ejecuta [Programa]".
Cerrar: "Cierra [Programa]", "Termina [Programa]", "Quita [Programa]".
2. Mensajería (WhatsApp)
Puedes enviar mensajes rápidos sin tocar el teclado.

Comandos: "Manda un WhatsApp a [Número/Nombre]", "Envía un mensaje por WhatsApp".
Ejemplo: "Manda un WhatsApp a 34600112233 diciendo que llegaré tarde".
3. Personalización de Voz
Nuvia puede cambiar su forma de hablar al instante.

Voz/Personaje: "Habla como [Personaje]", "Pon voz de [Voz]".
Idioma/Acento: "Habla en [Idioma]", "Habla con acento [País]".
Otros: "Cambia tu voz", "Habla diferente".
4. Memoria e Información Personal
Nuvia recuerda detalles importantes para ti.

Guardar: "Recuerda que [Información]", "Guarda que [Información]".
Recuperar: "¿Qué sabes de [Tema]?", "¿Te acuerdas de [Tema]?".
5. Control del Sistema y Estadísticas
Monitorea y controla tu PC con la voz.

Información: "Dime las estadísticas", "¿Cómo va la CPU/RAM?", "Estado del sistema".
Acciones: "Apaga el equipo", "Reinicia la computadora", "Cancela el apagado".
Tiempo: "¿Qué hora es?", "Dime la fecha".
6. Gestión de la Interfaz (Chat)
Controla visualmente el asistente.

Mostrar: "Abre el chat", "Muestra el teclado", "Quiero escribirte".
Ocultar: "Cierra el chat", "Esconde el teclado", "Oculta el chat".
7. Seguridad e Identidad Biométrica
Registra tu voz para que Nuvia solo te obedezca a ti en acciones críticas.

Comandos: "Registra mi voz", "Graba mi voz", "¿Quién soy?", "Identidad de voz".
8. Conversación General e IA
Pregúntale cualquier cosa, pide consejos o simplemente charlen.

Ejemplos: "¿Qué me recomiendas cenar hoy?", "Cuéntame un chiste", "¿Qué es la teoría de la relatividad?".
💡 Consejos para una mejor experiencia
Habla Natural: No necesitas comandos robóticos, Nuvia entiende el lenguaje natural.
Contexto: Nuvia sabe qué ventana tienes abierta. Si le dices "Explícame esto", analizará lo que estás viendo para ayudarte.
Seguridad: Algunas acciones (como apagar el PC) requieren que hayas registrado tu voz previamente.



🔗 Autor

Creado por L9TDeveloper.

