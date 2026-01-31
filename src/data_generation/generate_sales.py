# src/data_generation/generate_sales.py

import warnings
from datetime import timedelta
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class SalesGenerator:
    """
    Generates realistic sales data with:
    - Seasonality (holidays, back-to-school)
    - Day-of-week patterns
    - Growth trends
    - External events
    - Stockouts
    - Multi-warehouse distribution
    """

    def __init__(
        self,
        products_df: pd.DataFrame,
        start_date: str = "2023-01-01",
        end_date: str = "2024-12-31",
        seed: int = 42,
    ):
        self.products = products_df
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.dates = pd.date_range(start_date, end_date, freq="D")
        np.random.seed(seed)

        # External events
        self.events = self._define_external_events()

        # Warehouse distribution weights
        self.warehouse_weights = {
            "WH-EAST": 0.40,  # Newark - B2B heavy
            "WH-CENTRAL": 0.35,  # Chicago - Balanced
            "WH-WEST": 0.25,  # LA - Retail heavy
        }

    def _define_external_events(self) -> pd.DataFrame:
        """Define external events affecting demand"""
        events = [
            # Product launches
            {
                "date": "2023-09-15",
                "type": "Product-Launch",
                "category": "Tablets",
                "multiplier": 1.4,
                "duration_days": 14,
                "description": "New iPad Pro release",
            },
            {
                "date": "2024-09-10",
                "type": "Product-Launch",
                "category": "Laptops",
                "multiplier": 1.5,
                "duration_days": 21,
                "description": "New MacBook launch",
            },
            # Black Friday
            {
                "date": "2023-11-24",
                "type": "Black-Friday",
                "category": "ALL",
                "multiplier": 2.5,
                "duration_days": 4,
                "description": "Black Friday weekend",
            },
            {
                "date": "2024-11-29",
                "type": "Black-Friday",
                "category": "ALL",
                "multiplier": 2.3,
                "duration_days": 4,
                "description": "Black Friday weekend",
            },
            # Cyber Monday
            {
                "date": "2023-11-27",
                "type": "Cyber-Monday",
                "category": "Laptops,Tablets,Monitors",
                "multiplier": 2.0,
                "duration_days": 1,
                "description": "Cyber Monday",
            },
            {
                "date": "2024-12-02",
                "type": "Cyber-Monday",
                "category": "Laptops,Tablets,Monitors",
                "multiplier": 1.9,
                "duration_days": 1,
                "description": "Cyber Monday",
            },
            # Post-holiday slump
            {
                "date": "2023-12-26",
                "type": "Post-Holiday",
                "category": "ALL",
                "multiplier": 0.4,
                "duration_days": 10,
                "description": "Post-Christmas slowdown",
            },
            {
                "date": "2024-12-26",
                "type": "Post-Holiday",
                "category": "ALL",
                "multiplier": 0.4,
                "duration_days": 10,
                "description": "Post-Christmas slowdown",
            },
            # Supply disruptions
            {
                "date": "2024-03-10",
                "type": "Supply-Disruption",
                "category": "Laptops",
                "multiplier": 0.65,
                "duration_days": 21,
                "description": "Port congestion delays",
            },
            {
                "date": "2024-06-15",
                "type": "Supply-Disruption",
                "category": "Monitors",
                "multiplier": 0.70,
                "duration_days": 14,
                "description": "Factory shutdown",
            },
            # Back to school
            {
                "date": "2023-08-01",
                "type": "Back-to-School",
                "category": "Laptops,Tablets,Laptop-Bags",
                "multiplier": 1.9,
                "duration_days": 45,
                "description": "Back to school season",
            },
            {
                "date": "2024-08-01",
                "type": "Back-to-School",
                "category": "Laptops,Tablets,Laptop-Bags",
                "multiplier": 2.0,
                "duration_days": 45,
                "description": "Back to school season",
            },
            # Price war
            {
                "date": "2024-04-15",
                "type": "Price-War",
                "category": "Keyboards,Mice",
                "multiplier": 1.3,
                "duration_days": 30,
                "description": "Competitor aggressive pricing",
            },
        ]

        return pd.DataFrame(events)

    def _get_event_multiplier(self, date: pd.Timestamp, category: str) -> float:
        """Get demand multiplier from external events"""
        multiplier = 1.0

        for _, event in self.events.iterrows():
            event_start = pd.to_datetime(event["date"])
            event_end = event_start + timedelta(days=event["duration_days"])

            if event_start <= date <= event_end:
                # Check if event applies to this category
                if event["category"] == "ALL" or category in event["category"].split(
                    ","
                ):
                    # Linear decay over event duration
                    days_into_event = (date - event_start).days
                    decay_factor = 1 - (days_into_event / event["duration_days"]) * 0.3
                    multiplier *= event["multiplier"] * decay_factor

        return multiplier

    def _get_seasonal_multiplier(self, date: pd.Timestamp, category: str) -> float:
        """Seasonal patterns by month"""
        month = date.month

        # Base seasonal pattern
        seasonal_base = {
            1: 0.75,  # January (post-holiday)
            2: 0.80,  # February
            3: 0.90,  # March
            4: 0.95,  # April
            5: 1.00,  # May
            6: 0.85,  # June (summer slump)
            7: 0.80,  # July
            8: 1.10,  # August (back-to-school prep)
            9: 1.15,  # September (back-to-school)
            10: 1.05,  # October
            11: 1.40,  # November (Black Friday)
            12: 1.30,  # December (holidays)
        }

        base = seasonal_base[month]

        # Category-specific adjustments
        if category in ["Laptops", "Tablets", "Laptop-Bags"]:
            if month in [8, 9]:
                base *= 1.2

        if category in ["Keyboards", "Mice", "USB-C-Cables"]:
            # More stable year-round
            base = 0.9 + (base - 0.9) * 0.5

        return base

    def _get_dow_multiplier(self, date: pd.Timestamp) -> float:
        """Day of week pattern (B2B focused)"""
        dow = date.dayofweek

        dow_pattern = {
            0: 1.05,  # Monday
            1: 1.10,  # Tuesday (highest)
            2: 1.08,  # Wednesday
            3: 1.06,  # Thursday
            4: 0.95,  # Friday
            5: 0.35,  # Saturday
            6: 0.30,  # Sunday
        }

        return dow_pattern[dow]

    def _get_trend_multiplier(self, date: pd.Timestamp) -> float:
        """YoY growth trend (15% annual)"""
        days_since_start = (date - self.dates[0]).days
        years_elapsed = days_since_start / 365.25
        annual_growth = 0.30

        return (1 + annual_growth) ** years_elapsed

    def _simulate_stockout(self, date: pd.Timestamp, product_id: str) -> float:
        """Simulate occasional stockouts"""
        month = date.month

        # Higher stockout risk during peak season
        if month in [11, 12, 8, 9]:
            stockout_prob = 0.12
        else:
            stockout_prob = 0.05

        if np.random.random() < stockout_prob:
            # Partial stockout (30-70% of demand fulfilled)
            return np.random.uniform(0.3, 0.7)

        return 1.0

    def generate(self) -> pd.DataFrame:
        """Generate complete sales dataset"""
        print("=" * 60)
        print("GENERATING SALES DATA")
        print("=" * 60)
        print(f"Date range: {self.start_date.date()} to {self.end_date.date()}")
        print(f"Products: {len(self.products)}")
        print(f"Days: {len(self.dates)}")
        print("This will take 2-3 minutes...")
        print()

        all_sales = []

        for idx, product in self.products.iterrows():
            if idx % 10 == 0:
                print(f"  Processing product {idx+1}/{len(self.products)}...")

            product_sales = self._generate_product_sales(product)
            all_sales.extend(product_sales)

        df = pd.DataFrame(all_sales)

        # Add derived fields
        df["revenue"] = df["units_sold"] * df["unit_price"]
        df["cost"] = df["units_sold"] * df["unit_cost"]
        df["profit"] = df["revenue"] - df["cost"]

        # Customer type distribution
        df["customer_type"] = np.random.choice(
            ["Retail-Chain", "Small-Business", "Direct-Consumer", "Enterprise"],
            size=len(df),
            p=[0.45, 0.25, 0.20, 0.10],
        )

        # Sort by date
        df = df.sort_values("date").reset_index(drop=True)

        print()
        print("=" * 60)
        print("✅ SALES GENERATION COMPLETE")
        print("=" * 60)
        print(f"Total transactions: {len(df):,}")
        print(f"Total revenue: ${df['revenue'].sum():,.2f}")
        print(f"Total profit: ${df['profit'].sum():,.2f}")
        print(f"Avg daily revenue: ${df.groupby('date')['revenue'].sum().mean():,.2f}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print("=" * 60)

        return df

    def _generate_product_sales(self, product: pd.Series) -> List[Dict]:
        """Generate sales for one product across all dates"""
        sales = []

        base_demand = product["base_demand_daily"]
        category = product["category"]

        for date in self.dates:
            # Combine all multipliers
            seasonal = self._get_seasonal_multiplier(date, category)
            dow = self._get_dow_multiplier(date)
            trend = self._get_trend_multiplier(date)
            event = self._get_event_multiplier(date, category)
            stockout = self._simulate_stockout(date, product["product_id"])

            # Random noise (±20%)
            noise = np.random.normal(1.0, 0.20)

            # Calculate demand
            demand = base_demand * seasonal * dow * trend * event * noise * stockout
            units = max(0, int(np.round(demand)))

            # Only record if there were sales
            if units > 0:
                # Distribute across warehouses
                warehouse_dist = np.random.multinomial(
                    units, list(self.warehouse_weights.values())
                )

                for warehouse_id, wh_units in zip(
                    self.warehouse_weights.keys(), warehouse_dist
                ):
                    if wh_units > 0:
                        sales.append(
                            {
                                "date": date,
                                "product_id": product["product_id"],
                                "warehouse_id": warehouse_id,
                                "units_sold": wh_units,
                                "unit_price": product["unit_price"],
                                "unit_cost": product["unit_cost"],
                            }
                        )

        return sales


def main():
    """Generate sales data"""
    print("\nLoading products...")
    products_df = pd.read_csv("data/raw/products.csv")

    print(f"Loaded {len(products_df)} products")
    print()

    # Generate sales
    generator = SalesGenerator(products_df, seed=42)
    sales_df = generator.generate()

    # Save
    print("\nSaving files...")
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    sales_df.to_csv("data/raw/sales.csv", index=False)
    sales_df.to_parquet("data/raw/sales.parquet", index=False)

    # Save external events
    generator.events.to_csv("data/raw/external_events.csv", index=False)
    generator.events.to_parquet("data/raw/external_events.parquet", index=False)

    print("✅ Saved sales.csv / .parquet")
    print("✅ Saved external_events.csv / .parquet")

    # Summary stats
    print("\n" + "=" * 60)
    print("SALES SUMMARY STATISTICS")
    print("=" * 60)

    print("\nTransactions by warehouse:")
    wh_stats = sales_df.groupby("warehouse_id").agg(
        {"units_sold": "sum", "revenue": "sum"}
    )
    for wh, row in wh_stats.iterrows():
        print(f"  {wh}: {row['units_sold']:,} units, ${row['revenue']:,.2f}")

    print("\nTop 5 products by revenue:")
    top_products = sales_df.groupby("product_id")["revenue"].sum().nlargest(5)
    for prod, rev in top_products.items():
        print(f"  {prod}: ${rev:,.2f}")

    print("\nMonthly revenue trend:")
    sales_df["month"] = pd.to_datetime(sales_df["date"]).dt.to_period("M")
    monthly_rev = sales_df.groupby("month")["revenue"].sum()
    print(f"  First month (2023-01): ${monthly_rev.iloc[0]:,.2f}")
    print(f"  Last month (2024-12): ${monthly_rev.iloc[-1]:,.2f}")
    print(f"  Peak month: {monthly_rev.idxmax()} with ${monthly_rev.max():,.2f}")
    print(f"  Lowest month: {monthly_rev.idxmin()} with ${monthly_rev.min():,.2f}")

    print("\n" + "=" * 60)

    return sales_df


if __name__ == "__main__":
    main()
