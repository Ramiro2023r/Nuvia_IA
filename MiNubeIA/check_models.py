from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY no encontrada en .env")
    exit()

client = genai.Client(api_key=api_key)

print("--- Modelos disponibles para tu API Key ---")
try:
    for model in client.models.list():
        print(f"ID: {model.name} | Display Name: {model.display_name}")
except Exception as e:
    print(f"Error al listar modelos: {e}")
