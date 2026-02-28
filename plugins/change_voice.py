"""
plugins/change_voice.py — Plugin para cambiar la voz de Nuvia dinámicamente.

Recibe la descripción del usuario, usa voice_resolver para encontrar
la voz correcta de Edge TTS, y la cambia en caliente.
Nuvia confirma el cambio hablando EN LA NUEVA VOZ.
"""

from voice.voice_resolver import resolve_voice, get_available_voices_summary
from voice.speak import change_voice, stop_speak
import logging

logger = logging.getLogger("NuviaPlugins")

intent_name = "change_voice"


def execute(params, context=None, memory=None):
    """
    Cambia la voz de Nuvia basándose en la petición del usuario.
    
    Flujo:
      1. Recibe el texto del usuario (ej: "argentino", "japonés", "voz femenina")
      2. Llama a voice_resolver.resolve_voice() para encontrar el voice_id
      3. Cambia la voz en el Speaker
      4. Retorna confirmación (se hablará EN LA NUEVA VOZ automáticamente)
    """
    voice_request = params.get("voice_request", "").strip()

    if not voice_request:
        summary = get_available_voices_summary()
        return ("system", f"¿A qué voz quieres que cambie? {summary}", None)

    logger.info(f"Solicitud de cambio de voz: '{voice_request}'")

    # Resolver la voz usando las 3 capas
    result = resolve_voice(voice_request)
    voice_id = result.get("voice_id")
    resolved_by = result.get("resolved_by", "none")
    description = result.get("description", "")

    if voice_id:
        # Detener cualquier habla actual antes de cambiar
        stop_speak()

        # Cambiar la voz ANTES de responder (así la confirmación usa la nueva voz)
        change_voice(voice_id)

        logger.info(f"Voz cambiada exitosamente a '{voice_id}' (resuelta por: {resolved_by})")

        # Mensaje de confirmación contextual
        if resolved_by == "base_map":
            response = f"¡Listo! He cambiado mi voz. Ahora hablo con esta voz. ¿Qué te parece?"
        elif resolved_by == "dynamic_search":
            response = f"Encontré esta voz para ti. ¿Suena bien?"
        else:  # llm
            response = f"Creo que esta es la voz que buscas. ¿Te gusta?"

        return ("system", response, {"voice_id": voice_id, "resolved_by": resolved_by})

    else:
        # No se encontró la voz - sugerir alternativas
        suggestions = result.get("suggestions", [])
        if suggestions:
            sugg_text = ", ".join(suggestions[:5])
            response = (
                f"No encontré una voz exacta para '{voice_request}'. "
                f"Pero puedo hablar como: {sugg_text}. "
                f"¿Cuál prefieres?"
            )
        else:
            response = (
                f"No encontré una voz para '{voice_request}'. "
                f"Puedo hablar en muchos idiomas y acentos. "
                f"Prueba con algo como 'argentino', 'japonés', o 'voz femenina'."
            )

        return ("system", response, None)
