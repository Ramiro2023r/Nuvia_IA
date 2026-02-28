"""
voice/voice_resolver.py — Resolución dinámica e inteligente de voces Edge TTS.

Implementa 3 capas de resolución:
  CAPA 1: Mapa base de voces conocidas (instantáneo, sin red)
  CAPA 2: Búsqueda dinámica en edge_tts.list_voices() con matching inteligente
  CAPA 3: LLM (Ollama) como fallback para interpretar peticiones ambiguas
"""

import logging
import time
import asyncio
import unicodedata

logger = logging.getLogger("NuviaVoiceResolver")

# ══════════════════════════════════════════════════════════════════════════════
# NORMALIZACIÓN DE TEXTO
# ══════════════════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    """Quita tildes, convierte a minúsculas y limpia espacios."""
    text = text.lower().strip()
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


# ══════════════════════════════════════════════════════════════════════════════
# CAPA 1: MAPA BASE DE VOCES CONOCIDAS
# ══════════════════════════════════════════════════════════════════════════════

_BASE_MAP = {
    # ═══ ESPAÑOL — PERÚ ═══
    "peruano":    "es-PE-AlexNeural",
    "peruana":    "es-PE-CamilaNeural",
    "peru":       "es-PE-AlexNeural",

    # ═══ ESPAÑOL — ARGENTINA ═══
    "argentino":  "es-AR-TomasNeural",
    "argentina":  "es-AR-ElenaNeural",
    "porteno":    "es-AR-TomasNeural",
    "portena":    "es-AR-ElenaNeural",

    # ═══ ESPAÑOL — COLOMBIA ═══
    "colombiano": "es-CO-GonzaloNeural",
    "colombiana": "es-CO-SalomeNeural",
    "colombia":   "es-CO-GonzaloNeural",

    # ═══ ESPAÑOL — CHILE ═══
    "chileno":    "es-CL-LorenzoNeural",
    "chilena":    "es-CL-CatalinaNeural",
    "chile":      "es-CL-LorenzoNeural",

    # ═══ ESPAÑOL — MÉXICO ═══
    "mexicano":   "es-MX-JorgeNeural",
    "mexicana":   "es-MX-DaliaNeural",
    "mexico":     "es-MX-JorgeNeural",

    # ═══ ESPAÑOL — ESPAÑA ═══
    "espanol":    "es-ES-AlvaroNeural",
    "espanola":   "es-ES-ElviraNeural",
    "espana":     "es-ES-AlvaroNeural",
    "castellano": "es-ES-AlvaroNeural",
    "castellana": "es-ES-ElviraNeural",

    # ═══ ESPAÑOL — VENEZUELA ═══
    "venezolano": "es-VE-SebastianNeural",
    "venezolana": "es-VE-PaolaNeural",
    "venezuela":  "es-VE-SebastianNeural",

    # ═══ ESPAÑOL — CUBA ═══
    "cubano":     "es-CU-ManuelNeural",
    "cubana":     "es-CU-BelkysNeural",
    "cuba":       "es-CU-ManuelNeural",

    # ═══ ESPAÑOL — BOLIVIA ═══
    "boliviano":  "es-BO-MarceloNeural",
    "boliviana":  "es-BO-SofiaNeural",
    "bolivia":    "es-BO-MarceloNeural",

    # ═══ ESPAÑOL — URUGUAY ═══
    "uruguayo":   "es-UY-MateoNeural",
    "uruguaya":   "es-UY-ValentinaNeural",
    "uruguay":    "es-UY-MateoNeural",

    # ═══ ESPAÑOL — ECUADOR ═══
    "ecuatoriano": "es-EC-LuisNeural",
    "ecuatoriana": "es-EC-AndreaNeural",
    "ecuador":     "es-EC-LuisNeural",

    # ═══ ESPAÑOL — PARAGUAY ═══
    "paraguayo":  "es-PY-MarioNeural",
    "paraguaya":  "es-PY-TaniaNeural",
    "paraguay":   "es-PY-MarioNeural",

    # ═══ ESPAÑOL — REP. DOMINICANA ═══
    "dominicano":  "es-DO-EmilioNeural",
    "dominicana":  "es-DO-RamonaNeural",
    "dominicano":  "es-DO-EmilioNeural",

    # ═══ ESPAÑOL — HONDURAS ═══
    "hondureno":   "es-HN-CarlosNeural",
    "hondurena":   "es-HN-KarlaNeural",
    "honduras":    "es-HN-CarlosNeural",

    # ═══ ESPAÑOL — COSTA RICA ═══
    "costarricense": "es-CR-JuanNeural",
    "costa rica":    "es-CR-JuanNeural",

    # ═══ ESPAÑOL — PANAMÁ ═══
    "panameno":    "es-PA-RobertoNeural",
    "panamena":    "es-PA-MargaritaNeural",
    "panama":      "es-PA-RobertoNeural",

    # ═══ ESPAÑOL — GUATEMALA ═══
    "guatemalteco": "es-GT-AndresNeural",
    "guatemalteca": "es-GT-MartaNeural",
    "guatemala":    "es-GT-AndresNeural",

    # ═══ ESPAÑOL — EL SALVADOR ═══
    "salvadoreno":  "es-SV-RodrigoNeural",
    "salvadorena":  "es-SV-LorenaNeural",
    "el salvador":  "es-SV-RodrigoNeural",

    # ═══ ESPAÑOL — NICARAGUA ═══
    "nicaraguense": "es-NI-FedericoNeural",
    "nicaragua":    "es-NI-FedericoNeural",

    # ═══ ESPAÑOL — PUERTO RICO ═══
    "puertorriqueno": "es-PR-VictorNeural",
    "puertorriquena": "es-PR-KarinaNeural",
    "puerto rico":    "es-PR-VictorNeural",

    # ═══ INGLÉS ═══
    "ingles":       "en-US-GuyNeural",
    "english":      "en-US-GuyNeural",
    "americano":    "en-US-GuyNeural",
    "americana":    "en-US-JennyNeural",
    "estadounidense": "en-US-GuyNeural",
    "britanico":    "en-GB-RyanNeural",
    "britanica":    "en-GB-SoniaNeural",
    "londres":      "en-GB-RyanNeural",
    "australiano":  "en-AU-WilliamNeural",
    "australiana":  "en-AU-NatashaNeural",
    "australia":    "en-AU-WilliamNeural",
    "irlandes":     "en-IE-ConnorNeural",
    "irlandesa":    "en-IE-EmilyNeural",
    "irlanda":      "en-IE-ConnorNeural",
    "indio":        "en-IN-PrabhatNeural",
    "india":        "en-IN-NeerjaNeural",
    "canadiense":   "en-CA-LiamNeural",
    "canada":       "en-CA-LiamNeural",

    # ═══ FRANCÉS ═══
    "frances":    "fr-FR-HenriNeural",
    "francesa":   "fr-FR-DeniseNeural",
    "francia":    "fr-FR-HenriNeural",

    # ═══ ALEMÁN ═══
    "aleman":     "de-DE-ConradNeural",
    "alemana":    "de-DE-KatjaNeural",
    "alemania":   "de-DE-ConradNeural",

    # ═══ ITALIANO ═══
    "italiano":   "it-IT-DiegoNeural",
    "italiana":   "it-IT-ElsaNeural",
    "italia":     "it-IT-DiegoNeural",

    # ═══ PORTUGUÉS ═══
    "portugues":  "pt-PT-DuarteNeural",
    "portuguesa": "pt-PT-RaquelNeural",
    "portugal":   "pt-PT-DuarteNeural",
    "brasileno":  "pt-BR-AntonioNeural",
    "brasilena":  "pt-BR-FranciscaNeural",
    "brasil":     "pt-BR-AntonioNeural",

    # ═══ JAPONÉS ═══
    "japones":    "ja-JP-KeitaNeural",
    "japonesa":   "ja-JP-NanamiNeural",
    "japon":      "ja-JP-KeitaNeural",

    # ═══ CHINO ═══
    "chino":      "zh-CN-YunxiNeural",
    "china":      "zh-CN-XiaoxiaoNeural",
    "mandarin":   "zh-CN-YunxiNeural",

    # ═══ COREANO ═══
    "coreano":    "ko-KR-InJoonNeural",
    "coreana":    "ko-KR-SunHiNeural",
    "corea":      "ko-KR-InJoonNeural",

    # ═══ ÁRABE ═══
    "arabe":      "ar-SA-HamedNeural",
    "arabia":     "ar-SA-HamedNeural",

    # ═══ RUSO ═══
    "ruso":       "ru-RU-DmitryNeural",
    "rusa":       "ru-RU-SvetlanaNeural",
    "rusia":      "ru-RU-DmitryNeural",

    # ═══ TURCO ═══
    "turco":      "tr-TR-AhmetNeural",
    "turca":      "tr-TR-EmelNeural",
    "turquia":    "tr-TR-AhmetNeural",

    # ═══ HOLANDÉS ═══
    "holandes":   "nl-NL-MaartenNeural",
    "holandesa":  "nl-NL-ColetteNeural",
    "holanda":    "nl-NL-MaartenNeural",

    # ═══ HINDI ═══
    "hindi":      "hi-IN-MadhurNeural",

    # ═══ POLACO ═══
    "polaco":     "pl-PL-MarekNeural",
    "polaca":     "pl-PL-ZofiaNeural",
    "polonia":    "pl-PL-MarekNeural",

    # ═══ SUECO ═══
    "sueco":      "sv-SE-MattiasNeural",
    "sueca":      "sv-SE-SofieNeural",
    "suecia":     "sv-SE-MattiasNeural",

    # ═══ NORUEGO ═══
    "noruego":    "nb-NO-FinnNeural",
    "noruega":    "nb-NO-PernilleNeural",

    # ═══ DANÉS ═══
    "danes":      "da-DK-JeppeNeural",
    "danesa":     "da-DK-ChristelNeural",
    "dinamarca":  "da-DK-JeppeNeural",

    # ═══ GRIEGO ═══
    "griego":     "el-GR-NestorasNeural",
    "griega":     "el-GR-AthinaNeural",
    "grecia":     "el-GR-NestorasNeural",

    # ═══ HEBREO ═══
    "hebreo":     "he-IL-AvriNeural",
    "hebrea":     "he-IL-HilaNeural",
    "israel":     "he-IL-AvriNeural",

    # ═══ TAILANDÉS ═══
    "tailandes":  "th-TH-NiwatNeural",
    "tailandesa": "th-TH-PremwadeeNeural",
    "tailandia":  "th-TH-NiwatNeural",

    # ═══ VIETNAMITA ═══
    "vietnamita": "vi-VN-NamMinhNeural",
    "vietnam":    "vi-VN-NamMinhNeural",

    # ═══ INDONESIO ═══
    "indonesio":  "id-ID-ArdiNeural",
    "indonesia":  "id-ID-ArdiNeural",

    # ═══ UCRANIANO ═══
    "ucraniano":  "uk-UA-OstapNeural",
    "ucraniana":  "uk-UA-PolinaNeural",
    "ucrania":    "uk-UA-OstapNeural",

    # ═══ RUMANO ═══
    "rumano":     "ro-RO-EmilNeural",
    "rumana":     "ro-RO-AlinaNeural",
    "rumania":    "ro-RO-EmilNeural",

    # ═══ CHECO ═══
    "checo":      "cs-CZ-AntoninNeural",
    "checa":      "cs-CZ-VlastaNeural",

    # ═══ HÚNGARO ═══
    "hungaro":    "hu-HU-TamasNeural",
    "hungara":    "hu-HU-NoemiNeural",
    "hungria":    "hu-HU-TamasNeural",

    # ═══ FINLANDÉS ═══
    "finlandes":  "fi-FI-HarriNeural",
    "finlandesa": "fi-FI-NooraNeural",
    "finlandia":  "fi-FI-HarriNeural",

    # ═══ CATALÁN ═══
    "catalan":    "ca-ES-EnricNeural",
    "catalana":   "ca-ES-JoanaNeural",

    # ═══ GÉNERO / EDAD (default español peruano) ═══
    "masculino":  "es-PE-AlexNeural",
    "femenino":   "es-PE-CamilaNeural",
    "hombre":     "es-PE-AlexNeural",
    "mujer":      "es-PE-CamilaNeural",
    "nino":       "es-MX-JorgeNeural",
    "nina":       "es-MX-DaliaNeural",
    "joven":      "es-MX-JorgeNeural",

    # ═══ RESET / DEFAULT ═══
    "normal":     "es-PE-AlexNeural",
    "default":    "es-PE-AlexNeural",
    "original":   "es-PE-AlexNeural",
    "resetear":   "es-PE-AlexNeural",
    "por defecto": "es-PE-AlexNeural",
}


# ══════════════════════════════════════════════════════════════════════════════
# MAPA DE KEYWORDS A LOCALES (para Capa 2)
# ══════════════════════════════════════════════════════════════════════════════

_KEYWORD_TO_LOCALE = {
    "espanol": "es", "spanish": "es",
    "ingles": "en", "english": "en",
    "frances": "fr", "french": "fr",
    "aleman": "de", "german": "de",
    "italiano": "it", "italian": "it",
    "portugues": "pt", "portuguese": "pt",
    "japones": "ja", "japanese": "ja",
    "chino": "zh", "chinese": "zh", "mandarin": "zh",
    "coreano": "ko", "korean": "ko",
    "arabe": "ar", "arabic": "ar",
    "ruso": "ru", "russian": "ru",
    "turco": "tr", "turkish": "tr",
    "holandes": "nl", "dutch": "nl",
    "hindi": "hi",
    "polaco": "pl", "polish": "pl",
    "sueco": "sv", "swedish": "sv",
    "noruego": "nb", "norwegian": "nb",
    "danes": "da", "danish": "da",
    "griego": "el", "greek": "el",
    "hebreo": "he", "hebrew": "he",
    "tailandes": "th", "thai": "th",
    "vietnamita": "vi", "vietnamese": "vi",
    "indonesio": "id", "indonesian": "id",
    "ucraniano": "uk", "ukrainian": "uk",
    "rumano": "ro", "romanian": "ro",
    "checo": "cs", "czech": "cs",
    "hungaro": "hu", "hungarian": "hu",
    "finlandes": "fi", "finnish": "fi",
    "catalan": "ca",
    "brasileno": "pt-BR", "brasil": "pt-BR", "brazilian": "pt-BR",
}


# ══════════════════════════════════════════════════════════════════════════════
# CACHÉ DE VOCES DE EDGE TTS
# ══════════════════════════════════════════════════════════════════════════════

_voices_cache = None
_cache_timestamp = 0
_CACHE_TTL = 86400  # 24 horas


def _run_async(coro):
    """Ejecuta una coroutine de forma segura desde un contexto síncrono."""
    try:
        loop = asyncio.new_event_loop()
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _fetch_voices():
    """Obtiene todas las voces de Edge TTS con caché de 24h."""
    global _voices_cache, _cache_timestamp

    now = time.time()
    if _voices_cache and (now - _cache_timestamp) < _CACHE_TTL:
        return _voices_cache

    try:
        import edge_tts
        voices = await edge_tts.list_voices()
        _voices_cache = voices
        _cache_timestamp = now
        logger.info(f"Cache de voces actualizado: {len(voices)} voces disponibles.")
        return voices
    except Exception as e:
        logger.error(f"Error obteniendo lista de voces de Edge TTS: {e}")
        return _voices_cache or []  # Devolver cache viejo si existe


# ══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: VOICE RESOLVER
# ══════════════════════════════════════════════════════════════════════════════

class VoiceResolver:
    """Resuelve peticiones de voz del usuario a voice IDs de Edge TTS."""

    def resolve(self, user_request: str) -> dict:
        """
        Recibe lo que dijo el usuario y retorna un dict con:
          - voice_id: str | None
          - resolved_by: "base_map" | "dynamic_search" | "llm" | "none"
          - description: str (explicación legible)
          - suggestions: list[str] (alternativas si no se encontró)
        """
        original = user_request
        norm = _normalize(user_request)
        logger.info(f"Resolviendo voz para: '{original}' (normalizado: '{norm}')")

        # ── CAPA 1: Mapa Base ──
        result = self._layer1_base_map(norm)
        if result:
            logger.info(f"CAPA 1 resolvió: {result['voice_id']} ({result['description']})")
            return result

        # ── CAPA 2: Búsqueda Dinámica ──
        result = self._layer2_dynamic_search(norm)
        if result:
            logger.info(f"CAPA 2 resolvió: {result['voice_id']} ({result['description']})")
            return result

        # ── CAPA 3: LLM Fallback ──
        result = self._layer3_llm_fallback(original, norm)
        if result:
            logger.info(f"CAPA 3 resolvió: {result['voice_id']} ({result['description']})")
            return result

        # ── Sin resultado ──
        logger.warning(f"No se encontró voz para: '{original}'")
        suggestions = self._get_suggestions(norm)
        return {
            "voice_id": None,
            "resolved_by": "none",
            "description": f"No encontré una voz para '{original}'",
            "suggestions": suggestions,
        }

    # ──────────────────────────────────────────────────────────────────────
    # CAPA 1: Búsqueda directa en el mapa base
    # ──────────────────────────────────────────────────────────────────────

    def _layer1_base_map(self, norm_request: str) -> dict | None:
        """Busca coincidencia exacta o parcial en el mapa base."""
        # 1. Coincidencia exacta
        if norm_request in _BASE_MAP:
            return {
                "voice_id": _BASE_MAP[norm_request],
                "resolved_by": "base_map",
                "description": f"Coincidencia exacta: '{norm_request}'",
                "suggestions": [],
            }

        # 2. Coincidencia parcial: buscar si alguna keyword del mapa está en el request
        for keyword, voice_id in _BASE_MAP.items():
            if keyword in norm_request:
                return {
                    "voice_id": voice_id,
                    "resolved_by": "base_map",
                    "description": f"Coincidencia parcial: '{keyword}' en '{norm_request}'",
                    "suggestions": [],
                }

        return None

    # ──────────────────────────────────────────────────────────────────────
    # CAPA 2: Búsqueda dinámica en la lista completa de Edge TTS
    # ──────────────────────────────────────────────────────────────────────

    def _layer2_dynamic_search(self, norm_request: str) -> dict | None:
        """Busca en edge_tts.list_voices() con scoring inteligente."""
        try:
            voices = _run_async(_fetch_voices())
            if not voices:
                return None
        except Exception as e:
            logger.error(f"Error en búsqueda dinámica: {e}")
            return None

        # Detectar preferencia de género
        prefer_female = any(w in norm_request for w in [
            "femenina", "mujer", "femenino", "chica", "voz de mujer",
        ])
        prefer_male = any(w in norm_request for w in [
            "masculino", "hombre", "masculina", "chico", "voz de hombre",
        ])

        # Extraer posible locale del request via keywords
        target_locale = None
        for keyword, locale in _KEYWORD_TO_LOCALE.items():
            if keyword in norm_request:
                target_locale = locale
                break

        # Scoring de cada voz
        best_voice = None
        best_score = 0

        for voice in voices:
            score = 0
            locale = voice.get("Locale", "").lower()
            short_name = voice.get("ShortName", "").lower()
            gender = voice.get("Gender", "").lower()
            friendly = voice.get("FriendlyName", "").lower()
            lang = locale.split("-")[0] if "-" in locale else locale

            # Match por locale exacto
            if target_locale:
                if locale.startswith(target_locale.lower()):
                    score += 10
                elif lang == target_locale.lower().split("-")[0]:
                    score += 5

            # Match por palabras del request en el nombre amigable
            request_words = norm_request.split()
            for word in request_words:
                if len(word) > 2 and word in friendly:
                    score += 3
                if len(word) > 2 and word in locale:
                    score += 4

            # Bonus por género preferido
            if prefer_female and gender == "female":
                score += 2
            elif prefer_male and gender == "male":
                score += 2
            elif not prefer_female and not prefer_male:
                # Sin preferencia: priorizar voces femeninas (más naturales en TTS)
                if gender == "female":
                    score += 1

            if score > best_score:
                best_score = score
                best_voice = voice

        if best_voice and best_score >= 3:
            voice_id = best_voice["ShortName"]
            friendly = best_voice.get("FriendlyName", voice_id)
            return {
                "voice_id": voice_id,
                "resolved_by": "dynamic_search",
                "description": f"Búsqueda dinámica (score {best_score}): {friendly}",
                "suggestions": [],
            }

        return None

    # ──────────────────────────────────────────────────────────────────────
    # CAPA 3: LLM (Ollama local) como fallback final
    # ──────────────────────────────────────────────────────────────────────

    def _layer3_llm_fallback(self, original_request: str, norm_request: str) -> dict | None:
        """Usa Ollama para interpretar la petición y mapearla a un locale."""
        try:
            from ai.ollama_client import OllamaClient
            ollama = OllamaClient()

            prompt = (
                f"El usuario quiere que un asistente de voz cambie su voz. "
                f"Dijo: \"{original_request}\". "
                f"Responde SOLO con el código de locale de Edge TTS que mejor "
                f"coincida (formato: xx-XX, ejemplo: es-AR, en-GB, fr-FR, ja-JP). "
                f"Si no puedes determinarlo, responde UNKNOWN. "
                f"Solo el código, nada más."
            )

            response = ollama.chat_response(prompt).strip().upper()
            logger.info(f"LLM respondió locale: '{response}'")

            if response == "UNKNOWN" or len(response) < 4:
                return None

            # Limpiar respuesta (a veces el LLM agrega texto extra)
            import re
            locale_match = re.search(r'[A-Za-z]{2}-[A-Za-z]{2}', response)
            if not locale_match:
                return None

            target_locale = locale_match.group(0).lower()

            # Buscar en las voces de Edge TTS
            voices = _run_async(_fetch_voices())
            if not voices:
                return None

            for voice in voices:
                if voice.get("Locale", "").lower() == target_locale:
                    return {
                        "voice_id": voice["ShortName"],
                        "resolved_by": "llm",
                        "description": f"LLM mapeó '{original_request}' → {target_locale}",
                        "suggestions": [],
                    }

        except Exception as e:
            logger.error(f"Error en fallback LLM: {e}")

        return None

    # ──────────────────────────────────────────────────────────────────────
    # SUGERENCIAS
    # ──────────────────────────────────────────────────────────────────────

    def _get_suggestions(self, norm_request: str) -> list:
        """Genera sugerencias de voces similares al request."""
        suggestions = []
        request_words = set(norm_request.split())

        for keyword in _BASE_MAP:
            keyword_words = set(keyword.split())
            # Si comparten alguna palabra
            if request_words & keyword_words:
                suggestions.append(keyword)

        # Si no hay sugerencias por palabras, dar las más populares
        if not suggestions:
            suggestions = ["peruano", "argentino", "colombiano", "mexicano",
                           "ingles", "frances", "japones"]

        return suggestions[:5]


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES PÚBLICAS
# ══════════════════════════════════════════════════════════════════════════════

# Instancia global del resolver
_resolver = VoiceResolver()


def resolve_voice(user_request: str) -> dict:
    """Función pública para resolver una voz desde cualquier módulo."""
    return _resolver.resolve(user_request)


def get_available_voices_summary() -> str:
    """Retorna un resumen de las categorías de voces disponibles."""
    return (
        "Tengo voces en español (peruano, argentino, colombiano, chileno, mexicano, "
        "español, venezolano, cubano, boliviano, uruguayo y más), "
        "inglés (americano, británico, australiano, irlandés, indio), "
        "y muchos otros idiomas como francés, alemán, italiano, portugués, "
        "japonés, chino, coreano, árabe, ruso, turco, holandés y más. "
        "También puedo hablar con voz masculina o femenina en cualquier idioma."
    )
