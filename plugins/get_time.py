"""
plugins/get_time.py — Plugin para obtener la hora y fecha
"""

from datetime import datetime

intent_name = "get_time"

def execute(params, context=None, memory=None):
    now = datetime.now()
    text = f"Son las {now.strftime('%I:%M %p')} de hoy {now.strftime('%A %d de %B')}"
    return ("time", text, None)
