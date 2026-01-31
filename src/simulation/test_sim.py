# from src.simulation.agent_baseline import RuleBasedAgent  <-- COMENTA ESTO
from src.agents.llm_agent import SupplyChainLLMAgent  # <-- AGREGA ESTO
from src.simulation.environment import SupplyChainEnvironment


def test_simulation_with_agent():
    env = SupplyChainEnvironment(start_date="2023-01-01", end_date="2023-01-15")

    # Cambiamos el agente tonto por el inteligente
    agent = SupplyChainLLMAgent()

    print("🌍 Mundo creado. Iniciando simulación con CEREBRO GEMINI...")

    done = False
    day = 1

    # 2. Bucle de Juego
    while not done:
        # A. El entorno nos da la foto del día (OBSERVACIÓN)
        observation, done = env.step()

        if not done:
            # Imprimir estado actual de TAB-012
            stock = observation["inventory"]["TAB-012"]["on_hand"]
            print(f"📅 Día {day}: Stock TAB-012 = {stock}")

            # B. El agente piensa y decide (DECISIÓN)
            actions = agent.decide(observation)

            # C. El entorno ejecuta la decisión (ACCIÓN)
            if actions:
                env.apply_actions(actions)

            day += 1


if __name__ == "__main__":
    test_simulation_with_agent()
