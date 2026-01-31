# src/data_generation/generate_inventory_and_orders.py

import warnings
from datetime import timedelta
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class InventorySimulator:
    """
    Simulates inventory levels and purchase orders using simple reorder point logic.
    This is the BASELINE that our agentic system will beat.

    Simple reorder point logic:
    - If inventory <= reorder_point AND no pending orders: place order
    - Order quantity = enough to reach supply_days_target
    - No optimization, no forecasting, no event awareness
    """

    def __init__(
        self,
        products_df: pd.DataFrame,
        suppliers_df: pd.DataFrame,
        sales_df: pd.DataFrame,
        warehouses_df: pd.DataFrame,
        seed: int = 42,
    ):
        self.products = products_df.set_index("product_id")
        self.suppliers = suppliers_df.set_index("supplier_id")
        self.sales = sales_df.sort_values("date")
        self.warehouses = warehouses_df.set_index("warehouse_id")
        np.random.seed(seed)

        # State tracking
        self.inventory = self._initialize_inventory()
        self.purchase_orders = []
        self.inventory_snapshots = []

        print("=" * 60)
        print("INVENTORY SIMULATOR INITIALIZED")
        print("=" * 60)
        print(f"Products: {len(self.products)}")
        print(f"Suppliers: {len(self.suppliers)}")
        print(f"Warehouses: {len(self.warehouses)}")
        print(f"Sales records: {len(self.sales):,}")
        print("=" * 60)

    def _initialize_inventory(self) -> Dict:
        """Start with initial inventory in each warehouse"""
        inventory = {}

        print("\nInitializing starting inventory...")

        for product_id in self.products.index:
            product = self.products.loc[product_id]

            for warehouse_id in self.warehouses.index:
                # Start with ~supply_days_target worth of inventory
                initial_stock = int(
                    product["base_demand_daily"] * 10 * np.random.uniform(0.7, 1.2)
                )

                inventory[(product_id, warehouse_id)] = {
                    "on_hand": initial_stock,
                    "on_order": 0,
                    "pending_arrivals": [],  # List of (arrival_date, quantity)
                    "total_stockouts": 0,
                    "lost_sales_units": 0,
                }

        total_initial = sum(inv["on_hand"] for inv in inventory.values())
        print(
            f"✅ Starting inventory: {total_initial:,} units across {len(inventory)} SKU-warehouse combinations"
        )

        return inventory

    def simulate(
        self, start_date: str, end_date: str
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Run day-by-day simulation"""
        dates = pd.date_range(start_date, end_date, freq="D")

        print("\n" + "=" * 60)
        print("RUNNING SIMULATION")
        print("=" * 60)
        print(f"Simulating {len(dates)} days ({start_date} to {end_date})")
        print("This will take 3-4 minutes...")
        print()

        for idx, date in enumerate(dates):
            if idx % 100 == 0:
                pct = (idx / len(dates)) * 100
                print(f"  Day {idx+1}/{len(dates)} ({pct:.1f}%) - {date.date()}")

            # Daily operations in order
            self._process_arrivals(date)
            self._process_sales(date)
            self._check_and_reorder(date)
            self._take_snapshot(date)

        # Convert to DataFrames
        inventory_df = pd.DataFrame(self.inventory_snapshots)
        orders_df = pd.DataFrame(self.purchase_orders)

        print()
        print("=" * 60)
        print("✅ SIMULATION COMPLETE")
        print("=" * 60)
        print(f"Inventory snapshots: {len(inventory_df):,}")
        print(f"Purchase orders placed: {len(orders_df):,}")
        print("=" * 60)

        return inventory_df, orders_df

    def _process_arrivals(self, date: pd.Timestamp):
        """Process orders arriving today"""
        for key, inv_data in self.inventory.items():
            arrivals_today = [
                (arr_date, qty)
                for arr_date, qty in inv_data["pending_arrivals"]
                if arr_date == date
            ]

            for arr_date, qty in arrivals_today:
                inv_data["on_hand"] += qty
                inv_data["on_order"] -= qty
                inv_data["pending_arrivals"].remove((arr_date, qty))

    def _process_sales(self, date: pd.Timestamp):
        """Deduct sales from inventory"""
        daily_sales = self.sales[self.sales["date"] == date]

        for _, sale in daily_sales.iterrows():
            key = (sale["product_id"], sale["warehouse_id"])

            if key in self.inventory:
                current = self.inventory[key]["on_hand"]
                sold = sale["units_sold"]

                # If we don't have enough, we lose the sale
                actual_sold = min(current, sold)
                lost_sale = sold - actual_sold

                self.inventory[key]["on_hand"] = max(0, current - sold)

                # Track lost sales
                if lost_sale > 0:
                    self.inventory[key]["lost_sales_units"] += lost_sale
                    if self.inventory[key]["on_hand"] == 0:
                        self.inventory[key]["total_stockouts"] += 1

    def _check_and_reorder(self, date: pd.Timestamp):
        """Simple reorder point logic (BASELINE - not optimal)"""
        for key, inv_data in self.inventory.items():
            product_id, warehouse_id = key
            product = self.products.loc[product_id]

            # Reorder point (from product spec)
            reorder_point = product["reorder_point_units"]

            # Solo pide si el azar lo permite (simula ineficiencia humana)
            if inv_data["on_hand"] <= reorder_point and inv_data["on_order"] == 0:
                if np.random.random() < 0.95:  # 30% de las veces no pide aunque deba
                    self._place_order(date, product_id, warehouse_id, product)

    def _place_order(
        self, date: pd.Timestamp, product_id: str, warehouse_id: str, product: pd.Series
    ):
        """Place a purchase order"""
        supplier_id = product["supplier_id"]
        supplier = self.suppliers.loc[supplier_id]

        # Order quantity: simple EOQ approximation
        # Target: reach supply_days_target + 20% buffer
        order_qty = int(
            product["base_demand_daily"] * product["supply_days_target"] * 1.0
        )

        # Respect MOQ (minimum order quantity)
        if order_qty < supplier["moq_units"]:
            order_qty = int(supplier["moq_units"])

        # Calculate actual lead time (with variability)
        expected_lead_time = supplier["lead_time_days"]
        actual_lead_time = int(
            np.random.normal(expected_lead_time, supplier["lead_time_std_dev"])
        )
        actual_lead_time = max(1, actual_lead_time)

        # Simulate reliability (supplier might be late)
        on_time = True
        if np.random.random() > supplier["reliability_score"]:
            # Late delivery
            delay_days = int(np.random.uniform(2, 7))
            actual_lead_time += delay_days
            on_time = False

        arrival_date = date + timedelta(days=actual_lead_time)

        # Unit cost with volume discount
        unit_cost = product["unit_cost"]
        volume_discount_applied = False

        if order_qty >= supplier["volume_discount_threshold_units"]:
            unit_cost *= 1 - supplier["volume_discount_pct"]
            volume_discount_applied = True

        # Total cost
        total_cost = order_qty * unit_cost

        # Shipping cost
        shipping_cost = (
            product["weight_kg"] * order_qty * supplier["shipping_cost_per_kg"]
        )
        total_cost_with_shipping = total_cost + shipping_cost

        # Record order
        order = {
            "order_id": f"PO-{len(self.purchase_orders)+1:05d}",
            "order_date": date,
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "supplier_id": supplier_id,
            "units_ordered": order_qty,
            "unit_cost": round(unit_cost, 2),
            "total_cost": round(total_cost, 2),
            "shipping_cost": round(shipping_cost, 2),
            "total_cost_with_shipping": round(total_cost_with_shipping, 2),
            "volume_discount_applied": volume_discount_applied,
            "lead_time_expected": expected_lead_time,
            "lead_time_actual": actual_lead_time,
            "arrival_date": arrival_date,
            "on_time": on_time,
        }

        self.purchase_orders.append(order)

        # Update inventory tracking
        key = (product_id, warehouse_id)
        self.inventory[key]["on_order"] += order_qty
        self.inventory[key]["pending_arrivals"].append((arrival_date, order_qty))

    def _take_snapshot(self, date: pd.Timestamp):
        """Record daily inventory snapshot"""
        for key, inv_data in self.inventory.items():
            product_id, warehouse_id = key
            product = self.products.loc[product_id]

            self.inventory_snapshots.append(
                {
                    "date": date,
                    "product_id": product_id,
                    "warehouse_id": warehouse_id,
                    "units_on_hand": inv_data["on_hand"],
                    "units_on_order": inv_data["on_order"],
                    "reorder_point": product["reorder_point_units"],
                    "stockout": 1 if inv_data["on_hand"] == 0 else 0,
                }
            )


def main():
    """Generate inventory snapshots and purchase orders"""
    print("\n" + "=" * 60)
    print("INVENTORY & PURCHASE ORDERS GENERATION")
    print("=" * 60)

    # Load all required data
    print("\nLoading data files...")
    products_df = pd.read_csv("data/raw/products.csv")
    suppliers_df = pd.read_csv("data/raw/suppliers.csv")
    sales_df = pd.read_csv("data/raw/sales.csv")
    sales_df["date"] = pd.to_datetime(sales_df["date"])
    warehouses_df = pd.read_csv("data/raw/warehouses.csv")

    print(f"✅ Loaded products: {len(products_df)}")
    print(f"✅ Loaded suppliers: {len(suppliers_df)}")
    print(f"✅ Loaded sales: {len(sales_df):,} transactions")
    print(f"✅ Loaded warehouses: {len(warehouses_df)}")

    # Run simulation
    simulator = InventorySimulator(
        products_df=products_df,
        suppliers_df=suppliers_df,
        sales_df=sales_df,
        warehouses_df=warehouses_df,
        seed=42,
    )

    inventory_df, orders_df = simulator.simulate("2023-01-01", "2024-12-31")

    # Save results
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)

    Path("data/raw").mkdir(parents=True, exist_ok=True)

    inventory_df.to_csv("data/raw/inventory_snapshots.csv", index=False)
    inventory_df.to_parquet("data/raw/inventory_snapshots.parquet", index=False)
    print("✅ Saved inventory_snapshots.csv / .parquet")

    orders_df.to_csv("data/raw/purchase_orders.csv", index=False)
    orders_df.to_parquet("data/raw/purchase_orders.parquet", index=False)
    print("✅ Saved purchase_orders.csv / .parquet")

    # Generate summary statistics
    print("\n" + "=" * 60)
    print("BASELINE SYSTEM PERFORMANCE SUMMARY")
    print("=" * 60)

    # Stockout analysis
    stockouts = inventory_df[inventory_df["stockout"] == 1]
    total_snapshots = len(inventory_df)
    stockout_rate = len(stockouts) / total_snapshots

    print("\n📊 INVENTORY METRICS:")
    print(f"  Total inventory snapshots: {total_snapshots:,}")
    print(f"  Stockout incidents: {len(stockouts):,}")
    print(f"  Stockout rate: {stockout_rate*100:.2f}%")

    # Calculate lost sales value
    stockout_products = stockouts.merge(
        products_df[["product_id", "unit_price"]], on="product_id"
    )

    # Estimate lost sales (rough approximation)
    avg_daily_demand = sales_df.groupby("product_id")["units_sold"].mean()
    stockout_products = stockout_products.merge(
        avg_daily_demand.rename("avg_demand"), left_on="product_id", right_index=True
    )
    stockout_products["estimated_lost_revenue"] = (
        stockout_products["avg_demand"] * stockout_products["unit_price"]
    )

    total_lost_revenue = stockout_products["estimated_lost_revenue"].sum()
    print(f"  Estimated lost revenue from stockouts: ${total_lost_revenue:,.2f}")

    # Purchase order analysis
    print("\n📦 PURCHASE ORDER METRICS:")
    print(f"  Total orders placed: {len(orders_df):,}")
    print(f"  Total procurement spend: ${orders_df['total_cost'].sum():,.2f}")
    print(f"  Total with shipping: ${orders_df['total_cost_with_shipping'].sum():,.2f}")
    print(f"  Avg order value: ${orders_df['total_cost'].mean():,.2f}")
    print(f"  Avg order size: {orders_df['units_ordered'].mean():.0f} units")

    # Supplier performance
    print("\n🚚 SUPPLIER PERFORMANCE:")
    for supplier_id in suppliers_df["supplier_id"]:
        supplier_orders = orders_df[orders_df["supplier_id"] == supplier_id]
        if len(supplier_orders) > 0:
            on_time_rate = supplier_orders["on_time"].mean()
            avg_lead_time = supplier_orders["lead_time_actual"].mean()
            total_spend = supplier_orders["total_cost"].sum()
            discount_rate = supplier_orders["volume_discount_applied"].mean()

            print(f"  {supplier_id}:")
            print(f"    Orders: {len(supplier_orders):,}")
            print(f"    Spend: ${total_spend:,.2f}")
            print(f"    On-time rate: {on_time_rate*100:.1f}%")
            print(f"    Avg lead time: {avg_lead_time:.1f} days")
            print(f"    Volume discount rate: {discount_rate*100:.1f}%")

    # Top stockout products
    print("\n⚠️  TOP 10 PRODUCTS BY STOCKOUT INCIDENTS:")
    stockout_by_product = stockouts.groupby("product_id").size().nlargest(10)
    stockout_summary = stockout_by_product.to_frame("stockout_days")
    stockout_summary = stockout_summary.merge(
        products_df[["product_id", "name", "category"]],
        left_index=True,
        right_on="product_id",
    )

    for _, row in stockout_summary.iterrows():
        print(
            f"  {row['product_id']:12s} ({row['category']:15s}): {row['stockout_days']:3d} days"
        )

    # Cost breakdown
    print("\n💰 COST BREAKDOWN:")
    total_product_cost = orders_df["total_cost"].sum()
    total_shipping = orders_df["shipping_cost"].sum()
    volume_discount_orders = orders_df[orders_df["volume_discount_applied"] == True]
    estimated_savings = (
        len(volume_discount_orders) * orders_df["total_cost"].mean() * 0.05
    )  # rough estimate

    print(f"  Product costs: ${total_product_cost:,.2f}")
    print(f"  Shipping costs: ${total_shipping:,.2f}")
    print(
        f"  Orders with volume discount: {len(volume_discount_orders)} ({len(volume_discount_orders)/len(orders_df)*100:.1f}%)"
    )
    print(f"  Estimated savings from discounts: ${estimated_savings:,.2f}")

    print("\n" + "=" * 60)
    print("✅ BASELINE SYSTEM ANALYSIS COMPLETE")
    print("=" * 60)
    print("\nThis baseline will be our benchmark.")
    print("Our agentic system will aim to:")
    print("  • Reduce stockout rate from {:.2f}% to <3%".format(stockout_rate * 100))
    print("  • Reduce total costs by 10-15%")
    print("  • Increase volume discount capture")
    print("  • Better anticipate demand spikes")
    print("=" * 60)

    return inventory_df, orders_df


if __name__ == "__main__":
    main()
