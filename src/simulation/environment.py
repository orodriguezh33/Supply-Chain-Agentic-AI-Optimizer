from datetime import timedelta

import pandas as pd

from src.utils.db import SupplyChainDB


class SupplyChainEnvironment:
    def __init__(self, start_date="2023-01-01", end_date="2023-12-31"):
        self.db = SupplyChainDB()
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.current_date = self.start_date

        self.current_inventory = {}
        # --- NUEVO: COLA DE ENVÍOS (MEMORIA DEL MUNDO) ---
        self.pending_shipments = (
            []
        )  # Lista de diccionarios: {'date': fecha_llegada, 'qty': cantidad, 'pid': producto}

        self._load_initial_inventory()

    def _load_initial_inventory(self):
        print(f"🎮 Iniciando simulación realista desde {self.start_date.date()}...")
        query = f"""
        SELECT product_id, units_on_hand, units_on_order 
        FROM inventory_snapshots 
        WHERE date = '{self.start_date.date()}'
        """
        df = self.db.query(query)
        for _, row in df.iterrows():
            self.current_inventory[row["product_id"]] = {
                "on_hand": row["units_on_hand"],
                "on_order": 0,  # Reseteamos esto porque lo calcularemos nosotros
            }

    def step(self):
        """Tic-Tac del reloj con gestión de envíos."""
        if self.current_date >= self.end_date:
            return None, True

        # 1. PROCESAR LLEGADAS (El camión descarga)
        # Revisamos si hay envíos programados para HOY (o antes)
        arrived_shipments = [
            s for s in self.pending_shipments if s["arrival_date"] <= self.current_date
        ]
        self.pending_shipments = [
            s for s in self.pending_shipments if s["arrival_date"] > self.current_date
        ]

        for shipment in arrived_shipments:
            pid = shipment["product_id"]
            qty = shipment["quantity"]

            # Magia de la contabilidad:
            # Sube el stock físico ('on_hand')
            self.current_inventory[pid]["on_hand"] += qty
            # Baja el stock en tránsito ('on_order') porque ya llegó
            self.current_inventory[pid]["on_order"] -= qty

            print(f"📦 ENTREGA RECIBIDA: {qty} unidades de {pid} ya están disponibles.")

        # 2. PROCESAR VENTAS (Clientes compran)
        sales_query = f"""
        SELECT product_id, units_sold 
        FROM sales 
        WHERE date = '{self.current_date.date()}'
        """
        daily_sales = self.db.query(sales_query)

        for _, sale in daily_sales.iterrows():
            pid = sale["product_id"]
            if pid in self.current_inventory:
                stock_actual = self.current_inventory[pid]["on_hand"]
                venta_real = min(stock_actual, sale["units_sold"])
                self.current_inventory[pid]["on_hand"] -= venta_real

        # 3. Avanzar reloj
        self.current_date += timedelta(days=1)

        return {
            "date": self.current_date.date(),
            "inventory": self.current_inventory,
        }, False

    def apply_actions(self, actions):
        """
        Ahora las acciones no son inmediatas. Tardan 3 días.
        """
        if not actions:
            return

        LEAD_TIME_DAYS = 3  # ¡El camión tarda 3 días en llegar!

        for order in actions:
            pid = order["product_id"]
            qty = order["quantity"]

            # Calculamos cuándo llegará
            arrival_date = self.current_date + timedelta(days=LEAD_TIME_DAYS)

            # 1. Registramos el envío en la cola
            shipment = {
                "arrival_date": arrival_date,
                "product_id": pid,
                "quantity": qty,
            }
            self.pending_shipments.append(shipment)

            # 2. Actualizamos 'on_order' inmediatamente
            # Esto es CRUCIAL: El Agente verá que este número sube y sabrá que la ayuda viene en camino.
            if pid in self.current_inventory:
                self.current_inventory[pid]["on_order"] += qty

            print(
                f"🚚 PEDIDO ENVIADO: {qty} unidades de {pid} llegarán el {arrival_date.date()} (En tránsito)."
            )
