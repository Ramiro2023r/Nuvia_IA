from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# Test con los IDs exactos que salieron en list_models()
models_to_test = [
    "models/gemini-1.5-flash",
    "models/gemini-flash-latest",
    "models/gemini-1.5-flash-002",
    "models/gemini-2.0-flash-lite-preview-02-05" 
]

for model_id in models_to_test:
    print(f"Testing {model_id}...")
    try:
        response = client.models.generate_content(
            model=model_id,
            contents="Hola"
        )
        print(f"SUCCESS: {model_id} works.")
        break
    except Exception as e:
        print(f"FAILED: {model_id}: {e}")
