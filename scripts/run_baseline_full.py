# scripts/run_baseline_full.py

"""
Run full baseline simulation and save results

This creates the benchmark we'll compare our agent against.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import json

import pandas as pd

from src.simulation import MetricsCalculator, run_baseline_simulation
from src.utils.db import SupplyChainDB


def main():
    print("\n" + "=" * 70)
    print("FULL BASELINE SIMULATION RUN")
    print("=" * 70)

    # Load data
    print("\nLoading data from database...")
    db = SupplyChainDB()

    products = db.query("SELECT * FROM products")
    suppliers = db.query("SELECT * FROM suppliers")
    warehouses = db.query("SELECT * FROM warehouses")
    sales = db.query("SELECT * FROM sales")
    sales["date"] = pd.to_datetime(sales["date"])

    print(f"✅ Loaded {len(products)} products")
    print(f"✅ Loaded {len(sales):,} sales transactions")

    # Run simulation
    print("\n" + "=" * 70)
    print("Running full simulation (2023-2024 = 731 days)")
    print("This will take 3-5 minutes...")
    print("=" * 70)

    final_state, metrics_df, orders_df = run_baseline_simulation(
        products,
        suppliers,
        warehouses,
        sales,
        start_date="2023-01-01",
        end_date="2024-12-31",
    )

    # Calculate metrics
    print("\nCalculating comprehensive metrics...")
    calculator = MetricsCalculator(products, suppliers)
    metrics = calculator.calculate(final_state, metrics_df, orders_df)

    print(metrics)

    # Save results
    output_dir = Path("data/processed/simulations")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("SAVING RESULTS")
    print("=" * 70)

    # Save metrics as JSON
    metrics_path = output_dir / "baseline_full_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics.to_dict(), f, indent=2)
    print(f"✅ Metrics saved: {metrics_path}")

    # Save daily metrics
    daily_path = output_dir / "baseline_full_daily_metrics.csv"
    metrics_df.to_csv(daily_path, index=False)
    print(f"✅ Daily metrics saved: {daily_path}")

    # Save orders
    orders_path = output_dir / "baseline_full_orders.csv"
    orders_df.to_csv(orders_path, index=False)
    print(f"✅ Orders saved: {orders_path}")

    # Summary comparison with original baseline
    print("\n" + "=" * 70)
    print("COMPARISON WITH ORIGINAL BASELINE SYSTEM")
    print("=" * 70)

    with open("data/processed/baseline_metrics.json", "r") as f:
        original_baseline = json.load(f)

    print("\nKey Metric Comparison:")
    print("  Stockout Rate:")
    print(f"    Original: {original_baseline['stockout_rate_pct']:.2f}%")
    print(f"    Simulation: {metrics.stockout_rate_pct:.2f}%")

    print("\n  Total Procurement:")
    print(f"    Original: ${original_baseline['total_procurement']:,.2f}")
    print(f"    Simulation: ${metrics.total_procurement_spend:,.2f}")

    print("\n  Discount Capture:")
    print(f"    Original: {original_baseline['discount_capture_pct']:.1f}%")
    print(f"    Simulation: {metrics.discount_capture_rate_pct:.1f}%")

    print("\n  Lost Revenue:")
    print(f"    Original: ${original_baseline['estimated_lost_revenue']:,.2f}")
    print(f"    Simulation: ${metrics.total_lost_sales:,.2f}")

    print("\n" + "=" * 70)
    print("✅ BASELINE SIMULATION COMPLETE")
    print("=" * 70)
    print("\nThese results are your benchmark.")
    print("Agent system must beat these numbers to prove value.")
    print("=" * 70)


if __name__ == "__main__":
    main()
