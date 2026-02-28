"""
ai/model_manager.py — Gestor central de modelos de IA (Singleton).
Maneja cifrado de llaves, persistencia en .env y cambio de motores.
"""

import os
import base64
import logging
import threading
from typing import List, Dict, Generator, Optional
from dotenv import load_dotenv, set_key
from .providers import (
    GeminiProvider, OpenAIProvider, GrokProvider, 
    GroqProvider, OllamaProvider, BaseProvider
)

logger = logging.getLogger("ModelManager")

class ModelManager:
    _instance = None
    _instance_lock = threading.Lock()
    _SALT = "NUVIA_SECURE_2026"

    def __init__(self):
        self.active_model_name = "none"
        self.active_variant = "none"
        self.provider: Optional[BaseProvider] = None
        self.lock = threading.Lock()
        self.env_path = os.path.join(os.getcwd(), ".env")
        self.load_from_env()

    @classmethod
    def instance(cls):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    # ── Cifrado Simple (Obfuscación) ──────────────────────────────────────────
    def _encrypt(self, text: str) -> str:
        if not text: return ""
        combined = f"{text}{self._SALT}"
        return base64.b64encode(combined.encode()).decode()

    def _decrypt(self, encrypted: str) -> str:
        if not encrypted: return ""
        try:
            decoded = base64.b64decode(encrypted.encode()).decode()
            if decoded.endswith(self._SALT):
                return decoded[:-len(self._SALT)]
            return decoded
        except:
            return ""

    # ── Gestión de Modelos ────────────────────────────────────────────────────
    def set_model(self, model_name: str, api_key: str = None, variant: str = None) -> (bool, str):
        """
        Cambia el modelo activo y lo inicializa.
        Si api_key es None, intenta cargarla del .env.
        """
        model_name = model_name.lower()
        with self.lock:
            # 1. Obtener API Key si no se provee
            if not api_key and model_name != "ollama" and model_name != "none":
                api_key = self.get_key_from_env(model_name)
                if not api_key:
                    return False, f"No hay API Key configurada para {model_name}."

            try:
                new_provider = None
                if model_name == "gemini":
                    v = variant or "gemini-flash-latest"
                    new_provider = GeminiProvider(api_key, variant=v)
                elif model_name == "openai" or model_name == "gpt":
                    v = variant or "gpt-4o-mini"
                    new_provider = OpenAIProvider(api_key, variant=v)
                elif model_name == "grok":
                    v = variant or "grok-2"
                    new_provider = GrokProvider(api_key, variant=v)
                elif model_name == "groq":
                    v = variant or "llama-3.3-70b-versatile"
                    new_provider = GroqProvider(api_key, variant=v)
                elif model_name == "ollama":
                    v = variant or "phi3:mini"
                    new_provider = OllamaProvider(variant=v)
                elif model_name == "none":
                    self.active_model_name = "none"
                    self.provider = None
                    self.save_to_env()
                    return True, "Desconectado de IA."

                if new_provider:
                    # Guardar la llave SIEMPRE que se provea explícitamente, para que quede "registrada"
                    if api_key:
                        self.save_key_to_env(model_name, api_key)
                    
                    success, msg = new_provider.test_connection()
                    if success:
                        self.provider = new_provider
                        self.active_model_name = model_name
                        self.active_variant = variant or "auto"
                        self.save_to_env()
                        return True, f"Conectado a {model_name} exitosamente."
                    else:
                        # Si falló la conexión pero tenemos la llave guardada, 
                        # el manager al menos "conoce" el modelo activo para el siguiente reinicio
                        self.active_model_name = model_name
                        self.save_to_env()
                        return False, f"Error de validación: {msg}"
                
                return False, f"Modelo {model_name} no soportado."

            except Exception as e:
                logger.error(f"Error conectando {model_name}: {e}")
                return False, f"Excepción al conectar: {str(e)}"

    # ── Ask Interface ─────────────────────────────────────────────────────────
    def ask(self, prompt: str, history: List[Dict[str, str]] = None) -> str:
        if not self.provider:
            return "No tengo ningún modelo de IA conectado. Di 'conectar IA' o abre el chat para configurar uno."
        return self.provider.ask(prompt, history)

    def stream_ask(self, prompt: str, history: List[Dict[str, str]] = None) -> Generator[str, None, None]:
        if not self.provider:
            yield "No tengo ningún modelo de IA conectado. Por favor, realiza la configuración en el panel de chat."
            return
        yield from self.provider.stream_ask(prompt, history)

    # ── Persistencia ──────────────────────────────────────────────────────────
    def save_key_to_env(self, model: str, key: str):
        # 1. Guardar la versión cifrada
        env_var_enc = f"{model.upper()}_API_KEY_ENC"
        set_key(self.env_path, env_var_enc, self._encrypt(key))
        
        # 2. Limpiar la versión en texto plano si existe para evitar conflictos
        env_var_plain = f"{model.upper()}_API_KEY"
        if os.getenv(env_var_plain):
            set_key(self.env_path, env_var_plain, "") # Vaciar en .env
            if env_var_plain in os.environ:
                del os.environ[env_var_plain] # Quitar de memoria

    def delete_key(self, model: str):
        """Elimina la llave del modelo (tanto cifrada como plana)."""
        vars_to_clear = [f"{model.upper()}_API_KEY_ENC", f"{model.upper()}_API_KEY"]
        for var in vars_to_clear:
            set_key(self.env_path, var, "")
            if var in os.environ:
                del os.environ[var]
        logger.info(f"Llave de {model} eliminada de .env")

    def get_key_from_env(self, model: str) -> str:
        # 1. Intentar con la versión cifrada (Nuvia Standard)
        env_var_enc = f"{model.upper()}_API_KEY_ENC"
        encrypted = os.getenv(env_var_enc)
        if encrypted:
            return self._decrypt(encrypted)
            
        # 2. Fallback a texto plano (Manual / Legacy)
        env_var_plain = f"{model.upper()}_API_KEY"
        plain = os.getenv(env_var_plain)
        if plain:
            logger.info(f"Usando llave en texto plano detectada para {model}")
            return plain
            
        return ""

    def save_to_env(self):
        set_key(self.env_path, "ACTIVE_MODEL", self.active_model_name)
        set_key(self.env_path, "ACTIVE_MODEL_VARIANT", self.active_variant)

    def load_from_env(self):
        load_dotenv(override=True)
        self.active_model_name = os.getenv("ACTIVE_MODEL", "none")
        self.active_variant = os.getenv("ACTIVE_MODEL_VARIANT", "none")
        
        if self.active_model_name != "none":
            # Re-conectar silenciosamente al inicio
            # Usamos un hilo para no bloquear si tarda
            import threading
            threading.Thread(target=self.set_model, args=(self.active_model_name,), daemon=True).start()

    def is_connected(self) -> bool:
        return self.provider is not None
