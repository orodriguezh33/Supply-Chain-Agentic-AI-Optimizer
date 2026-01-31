# src/data_generation/generate_products.py

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class CategorySpec:
    """Specifications for product category"""

    base_price: float
    base_cost: float
    count: int
    base_demand_daily: int
    weight_kg: float
    supply_days_target: int


class ProductGenerator:
    """Generates realistic product catalog for B2B electronics distributor"""

    CATEGORIES = {
        "Laptops": CategorySpec(
            base_price=700,
            base_cost=450,
            count=8,
            base_demand_daily=2,
            weight_kg=2.5,
            supply_days_target=30,
        ),
        "Tablets": CategorySpec(
            base_price=450,
            base_cost=280,
            count=6,
            base_demand_daily=10,
            weight_kg=0.8,
            supply_days_target=25,
        ),
        "Monitors": CategorySpec(
            base_price=300,
            base_cost=180,
            count=6,
            base_demand_daily=12,
            weight_kg=5.0,
            supply_days_target=35,
        ),
        "Keyboards": CategorySpec(
            base_price=80,
            base_cost=35,
            count=8,
            base_demand_daily=25,
            weight_kg=1.2,
            supply_days_target=45,
        ),
        "Mice": CategorySpec(
            base_price=40,
            base_cost=18,
            count=8,
            base_demand_daily=30,
            weight_kg=0.3,
            supply_days_target=45,
        ),
        "USB-C-Cables": CategorySpec(
            base_price=15,
            base_cost=5,
            count=6,
            base_demand_daily=50,
            weight_kg=0.1,
            supply_days_target=60,
        ),
        "Laptop-Bags": CategorySpec(
            base_price=50,
            base_cost=22,
            count=4,
            base_demand_daily=1,
            weight_kg=0.6,
            supply_days_target=15,
        ),
        "Docking-Stations": CategorySpec(
            base_price=150,
            base_cost=85,
            count=4,
            base_demand_daily=8,
            weight_kg=1.5,
            supply_days_target=35,
        ),
    }

    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.seed = seed

    def generate(self) -> pd.DataFrame:
        """Generate complete product catalog"""
        products = []
        product_id_counter = 1

        for category_name, spec in self.CATEGORIES.items():
            for i in range(spec.count):
                # Price variation within category (±30%)
                price_variation = np.random.uniform(0.7, 1.3)

                # Quality tier affects price/cost
                tier = np.random.choice(
                    ["Budget", "Standard", "Premium"], p=[0.3, 0.5, 0.2]
                )
                tier_multiplier = {"Budget": 0.8, "Standard": 1.0, "Premium": 1.3}[tier]

                final_price = round(
                    spec.base_price * price_variation * tier_multiplier, 2
                )
                final_cost = round(
                    spec.base_cost * price_variation * tier_multiplier, 2
                )

                # Assign supplier
                supplier_id = self._assign_supplier(category_name, tier)

                product = {
                    "product_id": f"{category_name[:3].upper()}-{product_id_counter:03d}",
                    "name": f"{category_name.replace('-', ' ')} {tier} Model-{chr(65+i)}",
                    "category": category_name,
                    "tier": tier,
                    "unit_price": final_price,
                    "unit_cost": final_cost,
                    "margin_pct": round(
                        (final_price - final_cost) / final_price * 100, 1
                    ),
                    "supplier_id": supplier_id,
                    "base_demand_daily": spec.base_demand_daily,
                    "weight_kg": round(spec.weight_kg * np.random.uniform(0.9, 1.1), 2),
                    "supply_days_target": spec.supply_days_target,
                    "reorder_point_multiplier": np.random.uniform(0.3, 0.6),
                }

                products.append(product)
                product_id_counter += 1

        df = pd.DataFrame(products)

        # Add calculated fields
        df["safety_stock_days"] = (df["supply_days_target"] * 0.5).round(0).astype(int)
        df["reorder_point_units"] = (
            (df["base_demand_daily"] * 15 * df["reorder_point_multiplier"])
            .round(0)
            .astype(int)
        )

        return df

    def _assign_supplier(self, category: str, tier: str) -> str:
        """Assign supplier based on category and tier logic"""
        # High-value items → SUP-A (premium, reliable)
        # Fast-moving accessories → SUP-B (fast delivery)
        # Bulk items → SUP-C (volume discounts)

        if category in ["Laptops", "Tablets", "Monitors"]:
            if tier == "Premium":
                return "SUP-A"
            else:
                return np.random.choice(["SUP-A", "SUP-B"], p=[0.6, 0.4])

        elif category in ["USB-C-Cables", "Mice", "Keyboards"]:
            return np.random.choice(["SUP-B", "SUP-C"], p=[0.4, 0.6])

        else:  # Bags, Docking stations
            return np.random.choice(["SUP-A", "SUP-B", "SUP-C"], p=[0.3, 0.4, 0.3])


def main():
    """Generate and save products"""
    print("=" * 60)
    print("GENERATING PRODUCT CATALOG")
    print("=" * 60)

    # Ensure output directory exists
    Path("data/raw").mkdir(parents=True, exist_ok=True)

    generator = ProductGenerator(seed=42)
    products_df = generator.generate()

    # Save both formats
    products_df.to_csv("data/raw/products.csv", index=False)
    products_df.to_parquet("data/raw/products.parquet", index=False)

    # Summary statistics
    print(f"\n✅ Generated {len(products_df)} products")
    print("\nBy Category:")
    category_counts = products_df.groupby("category").size()
    for cat, count in category_counts.items():
        print(f"  {cat:20s}: {count} products")

    print("\nBy Tier:")
    tier_counts = products_df.groupby("tier").size()
    for tier, count in tier_counts.items():
        print(f"  {tier:20s}: {count} products")

    print("\nBy Supplier:")
    supplier_counts = products_df.groupby("supplier_id").size()
    for supplier, count in supplier_counts.items():
        print(f"  {supplier:20s}: {count} products")

    print("\nPrice Statistics:")
    print(f"  Min price: ${products_df['unit_price'].min():.2f}")
    print(f"  Max price: ${products_df['unit_price'].max():.2f}")
    print(f"  Avg price: ${products_df['unit_price'].mean():.2f}")
    print(f"  Avg margin: {products_df['margin_pct'].mean():.1f}%")

    print("\nFiles saved:")
    print("  data/raw/products.csv")
    print("  data/raw/products.parquet")
    print("=" * 60)

    return products_df


if __name__ == "__main__":
    main()
