from ai.classifier import classify_intent
from system.commands import execute_intent

def test_nuvia():
    test_cases = [
        "Nuvia abre WhatsApp",
        "Genera una imagen de un gato astronauta",
        "¿Qué hora es?",
        "¿Quién es Lionel Messi?",
        "Hola Nuvia, ¿cómo estás?",
        "Apaga la computadora"
    ]
    
    print("\n--- TEST DE CLASIFICACIÓN DE INTENCIONES ---")
    for text in test_cases:
        print(f"\nEntrada: '{text}'")
        intent_data = classify_intent(text)
        print(f"IA Clasificó: {intent_data}")
        action, resp, extra = execute_intent(intent_data)
        print(f"Nuvia Ejecutará: Accion={action}, Respuesta='{resp}', Extra='{extra}'")

if __name__ == "__main__":
    test_nuvia()
