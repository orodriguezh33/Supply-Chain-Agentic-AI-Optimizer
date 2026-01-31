import os

from dotenv import load_dotenv

# Intentar cargar
load_dotenv()

key = os.getenv("GOOGLE_API_KEY")

if key:
    print("✅ ¡Clave encontrada!")
    print(f"Primeros 5 caracteres: {key[:5]}...")
    print(f"Longitud total: {len(key)} caracteres")

    if key.startswith("AIza"):
        print("✅ El formato parece correcto (empieza con AIza).")
    else:
        print(
            "⚠️ CUIDADO: Las claves de Google suelen empezar con 'AIza'. Revisa si copiaste algo más."
        )
else:
    print("❌ ERROR: No se encontró la variable GOOGLE_API_KEY.")
    print("Asegúrate de tener el archivo '.env' en la misma carpeta que este script.")
