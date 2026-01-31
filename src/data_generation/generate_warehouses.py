# src/data_generation/generate_warehouses.py

import pandas as pd
from pathlib import Path


def generate_warehouses() -> pd.DataFrame:
    """Generate warehouse specifications"""
    
    warehouses = [
        {
            'warehouse_id': 'WH-EAST',
            'name': 'Newark Distribution Center',
            'location': 'Newark, NJ',
            'region': 'Northeast',
            'max_units': 5000,
            'max_value_usd': 2500000,
            'max_weight_kg': 15000,
            'cost_per_unit_per_month': 0.50,
            'utilization_target_pct': 75,
            'handling_cost_per_unit': 1.20,
            'serves_regions': 'Northeast,Southeast'
        },
        {
            'warehouse_id': 'WH-CENTRAL',
            'name': 'Chicago Logistics Hub',
            'location': 'Chicago, IL',
            'region': 'Midwest',
            'max_units': 7000,
            'max_value_usd': 3000000,
            'max_weight_kg': 20000,
            'cost_per_unit_per_month': 0.40,
            'utilization_target_pct': 80,
            'handling_cost_per_unit': 1.00,
            'serves_regions': 'Midwest,Central,South'
        },
        {
            'warehouse_id': 'WH-WEST',
            'name': 'Los Angeles West Coast Center',
            'location': 'Los Angeles, CA',
            'region': 'West',
            'max_units': 4500,
            'max_value_usd': 2000000,
            'max_weight_kg': 12000,
            'cost_per_unit_per_month': 0.65,
            'utilization_target_pct': 70,
            'handling_cost_per_unit': 1.35,
            'serves_regions': 'West,Southwest'
        }
    ]
    
    df = pd.DataFrame(warehouses)
    
    # Save
    Path('data/raw').mkdir(parents=True, exist_ok=True)
    df.to_csv('data/raw/warehouses.csv', index=False)
    df.to_parquet('data/raw/warehouses.parquet', index=False)
    
    print("✅ Generated 3 warehouses:")
    print(df[['warehouse_id', 'location', 'max_units', 'cost_per_unit_per_month']])
    
    return df


if __name__ == "__main__":
    generate_warehouses()
