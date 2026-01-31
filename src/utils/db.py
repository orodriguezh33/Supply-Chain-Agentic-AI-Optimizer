import json
from pathlib import Path

import duckdb
import pandas as pd


class SupplyChainDB:
    """DuckDB wrapper for supply chain data with helper methods"""

    def __init__(self, db_path: str = "data/processed/supply_chain.duckdb"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(db_path)
        print(f"✅ Connected to database: {db_path}")

    def load_from_csv(self, data_dir: str = "data/raw"):
        """Load all CSVs into DuckDB tables"""
        print("\n" + "=" * 60)
        print("LOADING DATA INTO DUCKDB")
        print("=" * 60)

        tables = [
            "products",
            "suppliers",
            "warehouses",
            "sales",
            "inventory_snapshots",
            "purchase_orders",
            "external_events",
        ]

        for table in tables:
            # Intentamos primero con .parquet y luego con .csv
            parquet_path = Path(f"{data_dir}/{table}.parquet")
            csv_path = Path(f"{data_dir}/{table}.csv")

            if parquet_path.exists():
                path = str(parquet_path)
                read_func = f"read_parquet('{path}')"
            elif csv_path.exists():
                path = str(csv_path)
                read_func = f"read_csv_auto('{path}')"
            else:
                print(f"  ⚠️  {table} file not found, skipping...")
                continue

            print(f"  Loading {table}...", end="")

            self.conn.execute(
                f"""
                CREATE OR REPLACE TABLE {table} AS 
                SELECT * FROM {read_func}
            """
            )

            # Usamos count() en lugar de count(*) por consistencia
            count = self.conn.execute(f"SELECT COUNT() FROM {table}").fetchone()[0]
            print(f" {count:>10,} rows")

        print("=" * 60)
        print("✅ All tables loaded successfully")
        print("=" * 60)
        self.print_summary()

    def print_summary(self):
        """Print table summaries"""
        print("\n📊 DATABASE SUMMARY:")
        print("─" * 60)

        tables = self.conn.execute("SHOW TABLES").fetchall()

        for (table_name,) in tables:
            # CORRECCIÓN AQUÍ: Quitamos el COUNT(DISTINCT *) que fallaba
            # Si necesitas filas únicas, es mejor contar una columna clave específica
            count = self.conn.execute(f"SELECT COUNT() FROM {table_name}").fetchone()[0]
            print(f"  {table_name:25s}: {count:>10,} rows")

    def query(self, sql: str) -> pd.DataFrame:
        """Execute SQL and return DataFrame"""
        return self.conn.execute(sql).df()

    def get_baseline_metrics(self) -> dict:
        """Calculate baseline system performance metrics"""
        print("\n📈 CALCULATING BASELINE METRICS...")

        # Stockout metrics
        stockout_rate = self.query(
            """
            SELECT 
                COUNT() FILTER (WHERE stockout = 1) * 100.0 / COUNT() as stockout_pct,
                COUNT() FILTER (WHERE stockout = 1) as stockout_days
            FROM inventory_snapshots
        """
        ).iloc[0]

        # Financial metrics
        financial = self.query(
            """
            SELECT 
                SUM(revenue) as total_revenue,
                SUM(profit) as total_profit,
                AVG(revenue) as avg_transaction_revenue
            FROM sales
        """
        ).iloc[0]

        # Order metrics
        order_metrics = self.query(
            """
            SELECT 
                COUNT() as total_orders,
                SUM(total_cost) as total_procurement,
                AVG(total_cost) as avg_order_value,
                AVG(units_ordered) as avg_order_size,
                SUM(CASE WHEN on_time THEN 1 ELSE 0 END) * 100.0 / COUNT() as on_time_pct,
                SUM(CASE WHEN volume_discount_applied THEN 1 ELSE 0 END) * 100.0 / COUNT() as discount_capture_pct
            FROM purchase_orders
        """
        ).iloc[0]

        # Lost sales estimate
        lost_sales = self.query(
            """
            WITH stockout_products AS (
                SELECT 
                    i.product_id,
                    COUNT() as stockout_days,
                    p.unit_price,
                    p.base_demand_daily
                FROM inventory_snapshots i
                JOIN products p ON i.product_id = p.product_id
                WHERE i.stockout = 1
                GROUP BY i.product_id, p.unit_price, p.base_demand_daily
            )
            SELECT 
                SUM(stockout_days * base_demand_daily * unit_price) as estimated_lost_revenue
            FROM stockout_products
        """
        ).iloc[0]

        metrics = {
            "stockout_rate_pct": float(stockout_rate["stockout_pct"]),
            "stockout_days": int(stockout_rate["stockout_days"]),
            "total_revenue": float(financial["total_revenue"]),
            "total_profit": float(financial["total_profit"]),
            "total_orders": int(order_metrics["total_orders"]),
            "total_procurement": float(order_metrics["total_procurement"]),
            "avg_order_value": float(order_metrics["avg_order_value"]),
            "on_time_pct": float(order_metrics["on_time_pct"]),
            "discount_capture_pct": float(order_metrics["discount_capture_pct"]),
            "estimated_lost_revenue": float(lost_sales["estimated_lost_revenue"]),
        }

        print("\n✅ Baseline metrics calculated:")
        print(f"  Stockout rate: {metrics['stockout_rate_pct']:.2f}%")
        print(f"  Total procurement: ${metrics['total_procurement']:,.2f}")
        print(f"  Lost revenue: ${metrics['estimated_lost_revenue']:,.2f}")
        print(f"  Discount capture: {metrics['discount_capture_pct']:.1f}%")

        return metrics

    def close(self):
        """Close database connection"""
        self.conn.close()
        print("✅ Database connection closed")


def setup_database(data_dir: str = "data/raw") -> SupplyChainDB:
    """Initialize database from CSVs/Parquets"""
    db = SupplyChainDB()
    db.load_from_csv(data_dir)
    return db


def get_reorder_alerts(self) -> pd.DataFrame:
    """Identifica productos cuyo inventario actual está por debajo del punto de reorden"""
    return self.query(
        """
        WITH latest_inventory AS (
            SELECT 
                product_id, 
                warehouse_id,
                on_hand_units,
                ROW_NUMBER() OVER (PARTITION BY product_id, warehouse_id ORDER BY date DESC) as rn
            FROM inventory_snapshots
        )
        SELECT 
            p.product_id,
            p.name,
            p.supplier_id,
            i.warehouse_id,
            i.on_hand_units,
            p.reorder_point_units,
            (p.reorder_point_units - i.on_hand_units) as shortage_units
        FROM latest_inventory i
        JOIN products p ON i.product_id = p.product_id
        WHERE i.rn = 1 
          AND i.on_hand_units < p.reorder_point_units
        ORDER BY shortage_units DESC
    """
    )


def main():
    """Setup and test database"""
    print("\n" + "=" * 60)
    print("SUPPLY CHAIN DATABASE SETUP")
    print("=" * 60)

    db = setup_database()

    # Calculate baseline metrics
    baseline = db.get_baseline_metrics()

    # Save baseline metrics
    baseline_path = Path("data/processed/baseline_metrics.json")
    with open(baseline_path, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"\n✅ Baseline metrics saved to: {baseline_path}")

    # Test query
    print("\n" + "=" * 60)
    print("TESTING QUERIES")
    print("=" * 60)

    top_products = db.query(
        """
        SELECT 
            p.product_id,
            p.name,
            p.category,
            SUM(s.revenue) as total_revenue
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        GROUP BY p.product_id, p.name, p.category
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    )

    print("\n🏆 Top 5 Products by Revenue:")
    print(top_products.to_string(index=False))

    print("\n" + "=" * 60)
    print("✅ DATABASE READY FOR USE")
    print("=" * 60)

    return db


if __name__ == "__main__":
    db = main()
