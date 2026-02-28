"""
core/security_layer.py — Gestiona permisos y acciones críticas para NuviaIA
"""

import time
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configuración de Logging para Auditoría
audit_logger = logging.getLogger("SecurityAudit")
audit_logger.setLevel(logging.INFO)
if not audit_logger.handlers:
    fh = logging.FileHandler("security_audit.log", encoding='utf-8')
    fh.setFormatter(logging.Formatter('%(asctime)s [AUDIT] %(message)s'))
    audit_logger.addHandler(fh)

class SecurityManager:
    """
    Controla el acceso a funciones críticas y gestiona la sesión de administrador.
    """

    def __init__(self, admin_password=None, session_timeout_minutes=5):
        # SEGURIDAD: Nunca usar 'nuvia123' como fallback. 
        # Si no hay variable de entorno, la contraseña será None y las acciones críticas fallarán.
        self.admin_password = admin_password or os.getenv("ADMIN_PASSWORD")
        
        if not self.admin_password:
            audit_logger.critical("ADMIN_PASSWORD NO CONFIGURADA EN .ENV. Acciones críticas desactivadas.")
            print("[Security] ERROR: ADMIN_PASSWORD no encontrada en .env")

        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.admin_session_active = False
        self.last_admin_activity = None
        self.pending_action = None # Estructura: {"intent": str, "params": dict}

        # Acciones que requieren confirmación obligatoria o modo admin
        self.critical_intents = [
            "shutdown", "restart", "delete_file", 
            "move_file", "open_app", "system_control",
            "INTENT_CRITICAL_SHUTDOWN"
        ]

    def is_authorized(self, intent: str, speaker_identity: str) -> bool:
        """
        Verifica si el hablante tiene permiso para ejecutar la intención.
        """
        if intent not in self.critical_intents:
            return True
            
        if speaker_identity == "OWNER":
            audit_logger.info(f"Autorización CONCEDIDA por identidad de voz: {intent}")
            return True
        
        audit_logger.warning(f"Autorización DENEGADA por identidad de voz: {intent} (Speaker: {speaker_identity})")
        return False

    def authenticate(self, password: str) -> bool:
        """Verifica la contraseña y activa la sesión de administrador."""
        if self.admin_password is not None and password == self.admin_password:
            self.admin_session_active = True
            self.last_admin_activity = datetime.now()
            audit_logger.info("Sesión de administrador INICIADA.")
            return True
        else:
            audit_logger.warning(f"Intento de autenticación FALLIDO. (Password configurada: {self.admin_password is not None})")
            return False

    def is_session_valid(self) -> bool:
        """Comprueba si la sesión de administrador sigue activa y no ha expirado."""
        if not self.admin_session_active or self.last_admin_activity is None:
            return False
        
        expired = datetime.now() - self.last_admin_activity > self.session_timeout
        if expired:
            self.logout()
            return False
        
        # Refrescar actividad si es válida
        self.last_admin_activity = datetime.now()
        return True

    def logout(self):
        """Finaliza la sesión de administrador."""
        self.admin_session_active = False
        self.last_admin_activity = None
        audit_logger.info("Sesión de administrador FINALIZADA.")

    def needs_verification(self, intent: str) -> bool:
        """Determina si un intent requiere confirmación o privilegios elevados."""
        return intent in self.critical_intents

    def set_pending_action(self, intent: str, params: dict):
        """Guarda una acción que está esperando confirmación."""
        self.pending_action = {"intent": intent, "params": params, "time": datetime.now()}
        audit_logger.info(f"Acción crítica PENDIENTE: {intent} con {params}")

    def confirm_action(self, user_confirmation: str) -> dict | None:
        """
        Procesa la confirmación del usuario.
        user_confirmation: 'si', 'confirmar', etc.
        """
        if not self.pending_action:
            return None

        # Verificar si la acción ha expirado (confirmación debe ser rápida)
        if datetime.now() - self.pending_action["time"] > timedelta(minutes=1):
            self.pending_action = None
            audit_logger.warning("Confirmación de acción EXPIRADA.")
            return None

        clean_conf = user_confirmation.lower().strip()
        if any(word in clean_conf for word in ["si", "confirmar", "procede", "adelante"]):
            action = self.pending_action
            self.pending_action = None
            audit_logger.info(f"Acción crítica CONFIRMADA y EJECUTADA: {action['intent']}")
            return action
        
        self.pending_action = None
        audit_logger.info("Acción crítica CANCELADA por el usuario.")
        return None

if __name__ == "__main__":
    # Prueba rápida
    # Configurar una temporal para la prueba si no hay .env
    os.environ["ADMIN_PASSWORD"] = "test123"
    sec = SecurityManager()
    print(f"Auth (correcta): {sec.authenticate('test123')}")
    print(f"Auth (incorrecta): {sec.authenticate('wrong')}")
    print(f"Valid: {sec.is_session_valid()}")
    sec.set_pending_action("shutdown", {})
    print(f"Confirmado: {sec.confirm_action('si')}")
