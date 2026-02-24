"""
plugins/suggest_context.py — Plugin para generar sugerencias expertas basadas en el entorno
"""

intent_name = "suggest_context"

def execute(params, context=None, memory=None):
    if not context or not context.get("has_screenshot"):
        return ("system", "Lo siento, no tengo suficiente información visual de tu pantalla ahora mismo para darte sugerencias.", None)
    
    from context.analyzer import ContextAnalyzer
    analyzer = ContextAnalyzer()
    
    # Generar sugerencias usando la visión (Gemini Multimodal internamente)
    suggestions_data = analyzer.generate_context_suggestions(context, context.get("screenshot_path"))
    
    mode = suggestions_data.get("mode", "Asistente")
    text = suggestions_data.get("suggestions", "No tengo sugerencias claras ahora mismo.")
    actions = suggestions_data.get("priority_actions", [])
    
    res_text = f"Modo {mode}: {text}"
    if actions:
        res_text += f"\nAcciones recomendadas: {', '.join(actions)}."
        
    return ("system", res_text, suggestions_data)
