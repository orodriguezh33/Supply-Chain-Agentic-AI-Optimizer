from src.utils.db import SupplyChainDB


class AgentTools:
    def __init__(self):
        self.db = SupplyChainDB()

    def get_product_info(self, product_id):
        """Devuelve el precio, costo y proveedor de un producto."""
        q = f"SELECT * FROM products WHERE product_id = '{product_id}'"
        return self.db.query(q).to_dict(orient="records")[0]

    def get_supplier_info(self):
        """Devuelve la lista de proveedores con sus tiempos de entrega."""
        return self.db.query("SELECT * FROM suppliers").to_dict(orient="records")

    def calculate_reorder_qty(self, product_id, current_stock):
        """
        Calcula cuánto pedir usando una fórmula básica (EOQ simplificado).
        Esto ayuda al LLM a no tener que hacer matemáticas complejas.
        """
        # Por ahora, una lógica simple mejorada
        info = self.get_product_info(product_id)
        target = info["base_demand_daily"] * 30  # Objetivo: 30 días de stock
        qty_needed = target - current_stock
        return max(50, int(qty_needed))  # Mínimo pedir 50 (MOQ)
