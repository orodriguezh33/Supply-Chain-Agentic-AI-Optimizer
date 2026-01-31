import os

import google.generativeai as genai
from dotenv import load_dotenv

# Cargar entorno
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ No hay API Key.")
else:
    # Configurar Google
    genai.configure(api_key=api_key)

    print("🔍 Consultando modelos disponibles para tu API Key...")
    try:
        # Listar todos los modelos
        for m in genai.list_models():
            # Filtramos solo los que sirven para generar texto (chat)
            if "generateContent" in m.supported_generation_methods:
                print(f"✅ Disponible: {m.name}")
    except Exception as e:
        print(f"❌ Error conectando: {e}")
