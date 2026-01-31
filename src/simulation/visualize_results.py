import matplotlib.pyplot as plt

from src.agents.llm_agent import SupplyChainLLMAgent
from src.simulation.environment import SupplyChainEnvironment


def run_and_plot():
    # 1. Configuración
    env = SupplyChainEnvironment(
        start_date="2023-01-01", end_date="2023-01-30"
    )  # 30 días
    agent = SupplyChainLLMAgent()

    # Listas para guardar datos para el gráfico
    dates = []
    inventory_levels = []
    orders_placed = []  # (fecha, cantidad)
    shipments_received = []  # (fecha, cantidad)

    print("🎬 Rodando simulación de 30 días para generar gráfico...")

    done = False
    target_product = "TAB-012"

    while not done:
        # A. Guardar estado ANTES de actuar
        current_stock = env.current_inventory[target_product]["on_hand"]
        current_date = env.current_date

        dates.append(current_date)
        inventory_levels.append(current_stock)

        # B. Paso de simulación
        observation, done = env.step()

        if not done:
            # Detectar si llegó algo hoy (comparando con el paso anterior o logs)
            # Para simplificar, lo inferimos si el stock subió drásticamente sin ser venta
            # (Mejor: El entorno podría devolver eventos, pero lo haremos simple)
            pass

            # C. Decisión del Agente
            actions = agent.decide(observation)

            if actions:
                for action in actions:
                    if action["product_id"] == target_product:
                        qty = action["quantity"]
                        orders_placed.append((current_date, qty, current_stock))
                        env.apply_actions([action])

    # --- GENERAR GRÁFICO ---
    plt.figure(figsize=(12, 6))

    # 1. Línea de Inventario
    plt.plot(
        dates, inventory_levels, label="Nivel de Inventario", color="blue", linewidth=2
    )
    plt.axhline(y=50, color="r", linestyle="--", label="Stock de Seguridad (Critico)")

    # 2. Puntos de Pedidos (Cuando el Agente llama a Gemini)
    for date, qty, stock in orders_placed:
        plt.scatter(date, stock, color="red", s=100, zorder=5)
        plt.annotate(
            f"Pidió {qty}",
            (date, stock + 10),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            color="red",
        )

    plt.title(f"Gestión de Inventario con IA (Gemini 2.0) - {target_product}")
    plt.xlabel("Fecha")
    plt.ylabel("Unidades en Stock")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Guardar imagen
    plt.savefig("resultado_simulacion.png")
    print(
        "✅ Gráfico guardado como 'resultado_simulacion.png'. ¡Ábrelo para ver a tu IA en acción!"
    )
    plt.show()


if __name__ == "__main__":
    run_and_plot()
