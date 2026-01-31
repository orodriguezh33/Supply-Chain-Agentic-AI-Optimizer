# src/simulation/metrics.py

"""
Metrics calculation and comparison utilities

Calculates comprehensive KPIs for simulation runs and enables A/B comparison.
"""

from dataclasses import asdict, dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for a simulation run"""

    # Financial metrics
    total_revenue: float
    total_cost: float
    total_profit: float
    profit_margin_pct: float

    # Lost sales
    total_lost_sales: float
    lost_sales_pct_of_revenue: float

    # Procurement metrics
    total_orders: int
    avg_order_value: float
    total_procurement_spend: float
    total_shipping_cost: float

    # Discount metrics
    orders_with_discount: int
    discount_capture_rate_pct: float
    total_discount_savings: float

    # Inventory metrics
    avg_inventory_value: float
    avg_inventory_units: float
    stockout_incidents: int
    stockout_rate_pct: float

    # Operational metrics
    avg_orders_per_day: float

    def to_dict(self) -> Dict:
        """Convert to dictionary with JSON-serializable types"""
        d = asdict(self)
        # Convert numpy types to native Python types
        for key, value in d.items():
            if hasattr(value, "item"):  # numpy scalar
                d[key] = value.item()
            elif isinstance(value, (np.integer, np.floating)):
                d[key] = float(value) if isinstance(value, np.floating) else int(value)
        return d

    def __str__(self) -> str:
        """Formatted string representation"""
        return f"""
Performance Metrics Summary
{'='*70}
FINANCIAL:
  Revenue:              ${self.total_revenue:>15,.2f}
  Cost:                 ${self.total_cost:>15,.2f}
  Profit:               ${self.total_profit:>15,.2f}
  Margin:               {self.profit_margin_pct:>14.2f}%

LOST SALES:
  Lost Revenue:         ${self.total_lost_sales:>15,.2f}
  % of Revenue:         {self.lost_sales_pct_of_revenue:>14.2f}%

PROCUREMENT:
  Total Orders:         {self.total_orders:>16,}
  Avg Order Value:      ${self.avg_order_value:>15,.2f}
  Total Spend:          ${self.total_procurement_spend:>15,.2f}
  Shipping Cost:        ${self.total_shipping_cost:>15,.2f}

DISCOUNTS:
  Orders w/ Discount:   {self.orders_with_discount:>16,}
  Capture Rate:         {self.discount_capture_rate_pct:>14.2f}%
  Total Savings:        ${self.total_discount_savings:>15,.2f}

INVENTORY:
  Avg Value:            ${self.avg_inventory_value:>15,.2f}
  Avg Units:            {self.avg_inventory_units:>16,.0f}
  Stockout Count:       {self.stockout_incidents:>16,}
  Stockout Rate:        {self.stockout_rate_pct:>14.2f}%

OPERATIONS:
  Avg Orders/Day:       {self.avg_orders_per_day:>16.2f}
{'='*70}
        """


class MetricsCalculator:
    """Calculate performance metrics from simulation results"""

    def __init__(self, products_df: pd.DataFrame, suppliers_df: pd.DataFrame):
        self.products = products_df.set_index("product_id")
        self.suppliers = suppliers_df.set_index("supplier_id")

    def calculate(
        self, final_state, metrics_df: pd.DataFrame, orders_df: pd.DataFrame
    ) -> PerformanceMetrics:
        """Calculate all metrics from simulation outputs"""

        # Financial
        total_revenue = final_state.total_revenue
        total_cost = final_state.total_cost
        total_profit = total_revenue - total_cost
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

        # Lost sales
        total_lost_sales = final_state.total_lost_sales
        lost_sales_pct = (
            (total_lost_sales / total_revenue * 100) if total_revenue > 0 else 0
        )

        # Procurement
        total_orders = len(orders_df)

        # Calculate order costs (need to reconstruct from orders)
        order_costs = self._calculate_order_costs(orders_df)

        total_procurement = order_costs["total_product_cost"].sum()
        total_shipping = order_costs["shipping_cost"].sum()
        avg_order_value = total_procurement / total_orders if total_orders > 0 else 0

        # Discounts
        orders_with_discount = order_costs["volume_discount_applied"].sum()
        discount_rate = (
            (orders_with_discount / total_orders * 100) if total_orders > 0 else 0
        )
        total_discount_savings = order_costs["discount_savings"].sum()

        # Inventory
        avg_inventory_value = metrics_df["total_inventory_value"].mean()
        avg_inventory_units = metrics_df["total_inventory_units"].mean()

        # Stockouts
        stockout_incidents = final_state.stockout_count
        total_snapshots = len(metrics_df) * len(self.products) * 3  # 3 warehouses
        stockout_rate = (
            (stockout_incidents / total_snapshots * 100) if total_snapshots > 0 else 0
        )

        # Operations
        num_days = len(metrics_df)
        avg_orders_per_day = total_orders / num_days if num_days > 0 else 0

        return PerformanceMetrics(
            total_revenue=total_revenue,
            total_cost=total_cost,
            total_profit=total_profit,
            profit_margin_pct=profit_margin,
            total_lost_sales=total_lost_sales,
            lost_sales_pct_of_revenue=lost_sales_pct,
            total_orders=total_orders,
            avg_order_value=avg_order_value,
            total_procurement_spend=total_procurement,
            total_shipping_cost=total_shipping,
            orders_with_discount=int(orders_with_discount),
            discount_capture_rate_pct=discount_rate,
            total_discount_savings=total_discount_savings,
            avg_inventory_value=avg_inventory_value,
            avg_inventory_units=avg_inventory_units,
            stockout_incidents=stockout_incidents,
            stockout_rate_pct=stockout_rate,
            avg_orders_per_day=avg_orders_per_day,
        )

    def _calculate_order_costs(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate detailed costs for each order"""

        costs = []

        for _, order in orders_df.iterrows():
            product = self.products.loc[order["product_id"]]
            supplier = self.suppliers.loc[order["supplier_id"]]

            # Base unit cost
            unit_cost = product["unit_cost"]
            units = order["units_ordered"]

            # Volume discount check
            threshold = supplier["volume_discount_threshold_units"]
            discount_pct = supplier["volume_discount_pct"]

            if units >= threshold:
                discounted_cost = unit_cost * (1 - discount_pct)
                volume_discount_applied = True
                discount_savings = (unit_cost - discounted_cost) * units
            else:
                discounted_cost = unit_cost
                volume_discount_applied = False
                discount_savings = 0

            # Shipping cost
            shipping = product["weight_kg"] * units * supplier["shipping_cost_per_kg"]

            costs.append(
                {
                    "order_date": order["date"],
                    "product_id": order["product_id"],
                    "supplier_id": order["supplier_id"],
                    "units_ordered": units,
                    "unit_cost": discounted_cost,
                    "total_product_cost": discounted_cost * units,
                    "shipping_cost": shipping,
                    "total_cost": (discounted_cost * units) + shipping,
                    "volume_discount_applied": volume_discount_applied,
                    "discount_savings": discount_savings,
                }
            )

        return pd.DataFrame(costs)

    def compare(
        self, baseline_metrics: PerformanceMetrics, agent_metrics: PerformanceMetrics
    ) -> pd.DataFrame:
        """Compare two sets of metrics and calculate improvements"""

        comparison = []

        # Financial improvements
        comparison.append(
            {
                "category": "Financial",
                "metric": "Revenue",
                "baseline": baseline_metrics.total_revenue,
                "agent": agent_metrics.total_revenue,
                "delta": agent_metrics.total_revenue - baseline_metrics.total_revenue,
                "delta_pct": self._pct_change(
                    baseline_metrics.total_revenue, agent_metrics.total_revenue
                ),
                "better": (
                    "↑"
                    if agent_metrics.total_revenue > baseline_metrics.total_revenue
                    else "↓"
                ),
            }
        )

        comparison.append(
            {
                "category": "Financial",
                "metric": "Cost",
                "baseline": baseline_metrics.total_cost,
                "agent": agent_metrics.total_cost,
                "delta": agent_metrics.total_cost - baseline_metrics.total_cost,
                "delta_pct": self._pct_change(
                    baseline_metrics.total_cost, agent_metrics.total_cost
                ),
                "better": (
                    "↓"
                    if agent_metrics.total_cost < baseline_metrics.total_cost
                    else "↑"
                ),
            }
        )

        comparison.append(
            {
                "category": "Financial",
                "metric": "Profit",
                "baseline": baseline_metrics.total_profit,
                "agent": agent_metrics.total_profit,
                "delta": agent_metrics.total_profit - baseline_metrics.total_profit,
                "delta_pct": self._pct_change(
                    baseline_metrics.total_profit, agent_metrics.total_profit
                ),
                "better": (
                    "↑"
                    if agent_metrics.total_profit > baseline_metrics.total_profit
                    else "↓"
                ),
            }
        )

        # Lost sales
        comparison.append(
            {
                "category": "Lost Sales",
                "metric": "Lost Revenue",
                "baseline": baseline_metrics.total_lost_sales,
                "agent": agent_metrics.total_lost_sales,
                "delta": agent_metrics.total_lost_sales
                - baseline_metrics.total_lost_sales,
                "delta_pct": self._pct_change(
                    baseline_metrics.total_lost_sales, agent_metrics.total_lost_sales
                ),
                "better": (
                    "↓"
                    if agent_metrics.total_lost_sales
                    < baseline_metrics.total_lost_sales
                    else "↑"
                ),
            }
        )

        # Procurement
        comparison.append(
            {
                "category": "Procurement",
                "metric": "Total Spend",
                "baseline": baseline_metrics.total_procurement_spend,
                "agent": agent_metrics.total_procurement_spend,
                "delta": agent_metrics.total_procurement_spend
                - baseline_metrics.total_procurement_spend,
                "delta_pct": self._pct_change(
                    baseline_metrics.total_procurement_spend,
                    agent_metrics.total_procurement_spend,
                ),
                "better": (
                    "↓"
                    if agent_metrics.total_procurement_spend
                    < baseline_metrics.total_procurement_spend
                    else "↑"
                ),
            }
        )

        comparison.append(
            {
                "category": "Procurement",
                "metric": "Shipping Cost",
                "baseline": baseline_metrics.total_shipping_cost,
                "agent": agent_metrics.total_shipping_cost,
                "delta": agent_metrics.total_shipping_cost
                - baseline_metrics.total_shipping_cost,
                "delta_pct": self._pct_change(
                    baseline_metrics.total_shipping_cost,
                    agent_metrics.total_shipping_cost,
                ),
                "better": (
                    "↓"
                    if agent_metrics.total_shipping_cost
                    < baseline_metrics.total_shipping_cost
                    else "↑"
                ),
            }
        )

        comparison.append(
            {
                "category": "Procurement",
                "metric": "Discount Capture %",
                "baseline": baseline_metrics.discount_capture_rate_pct,
                "agent": agent_metrics.discount_capture_rate_pct,
                "delta": agent_metrics.discount_capture_rate_pct
                - baseline_metrics.discount_capture_rate_pct,
                "delta_pct": None,  # Already a percentage
                "better": (
                    "↑"
                    if agent_metrics.discount_capture_rate_pct
                    > baseline_metrics.discount_capture_rate_pct
                    else "↓"
                ),
            }
        )

        # Inventory
        comparison.append(
            {
                "category": "Inventory",
                "metric": "Avg Inventory Value",
                "baseline": baseline_metrics.avg_inventory_value,
                "agent": agent_metrics.avg_inventory_value,
                "delta": agent_metrics.avg_inventory_value
                - baseline_metrics.avg_inventory_value,
                "delta_pct": self._pct_change(
                    baseline_metrics.avg_inventory_value,
                    agent_metrics.avg_inventory_value,
                ),
                "better": (
                    "↓"
                    if agent_metrics.avg_inventory_value
                    < baseline_metrics.avg_inventory_value
                    else "↑"
                ),
            }
        )

        comparison.append(
            {
                "category": "Inventory",
                "metric": "Stockout Rate %",
                "baseline": baseline_metrics.stockout_rate_pct,
                "agent": agent_metrics.stockout_rate_pct,
                "delta": agent_metrics.stockout_rate_pct
                - baseline_metrics.stockout_rate_pct,
                "delta_pct": None,  # Already a percentage
                "better": (
                    "↓"
                    if agent_metrics.stockout_rate_pct
                    < baseline_metrics.stockout_rate_pct
                    else "↑"
                ),
            }
        )

        return pd.DataFrame(comparison)

    def _pct_change(self, baseline: float, agent: float) -> float:
        """Calculate percentage change"""
        if baseline == 0:
            return 0.0
        return ((agent - baseline) / baseline) * 100


def print_comparison(comparison_df: pd.DataFrame):
    """Pretty print comparison table"""
    print("\n" + "=" * 100)
    print("BASELINE vs AGENT COMPARISON")
    print("=" * 100)

    for category in comparison_df["category"].unique():
        cat_data = comparison_df[comparison_df["category"] == category]

        print(f"\n{category}:")
        print("-" * 100)

        for _, row in cat_data.iterrows():
            metric = row["metric"]
            baseline = row["baseline"]
            agent = row["agent"]
            delta = row["delta"]
            delta_pct = row["delta_pct"]
            better = row["better"]

            # Format values
            if baseline > 1000:
                baseline_str = f"${baseline:,.2f}"
                agent_str = f"${agent:,.2f}"
                delta_str = f"${delta:,.2f}"
            else:
                baseline_str = f"{baseline:.2f}"
                agent_str = f"{agent:.2f}"
                delta_str = f"{delta:+.2f}"

            if delta_pct is not None:
                delta_pct_str = f"({delta_pct:+.2f}%)"
            else:
                delta_pct_str = ""

            print(
                f"  {metric:25s}: {baseline_str:>20s} → {agent_str:>20s}  {delta_str:>20s} {delta_pct_str:>12s} {better}"
            )

    print("=" * 100)


def main():
    """Test metrics calculation"""
    from src.simulation.simulator import run_baseline_simulation
    from src.utils.db import SupplyChainDB

    print("\nLoading data...")
    db = SupplyChainDB()

    products = db.query("SELECT * FROM products")
    suppliers = db.query("SELECT * FROM suppliers")
    warehouses = db.query("SELECT * FROM warehouses")
    sales = db.query("SELECT * FROM sales")
    sales["date"] = pd.to_datetime(sales["date"])

    print("\nRunning test simulation (1 month)...")
    final_state, metrics_df, orders_df = run_baseline_simulation(
        products,
        suppliers,
        warehouses,
        sales,
        start_date="2023-01-01",
        end_date="2023-01-31",
    )

    print("\nCalculating metrics...")
    calculator = MetricsCalculator(products, suppliers)
    metrics = calculator.calculate(final_state, metrics_df, orders_df)

    print(metrics)

    # Save metrics
    import json

    output_path = Path("data/processed/test_simulation_metrics.json")
    with open(output_path, "w") as f:
        json.dump(metrics.to_dict(), f, indent=2)

    print(f"\n✅ Metrics saved to: {output_path}")

    return metrics


if __name__ == "__main__":
    from pathlib import Path

    main()
