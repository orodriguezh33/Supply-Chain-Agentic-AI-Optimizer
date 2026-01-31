# src/data_generation/generate_suppliers.py

from pathlib import Path

import pandas as pd


def generate_suppliers() -> pd.DataFrame:
    """Generate supplier catalog with different characteristics"""

    suppliers = [
        {
            "supplier_id": "SUP-A",
            "name": "GlobalTech Solutions",
            "location": "Shenzhen, China",
            "lead_time_days": 14,
            "lead_time_std_dev": 3,
            "moq_units": 50,
            "moq_value": 20000,
            "payment_terms": "Net-60",
            "reliability_score": 0.94,
            "volume_discount_threshold_units": 200,
            "volume_discount_pct": 0.05,
            "shipping_cost_per_kg": 2.50,
            "accepts_rush_orders": True,
            "rush_order_fee_pct": 0.15,
        },
        {
            "supplier_id": "SUP-B",
            "name": "FastSupply Inc",
            "location": "Los Angeles, USA",
            "lead_time_days": 7,
            "lead_time_std_dev": 2,
            "moq_units": 100,
            "moq_value": 15000,
            "payment_terms": "Net-30",
            "reliability_score": 0.88,
            "volume_discount_threshold_units": 300,
            "volume_discount_pct": 0.03,
            "shipping_cost_per_kg": 1.80,
            "accepts_rush_orders": True,
            "rush_order_fee_pct": 0.10,
        },
        {
            "supplier_id": "SUP-C",
            "name": "BulkSource Wholesale",
            "location": "Mumbai, India",
            "lead_time_days": 21,
            "lead_time_std_dev": 4,
            "moq_units": 500,
            "moq_value": 5000,
            "payment_terms": "Net-90",
            "reliability_score": 0.97,
            "volume_discount_threshold_units": 1000,
            "volume_discount_pct": 0.08,
            "shipping_cost_per_kg": 3.20,
            "accepts_rush_orders": False,
            "rush_order_fee_pct": None,
        },
    ]

    df = pd.DataFrame(suppliers)

    # Save
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    df.to_csv("data/raw/suppliers.csv", index=False)
    df.to_parquet("data/raw/suppliers.parquet", index=False)

    print("✅ Generated 3 suppliers:")
    print(
        df[["supplier_id", "name", "lead_time_days", "reliability_score", "moq_units"]]
    )

    return df


if __name__ == "__main__":
    generate_suppliers()
