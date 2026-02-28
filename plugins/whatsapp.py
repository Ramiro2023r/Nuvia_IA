"""
plugins/whatsapp.py — Plugin para enviar mensajes de WhatsApp
"""

from system.whatsapp import send_whatsapp

intent_name = "send_whatsapp"

def execute(params, context=None, memory=None):
    number = params.get("number", "")
    message = params.get("message", "")
    
    if send_whatsapp(number, message):
        return ("system", "Abriendo WhatsApp para enviar tu mensaje.", None)
    return ("system", "Lo siento, no pude preparar el mensaje de WhatsApp.", None)
