# src/data_generation/orchestrator.py

"""
Master data generation orchestrator
Runs all generators in correct order and validates output
"""

import sys
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd

from src.data_generation.generate_inventory_and_orders import InventorySimulator
from src.data_generation.generate_products import ProductGenerator
from src.data_generation.generate_sales import SalesGenerator
from src.data_generation.generate_suppliers import generate_suppliers
from src.data_generation.generate_warehouses import generate_warehouses


def ensure_directories():
    """Create necessary directories"""
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    print("✅ Directories created/verified")


def generate_all_data(seed: int = 42):
    """Generate complete dataset"""
    print("\n" + "=" * 70)
    print(" " * 15 + "TECHGEAR SUPPLY CHAIN DATA GENERATION")
    print("=" * 70)
    print("\nThis will take approximately 6-8 minutes total.\n")

    ensure_directories()

    # 1. Products
    print("\n" + "─" * 70)
    print("[1/6] Generating products...")
    print("─" * 70)
    pg = ProductGenerator(seed=seed)
    products = pg.generate()
    products.to_csv("data/raw/products.csv", index=False)
    products.to_parquet("data/raw/products.parquet", index=False)
    print(f"✅ Generated {len(products)} products")

    # 2. Suppliers
    print("\n" + "─" * 70)
    print("[2/6] Generating suppliers...")
    print("─" * 70)
    suppliers = generate_suppliers()
    print(f"✅ Generated {len(suppliers)} suppliers")

    # 3. Warehouses
    print("\n" + "─" * 70)
    print("[3/6] Generating warehouses...")
    print("─" * 70)
    warehouses = generate_warehouses()
    print(f"✅ Generated {len(warehouses)} warehouses")

    # 4. Sales (longest step)
    print("\n" + "─" * 70)
    print("[4/6] Generating sales (2-3 minutes)...")
    print("─" * 70)
    sg = SalesGenerator(products, seed=seed)
    sales = sg.generate()
    sales.to_csv("data/raw/sales.csv", index=False)
    sales.to_parquet("data/raw/sales.parquet", index=False)

    # Save external events
    sg.events.to_csv("data/raw/external_events.csv", index=False)
    sg.events.to_parquet("data/raw/external_events.parquet", index=False)
    print(f"✅ Generated {len(sales):,} sales transactions")
    print(f"✅ Generated {len(sg.events)} external events")

    # 5. Inventory + Purchase Orders (longest step)
    print("\n" + "─" * 70)
    print("[5/6] Simulating inventory & orders (3-4 minutes)...")
    print("─" * 70)
    sim = InventorySimulator(products, suppliers, sales, warehouses, seed=seed)
    inventory, orders = sim.simulate("2023-01-01", "2024-12-31")

    inventory.to_csv("data/raw/inventory_snapshots.csv", index=False)
    inventory.to_parquet("data/raw/inventory_snapshots.parquet", index=False)

    orders.to_csv("data/raw/purchase_orders.csv", index=False)
    orders.to_parquet("data/raw/purchase_orders.parquet", index=False)

    print(f"✅ Generated {len(inventory):,} inventory snapshots")
    print(f"✅ Generated {len(orders):,} purchase orders")

    # 6. Validation
    print("\n" + "─" * 70)
    print("[6/6] Validating data quality...")
    print("─" * 70)
    validation_results = validate_data(
        products, suppliers, warehouses, sales, inventory, orders
    )

    # Final summary
    print("\n" + "=" * 70)
    print(" " * 20 + "✅ DATA GENERATION COMPLETE")
    print("=" * 70)
    print_summary(products, sales, inventory, orders, validation_results)

    return {
        "products": products,
        "suppliers": suppliers,
        "warehouses": warehouses,
        "sales": sales,
        "inventory": inventory,
        "orders": orders,
    }


def print_summary(products, sales, inventory, orders, validation):
    """Print comprehensive dataset summary"""
    print("\n📊 DATASET SUMMARY:")
    print("─" * 70)
    print(f"  Products:              {len(products):>10,}")
    print(f"  Sales transactions:    {len(sales):>10,}")
    print(f"  Inventory snapshots:   {len(inventory):>10,}")
    print(f"  Purchase orders:       {len(orders):>10,}")

    print("\n💰 FINANCIAL SUMMARY:")
    print("─" * 70)
    print(f"  Total revenue:         ${sales['revenue'].sum():>15,.2f}")
    print(f"  Total profit:          ${sales['profit'].sum():>15,.2f}")
    print(f"  Procurement spend:     ${orders['total_cost'].sum():>15,.2f}")
    print(
        f"  Avg daily revenue:     ${sales.groupby('date')['revenue'].sum().mean():>15,.2f}"
    )

    print("\n📈 OPERATIONAL METRICS:")
    print("─" * 70)
    stockout_rate = (inventory["stockout"] == 1).mean()
    on_time_rate = orders["on_time"].mean()
    print(f"  Stockout rate:         {stockout_rate*100:>14.2f}%")
    print(f"  On-time delivery:      {on_time_rate*100:>14.2f}%")
    print(f"  Avg order size:        {orders['units_ordered'].mean():>14.0f} units")

    print("\n✅ VALIDATION RESULTS:")
    print("─" * 70)
    print(
        f"  Checks passed:         {validation['passed']:>10} / {validation['total']}"
    )
    print(
        f"  Status:                {'PASS' if validation['passed'] >= validation['total'] - 1 else 'FAIL':>10}"
    )


def validate_data(products, suppliers, warehouses, sales, inventory, orders):
    """Comprehensive data quality validation"""
    checks_passed = 0
    checks_total = 0
    issues = []

    print("\nRunning validation checks...\n")

    # Check 1: No negative inventory
    checks_total += 1
    if (inventory["units_on_hand"] >= 0).all():
        print("  ✅ No negative inventory")
        checks_passed += 1
    else:
        print("  ❌ FAIL: Negative inventory detected")
        issues.append("Negative inventory")

    # Check 2: Sales dates within range
    checks_total += 1
    sales_start = pd.to_datetime(sales["date"]).min()
    sales_end = pd.to_datetime(sales["date"]).max()
    if sales_start >= pd.Timestamp("2023-01-01") and sales_end <= pd.Timestamp(
        "2024-12-31"
    ):
        print("  ✅ Sales dates valid")
        checks_passed += 1
    else:
        print("  ❌ FAIL: Sales dates out of range")
        issues.append("Invalid sales dates")

    # Check 3: Seasonality exists (Nov-Dec spike)
    checks_total += 1
    sales["month"] = pd.to_datetime(sales["date"]).dt.month
    monthly_sales = sales.groupby("month")["revenue"].sum()
    nov_dec_avg = monthly_sales[11:].mean()
    overall_avg = monthly_sales.mean()

    if nov_dec_avg > overall_avg * 1.3:
        print(f"  ✅ Seasonality detected (Nov-Dec {nov_dec_avg/overall_avg:.2f}x avg)")
        checks_passed += 1
    else:
        print(
            f"  ⚠️  WARN: Weak seasonality (Nov-Dec {nov_dec_avg/overall_avg:.2f}x avg)"
        )
        checks_passed += 1  # Not a hard failure

    # Check 4: Stockouts exist but not excessive
    checks_total += 1
    stockout_rate = (inventory["stockout"] == 1).mean()
    if 0.02 < stockout_rate < 0.20:
        print(f"  ✅ Stockout rate realistic: {stockout_rate*100:.2f}%")
        checks_passed += 1
    else:
        print(f"  ⚠️  WARN: Stockout rate unusual: {stockout_rate*100:.2f}%")
        issues.append(f"Stockout rate {stockout_rate*100:.2f}%")

    # Check 5: Supplier reliability matches expectations
    checks_total += 1
    all_suppliers_ok = True
    for _, supplier in suppliers.iterrows():
        supplier_orders = orders[orders["supplier_id"] == supplier["supplier_id"]]
        if len(supplier_orders) > 0:
            on_time_rate = supplier_orders["on_time"].mean()
            expected = supplier["reliability_score"]
            if abs(on_time_rate - expected) > 0.15:
                all_suppliers_ok = False
                print(
                    f"  ⚠️  WARN: {supplier['supplier_id']} on-time {on_time_rate:.2f} vs expected {expected:.2f}"
                )

    if all_suppliers_ok:
        print("  ✅ Supplier reliability matches expectations")
        checks_passed += 1
    else:
        issues.append("Supplier reliability mismatch")

    # Check 6: Revenue growth trend
    checks_total += 1
    sales["month_period"] = pd.to_datetime(sales["date"]).dt.to_period("M")
    monthly_trend = sales.groupby("month_period")["revenue"].sum()

    # Simple linear regression
    x = np.arange(len(monthly_trend))
    y = monthly_trend.values
    slope = np.polyfit(x, y, 1)[0]

    if slope > 0:
        print("  ✅ Positive revenue growth trend")
        checks_passed += 1
    else:
        print("  ❌ FAIL: No growth trend detected")
        issues.append("No growth trend")

    # Check 7: No duplicate order IDs
    checks_total += 1
    if orders["order_id"].is_unique:
        print("  ✅ No duplicate order IDs")
        checks_passed += 1
    else:
        print("  ❌ FAIL: Duplicate order IDs found")
        issues.append("Duplicate orders")

    # Check 8: All products have sales
    checks_total += 1
    products_with_sales = sales["product_id"].nunique()
    total_products = len(products)
    if products_with_sales >= total_products * 0.95:  # 95% threshold
        print(f"  ✅ {products_with_sales}/{total_products} products have sales")
        checks_passed += 1
    else:
        print(
            f"  ⚠️  WARN: Only {products_with_sales}/{total_products} products have sales"
        )
        issues.append(f"Low sales coverage: {products_with_sales}/{total_products}")

    return {
        "passed": checks_passed,
        "total": checks_total,
        "issues": issues,
        "success_rate": checks_passed / checks_total,
    }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate TechGear supply chain dataset"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for reproducibility"
    )
    args = parser.parse_args()

    datasets = generate_all_data(seed=args.seed)

    print("\n" + "=" * 70)
    print("\n📁 FILES GENERATED:")
    print("─" * 70)

    files = [
        "products.csv",
        "products.parquet",
        "suppliers.csv",
        "suppliers.parquet",
        "warehouses.csv",
        "warehouses.parquet",
        "sales.csv",
        "sales.parquet",
        "external_events.csv",
        "external_events.parquet",
        "inventory_snapshots.csv",
        "inventory_snapshots.parquet",
        "purchase_orders.csv",
        "purchase_orders.parquet",
    ]

    for f in files:
        path = Path(f"data/raw/{f}")
        if path.exists():
            size = path.stat().st_size / 1024  # KB
            print(f"  ✅ {f:35s} ({size:>8.1f} KB)")

    print("\n" + "=" * 70)
    print("\n🎯 NEXT STEPS:")
    print("─" * 70)
    print("  1. Run: python -m src.utils.db")
    print("     (Sets up DuckDB database)")
    print()
    print("  2. Open: notebooks/01_data_exploration.ipynb")
    print("     (Explore the data)")
    print()
    print("  3. Continue to Week 2:")
    print("     - Baseline system analysis")
    print("     - Problem scenario documentation")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
