# Nuvia_IA
NuviaIA es un asistente virtual de escritorio con estilo kawaii que flota como una nube en Windows gracias a Tkinter. Incluye animaciones realistas, boca sincronizada con la voz, partículas de humo, efectos de brillo y sparkles, y escucha continua sin wake-word, siendo totalmente interactivo y escalable.

NuviaIA ☁️

![Uploading image.png…]()


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

🔗 Autor

Creado por L9TDeveloper.

