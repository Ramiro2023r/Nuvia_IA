"""
system/whatsapp.py — Envío de mensajes por WhatsApp Web
"""

import webbrowser
import urllib.parse
import logging

logger = logging.getLogger("NuviaSystem")

def send_whatsapp(number: str, message: str) -> bool:
    """
    Genera un enlace wa.me y lo abre en el navegador.
    number: debe incluir código de país (ej: '34600112233')
    """
    if not number or not message:
        logger.warning("Falta número o mensaje para WhatsApp.")
        return False

    try:
        # Limpiar el número (quitar espacios, +, etc.)
        clean_number = "".join(filter(str.isdigit, number))
        
        # Codificar el mensaje para URL
        encoded_msg = urllib.parse.quote(message)
        
        # Construir enlace wa.me
        url = f"https://wa.me/{clean_number}?text={encoded_msg}"
        
        logger.info(f"Abriendo WhatsApp para el número: {clean_number}")
        webbrowser.open(url)
        return True
    except Exception as e:
        logger.error(f"Error enviando WhatsApp: {e}")
        return False

if __name__ == "__main__":
    # Prueba rápida
    # send_whatsapp("123456789", "Hola desde Nuevi")
    pass
