class RuleBasedAgent:
    def __init__(self):
        """
        Un agente simple que sigue reglas fijas (IF/ELSE).
        Este es nuestro 'Baseline' vivo.
        """
        pass

    def decide(self, observation):
        """
        Recibe la 'foto' del juego (observation) y decide qué hacer.

        Input: observation (diccionario con fecha, inventario, etc.)
        Output: lista de acciones (órdenes de compra)
        """
        current_inventory = observation["inventory"]
        actions = []

        # Vamos a revisar producto por producto
        for product_id, data in current_inventory.items():
            stock_actual = data["on_hand"]
            stock_en_camino = data["on_order"]

            # --- AQUÍ ESTÁ LA LÓGICA (EL CEREBRO SIMPLE) ---
            # Regla: Si tengo menos de 70 unidades y no he pedido nada...
            if stock_actual < 70 and stock_en_camino == 0:
                print(
                    f"🤖 AGENTE: ¡Alerta! Stock bajo en {product_id} ({stock_actual}). ¡Comprando!"
                )

                # Generamos una orden de compra (Action)
                order = {
                    "product_id": product_id,
                    "quantity": 50,  # Pedimos 50 unidades
                    "supplier_id": "SUP-B",  # Proveedor rápido por defecto
                }
                actions.append(order)

        return actions
