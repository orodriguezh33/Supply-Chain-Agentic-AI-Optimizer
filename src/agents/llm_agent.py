import json
import os

from dotenv import load_dotenv

# Usamos langchain_core para evitar conflictos de versiones
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from src.agents.tools import AgentTools

# Cargar variables de entorno del archivo .env
load_dotenv()


class SupplyChainLLMAgent:
    def __init__(self):
        # --- CORRECCIÓN 1: Obtener la clave explícitamente ---
        # Esto asegura que Python lea la llave antes de llamar a Google
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            # Si no encuentra la llave, detiene el programa y avisa
            raise ValueError(
                "❌ ERROR CRÍTICO: No se encontró GOOGLE_API_KEY en el archivo .env. Asegúrate de tener el archivo creado."
            )

        # --- CORRECCIÓN 2: Pasar la llave directamente al modelo ---
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.1,
            google_api_key=api_key,  # <--- AQUÍ FORZAMOS LA CONEXIÓN
        )

        self.tools = AgentTools()

        # --- 🛡️ SEGURIDAD NIVEL 3: INTERRUPTOR DE EMERGENCIA ---
        self.call_count = 0  # Contador de llamadas realizadas
        self.max_calls = 10  # Límite DURO: El agente se apaga tras 10 llamadas

        # Definir la personalidad y reglas
        self.prompt_template = PromptTemplate(
            input_variables=["date", "inventory_data", "product_info"],
            template="""
            Eres un Gerente de Cadena de Suministro Experto IA para TechGear.
            Tu trabajo es evitar Stockouts (quedarse sin producto) y minimizar costos.

            FECHA ACTUAL: {date}
            
            SITUACIÓN DEL INVENTARIO:
            {inventory_data}

            INFORMACIÓN DEL PRODUCTO:
            {product_info}

            INSTRUCCIONES:
            1. Analiza si el stock actual ('on_hand') es bajo.
            2. REVISA SIEMPRE 'units_on_order'. Si hay pedidos en camino, ¡NO PIDAS MÁS! (Paciencia).
            3. Considera que el Lead Time es de 3 días.
            4. Si necesitas comprar, decide la cantidad.

            FORMATO DE RESPUESTA (JSON PURO):
            {{
                "reasoning": "Tu explicación breve de por qué pides o no pides",
                "decision": "ORDER" o "WAIT",
                "quantity": 50,
                "supplier_id": "SUP-B"
            }}
            """,
        )

    def decide(self, observation):
        """
        El cerebro recibe la observación, piensa y devuelve acciones.
        """
        current_inventory = observation["inventory"]
        actions = []

        # Producto objetivo (para pruebas controladas)
        target_product = "TAB-012"

        # --- 🛡️ VERIFICACIÓN DE SEGURIDAD ANTES DE CUALQUIER LÓGICA ---
        if self.call_count >= self.max_calls:
            print(
                f"🛑 SEGURIDAD ACTIVADA: Se alcanzó el límite de {self.max_calls} llamadas. El agente está en modo reposo."
            )
            return []  # Retorna lista vacía, no gasta ni un token más.

        if target_product in current_inventory:
            stock_data = current_inventory[target_product]

            # Solo consultamos al LLM si no tenemos pedidos en camino
            if stock_data["on_order"] == 0:

                # 1. Reunir datos
                product_info = self.tools.get_product_info(target_product)

                # 2. Construir prompt
                prompt = self.prompt_template.format(
                    date=observation["date"],
                    inventory_data=stock_data,
                    product_info=product_info,
                )

                # 3. ¡LLAMADA A LA IA CON CONTROL DE COSTOS!
                try:
                    # Incrementamos el contador
                    self.call_count += 1
                    print(f"💳 LLAMADA A GEMINI #{self.call_count}/{self.max_calls}...")

                    response = self.llm.invoke(prompt)

                    # 4. Limpiar respuesta (elimina markdown ```json si lo hay)
                    clean_json = (
                        response.content.replace("```json", "")
                        .replace("```", "")
                        .strip()
                    )
                    decision_data = json.loads(clean_json)

                    print(
                        f"🧠 PENSAMIENTO ({target_product}): {decision_data['reasoning']}"
                    )

                    # 5. Ejecutar decisión
                    if (
                        decision_data["decision"] == "ORDER"
                        and decision_data["quantity"] > 0
                    ):
                        order = {
                            "product_id": target_product,
                            "quantity": decision_data["quantity"],
                            "supplier_id": decision_data.get("supplier_id", "SUP-B"),
                        }
                        actions.append(order)
                        print(
                            f"✅ ORDEN GENERADA: {decision_data['quantity']} unidades"
                        )

                except Exception as e:
                    print(f"❌ Error del LLM o JSON: {e}")

        return actions
