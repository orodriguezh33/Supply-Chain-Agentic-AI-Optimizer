# src/simulation/simulator.py

"""
Supply Chain Simulation Engine

Replays historical sales data and tests different ordering strategies.
Allows A/B comparison between baseline and agent-based systems.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class SimulationConfig:
    """Configuration for simulation run"""

    start_date: str
    end_date: str
    initial_inventory_multiplier: float = 1.0  # Multiplier on supply_days_target
    random_seed: int = 42
    enable_stockout_penalty: bool = True
    enable_holding_cost: bool = True


@dataclass
class OrderDecision:
    """Represents an ordering decision"""

    date: datetime
    product_id: str
    warehouse_id: str
    supplier_id: str
    units_ordered: int
    reason: str  # Why this decision was made
    metadata: Dict = None  # Additional context (e.g., forecast, urgency)


@dataclass
class SimulationState:
    """Current state of simulation"""

    current_date: datetime
    inventory: Dict[Tuple[str, str], Dict]  # (product_id, warehouse_id) -> state
    pending_orders: List[Dict]
    total_cost: float = 0.0
    total_revenue: float = 0.0
    total_lost_sales: float = 0.0
    stockout_count: int = 0
    orders_placed: List[OrderDecision] = None

    def __post_init__(self):
        if self.orders_placed is None:
            self.orders_placed = []


class SupplyChainSimulator:
    """
    Main simulation engine

    Replays historical sales with different ordering strategies to compare performance.
    """

    def __init__(
        self,
        products_df: pd.DataFrame,
        suppliers_df: pd.DataFrame,
        warehouses_df: pd.DataFrame,
        sales_df: pd.DataFrame,
        config: SimulationConfig,
    ):
        self.products = products_df.set_index("product_id")
        self.suppliers = suppliers_df.set_index("supplier_id")
        self.warehouses = warehouses_df.set_index("warehouse_id")
        self.sales = sales_df.sort_values("date").copy()
        self.config = config

        np.random.seed(config.random_seed)

        # Filter sales to simulation period
        self.sales = self.sales[
            (self.sales["date"] >= config.start_date)
            & (self.sales["date"] <= config.end_date)
        ].copy()

        self.dates = pd.date_range(config.start_date, config.end_date, freq="D")

        print("=" * 70)
        print("SUPPLY CHAIN SIMULATOR INITIALIZED")
        print("=" * 70)
        print(f"Simulation period: {config.start_date} to {config.end_date}")
        print(f"Days to simulate: {len(self.dates)}")
        print(f"Sales transactions: {len(self.sales):,}")
        print(f"Products: {len(self.products)}")
        print("=" * 70)

    def initialize_inventory(self) -> Dict:
        """Create starting inventory state"""
        inventory = {}

        for product_id in self.products.index:
            product = self.products.loc[product_id]

            for warehouse_id in self.warehouses.index:
                # Start with supply_days_target worth of inventory
                initial_stock = int(
                    product["base_demand_daily"]
                    * product["supply_days_target"]
                    * self.config.initial_inventory_multiplier
                )

                inventory[(product_id, warehouse_id)] = {
                    "on_hand": initial_stock,
                    "on_order": 0,
                    "pending_arrivals": [],  # List of (arrival_date, quantity)
                    "total_stockouts": 0,
                    "lost_sales_units": 0,
                    "lost_sales_revenue": 0.0,
                }

        return inventory

    def run(
        self,
        ordering_strategy: Callable[
            [SimulationState, pd.DataFrame], List[OrderDecision]
        ],
    ) -> Tuple[SimulationState, pd.DataFrame, pd.DataFrame]:
        """
        Run simulation with given ordering strategy

        Args:
            ordering_strategy: Function that takes (state, products) and returns list of OrderDecisions

        Returns:
            final_state: Final simulation state
            metrics_df: Daily metrics dataframe
            orders_df: All orders placed
        """

        print(f"\n{'='*70}")
        print("RUNNING SIMULATION")
        print(f"{'='*70}")
        print(f"Strategy: {ordering_strategy.__name__}")
        print()

        # Initialize
        state = SimulationState(
            current_date=pd.to_datetime(self.config.start_date),
            inventory=self.initialize_inventory(),
            pending_orders=[],
        )

        daily_metrics = []

        # Simulate day by day
        for idx, date in enumerate(self.dates):
            if idx % 100 == 0:
                pct = (idx / len(self.dates)) * 100
                print(f"  Day {idx+1}/{len(self.dates)} ({pct:.1f}%) - {date.date()}")

            state.current_date = date

            # 1. Process arrivals
            self._process_arrivals(state)

            # 2. Process sales (and record lost sales)
            self._process_sales(state, date)

            # 3. Run ordering strategy
            decisions = ordering_strategy(state, self.products)

            # 4. Place orders
            for decision in decisions:
                self._place_order(state, decision)

            # 5. Record metrics
            metrics = self._calculate_daily_metrics(state, date)
            daily_metrics.append(metrics)

        # Convert to DataFrames
        metrics_df = pd.DataFrame(daily_metrics)
        orders_df = pd.DataFrame(
            [
                {
                    "date": d.date,
                    "product_id": d.product_id,
                    "warehouse_id": d.warehouse_id,
                    "supplier_id": d.supplier_id,
                    "units_ordered": d.units_ordered,
                    "reason": d.reason,
                    "metadata": d.metadata,
                }
                for d in state.orders_placed
            ]
        )

        print()
        print(f"{'='*70}")
        print("SIMULATION COMPLETE")
        print(f"{'='*70}")
        print(f"Total revenue: ${state.total_revenue:,.2f}")
        print(f"Total cost: ${state.total_cost:,.2f}")
        print(f"Lost sales: ${state.total_lost_sales:,.2f}")
        print(f"Stockout incidents: {state.stockout_count}")
        print(f"Orders placed: {len(state.orders_placed)}")
        print(f"{'='*70}")

        return state, metrics_df, orders_df

    def _process_arrivals(self, state: SimulationState):
        """Process orders arriving today"""
        for key, inv_data in state.inventory.items():
            arrivals_today = [
                (arr_date, qty)
                for arr_date, qty in inv_data["pending_arrivals"]
                if arr_date == state.current_date
            ]

            for arr_date, qty in arrivals_today:
                inv_data["on_hand"] += qty
                inv_data["on_order"] -= qty
                inv_data["pending_arrivals"].remove((arr_date, qty))

    def _process_sales(self, state: SimulationState, date: pd.Timestamp):
        """Process sales and track lost sales"""
        daily_sales = self.sales[self.sales["date"] == date]

        for _, sale in daily_sales.iterrows():
            key = (sale["product_id"], sale["warehouse_id"])

            if key in state.inventory:
                current = state.inventory[key]["on_hand"]
                sold = sale["units_sold"]

                # Can only sell what we have
                actual_sold = min(current, sold)
                lost_sale_units = sold - actual_sold

                # Deduct from inventory
                state.inventory[key]["on_hand"] = max(0, current - sold)

                # Track revenue
                state.total_revenue += actual_sold * sale["unit_price"]

                # Track lost sales
                if lost_sale_units > 0:
                    lost_revenue = lost_sale_units * sale["unit_price"]
                    state.inventory[key]["lost_sales_units"] += lost_sale_units
                    state.inventory[key]["lost_sales_revenue"] += lost_revenue
                    state.total_lost_sales += lost_revenue

                    if state.inventory[key]["on_hand"] == 0:
                        state.inventory[key]["total_stockouts"] += 1
                        state.stockout_count += 1

    def _place_order(self, state: SimulationState, decision: OrderDecision):
        """Execute an order decision"""
        product = self.products.loc[decision.product_id]
        supplier = self.suppliers.loc[decision.supplier_id]

        # Calculate actual lead time (with variability)
        expected_lead_time = supplier["lead_time_days"]
        actual_lead_time = int(
            np.random.normal(expected_lead_time, supplier["lead_time_std_dev"])
        )
        actual_lead_time = max(1, actual_lead_time)

        # Simulate reliability
        if np.random.random() > supplier["reliability_score"]:
            delay = int(np.random.uniform(2, 7))
            actual_lead_time += delay

        arrival_date = decision.date + timedelta(days=actual_lead_time)

        # Calculate costs
        unit_cost = product["unit_cost"]

        # Volume discount
        if decision.units_ordered >= supplier["volume_discount_threshold_units"]:
            unit_cost *= 1 - supplier["volume_discount_pct"]

        product_cost = decision.units_ordered * unit_cost
        shipping_cost = (
            product["weight_kg"]
            * decision.units_ordered
            * supplier["shipping_cost_per_kg"]
        )
        total_cost = product_cost + shipping_cost

        # Update state
        state.total_cost += total_cost

        key = (decision.product_id, decision.warehouse_id)
        state.inventory[key]["on_order"] += decision.units_ordered
        state.inventory[key]["pending_arrivals"].append(
            (arrival_date, decision.units_ordered)
        )

        # Record decision
        state.orders_placed.append(decision)

    def _calculate_daily_metrics(
        self, state: SimulationState, date: pd.Timestamp
    ) -> Dict:
        """Calculate metrics for the day"""
        # Inventory snapshot
        total_inventory_value = 0
        total_inventory_units = 0
        stockout_count_today = 0

        for key, inv_data in state.inventory.items():
            product_id, warehouse_id = key
            product = self.products.loc[product_id]

            total_inventory_units += inv_data["on_hand"]
            total_inventory_value += inv_data["on_hand"] * product["unit_cost"]

            if inv_data["on_hand"] == 0:
                stockout_count_today += 1

        return {
            "date": date,
            "total_inventory_units": total_inventory_units,
            "total_inventory_value": total_inventory_value,
            "stockout_count": stockout_count_today,
            "cumulative_revenue": state.total_revenue,
            "cumulative_cost": state.total_cost,
            "cumulative_lost_sales": state.total_lost_sales,
            "orders_placed_today": len(
                [o for o in state.orders_placed if o.date == date]
            ),
        }


def baseline_reorder_point_strategy(
    state: SimulationState, products: pd.DataFrame
) -> List[OrderDecision]:
    """
    Simple reorder point strategy (baseline)

    Logic: IF inventory <= reorder_point AND no pending orders THEN order
    """
    decisions = []

    for key, inv_data in state.inventory.items():
        product_id, warehouse_id = key
        product = products.loc[product_id]

        # Reorder point
        reorder_point = product["reorder_point_units"]

        # Simple rule
        if inv_data["on_hand"] <= reorder_point and inv_data["on_order"] == 0:
            # Order quantity: enough to reach supply_days_target
            order_qty = int(
                product["base_demand_daily"] * product["supply_days_target"] * 1.2
            )

            # Get supplier (use assigned supplier)
            supplier_id = product["supplier_id"]

            decisions.append(
                OrderDecision(
                    date=state.current_date,
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    supplier_id=supplier_id,
                    units_ordered=order_qty,
                    reason="reorder_point_triggered",
                    metadata={
                        "reorder_point": reorder_point,
                        "inventory": inv_data["on_hand"],
                    },
                )
            )

    return decisions


# Convenience function
def run_baseline_simulation(
    products_df: pd.DataFrame,
    suppliers_df: pd.DataFrame,
    warehouses_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    start_date: str = "2023-01-01",
    end_date: str = "2024-12-31",
) -> Tuple[SimulationState, pd.DataFrame, pd.DataFrame]:
    """Run simulation with baseline strategy"""

    config = SimulationConfig(start_date=start_date, end_date=end_date)

    simulator = SupplyChainSimulator(
        products_df, suppliers_df, warehouses_df, sales_df, config
    )

    return simulator.run(baseline_reorder_point_strategy)


def main():
    """Test simulation"""
    from src.utils.db import SupplyChainDB

    print("\nLoading data...")
    db = SupplyChainDB()

    products = db.query("SELECT * FROM products")
    suppliers = db.query("SELECT * FROM suppliers")
    warehouses = db.query("SELECT * FROM warehouses")
    sales = db.query("SELECT * FROM sales")
    sales["date"] = pd.to_datetime(sales["date"])

    # Run short test (1 month)
    print("\nRunning 1-month test simulation...")
    config = SimulationConfig(start_date="2023-01-01", end_date="2023-01-31")

    simulator = SupplyChainSimulator(products, suppliers, warehouses, sales, config)
    final_state, metrics_df, orders_df = simulator.run(baseline_reorder_point_strategy)

    print("\n📊 Test Simulation Results:")
    print(f"Revenue: ${final_state.total_revenue:,.2f}")
    print(f"Cost: ${final_state.total_cost:,.2f}")
    print(f"Profit: ${final_state.total_revenue - final_state.total_cost:,.2f}")
    print(f"Lost sales: ${final_state.total_lost_sales:,.2f}")
    print(f"Orders placed: {len(orders_df)}")

    return final_state, metrics_df, orders_df


if __name__ == "__main__":
    main()
