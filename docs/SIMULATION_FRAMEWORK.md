# Simulation Framework Documentation

**Version**: 1.0  
**Last Updated**: January 31, 2026

## Overview

The simulation framework enables **controlled A/B testing** of different supply chain strategies by replaying historical sales data.

## Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    SIMULATION ENGINE                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Historical Sales Data (92,535 transactions)                 │
│           ↓                                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │  SupplyChainSimulator                         │           │
│  │  • Processes sales day-by-day                 │           │
│  │  • Executes ordering strategy                 │           │
│  │  • Tracks inventory, costs, stockouts         │           │
│  └──────────────────────────────────────────────┘           │
│           ↓                                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │  Ordering Strategy (pluggable)                │           │
│  │  • baseline_reorder_point_strategy            │           │
│  │  • agent_strategy (Week 3)                    │           │
│  │  • custom strategies...                       │           │
│  └──────────────────────────────────────────────┘           │
│           ↓                                                   │
│  ┌──────────────────────────────────────────────┐           │
│  │  Metrics Calculator                           │           │
│  │  • Financial metrics                          │           │
│  │  • Procurement metrics                        │           │
│  │  • Inventory metrics                          │           │
│  │  • Comparison analysis                        │           │
│  └──────────────────────────────────────────────┘           │
│           ↓                                                   │
│  Results: State, Metrics, Orders                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. SupplyChainSimulator

**File**: `src/simulation/simulator.py`

**Purpose**: Core simulation engine that replays sales and executes strategies.

**Key Methods**:
- `initialize_inventory()`: Sets up starting state
- `run(ordering_strategy)`: Executes simulation with given strategy
- `_process_arrivals()`: Handles incoming orders
- `_process_sales()`: Deducts sales from inventory, tracks lost sales
- `_place_order()`: Executes order decision

**Configuration** (`SimulationConfig`):
```python
@dataclass
class SimulationConfig:
    start_date: str                      # '2023-01-01'
    end_date: str                        # '2024-12-31'
    initial_inventory_multiplier: float  # 1.0 = normal
    random_seed: int                     # 42 for reproducibility
    enable_stockout_penalty: bool        # True
    enable_holding_cost: bool            # True
```

### 2. Ordering Strategy Interface

**Signature**:
```python
def strategy_name(
    state: SimulationState,
    products: pd.DataFrame
) -> List[OrderDecision]:
    """
    Decides what orders to place on given day
    
    Args:
        state: Current simulation state (inventory, costs, etc)
        products: Product catalog with specs
    
    Returns:
        List of OrderDecision objects
    """
    decisions = []
    # Your logic here
    return decisions
```

**OrderDecision**:
```python
@dataclass
class OrderDecision:
    date: datetime
    product_id: str
    warehouse_id: str
    supplier_id: str
    units_ordered: int
    reason: str              # Human-readable explanation
    metadata: Dict           # Additional context (forecast, urgency, etc)
```

### 3. MetricsCalculator

**File**: `src/simulation/metrics.py`

**Purpose**: Calculates comprehensive KPIs from simulation results.

**Metrics Tracked**:

#### Financial
- Total revenue
- Total cost
- Total profit
- Profit margin %

#### Lost Sales
- Total lost sales revenue
- Lost sales % of revenue

#### Procurement
- Total orders
- Average order value
- Total procurement spend
- Total shipping cost

#### Discounts
- Orders with volume discount
- Discount capture rate %
- Total discount savings

#### Inventory
- Average inventory value
- Average inventory units
- Stockout incidents
- Stockout rate %

#### Operations
- Average orders per day

### 4. Comparison Framework

**Method**: `MetricsCalculator.compare(baseline, agent)`

**Output**: Side-by-side comparison with deltas and % improvements

**Example**:
```
BASELINE vs AGENT COMPARISON
======================================================================
Financial:
  Revenue:     $76.8M → $77.2M    +$400K  (+0.52%)  ↑
  Cost:        $41.3M → $38.1M    -$3.2M  (-7.75%)  ↓
  Profit:      $35.5M → $39.1M    +$3.6M  (+10.14%) ↑

Procurement:
  Total Spend: $39.8M → $36.5M    -$3.3M  (-8.29%)  ↓
  Shipping:    $1.45M → $1.20M    -$250K  (-17.24%) ↓
  Discount %:  60.0%  → 72.5%     +12.5pp           ↑

[...]
```

## Baseline Benchmark Results

**Period**: January 1, 2023 - December 31, 2024 (731 days)  
**Strategy**: Simple Reorder Point  
**Sales Replayed**: 92,535 transactions

### Key Metrics

| Category | Metric | Value |
|----------|--------|-------|
| **Financial** | Revenue | $76,765,701 |
| | Cost | $41,261,591 |
| | Profit | $35,504,110 (46.25%) |
| **Procurement** | Total Orders | 997 |
| | Total Spend | $39,807,276 |
| | Avg Order | $39,927 |
| | Shipping | $1,454,315 |
| **Discounts** | Capture Rate | 60.0% |
| | Savings | $1,503,078 |
| **Inventory** | Stockout Rate | 1.19% |
| | Stockout Count | 1,309 |
| | Avg Inv Value | $3,597,503 |
| **Lost Sales** | Lost Revenue | $1,578,701 (2.06%) |

## Usage Examples

### Run Baseline Simulation
```python
from src.simulation import run_baseline_simulation
from src.utils.db import get_db

# Load data
db = get_db()
products = db.query("SELECT * FROM products")
suppliers = db.query("SELECT * FROM suppliers")
warehouses = db.query("SELECT * FROM warehouses")
sales = db.query("SELECT * FROM sales")

# Run
final_state, metrics_df, orders_df = run_baseline_simulation(
    products, suppliers, warehouses, sales,
    start_date='2023-01-01',
    end_date='2024-12-31'
)
```

### Calculate Metrics
```python
from src.simulation import MetricsCalculator

calculator = MetricsCalculator(products, suppliers)
metrics = calculator.calculate(final_state, metrics_df, orders_df)

print(metrics)  # Formatted output
```

### Compare Two Strategies
```python
# Run baseline
baseline_state, baseline_metrics_df, baseline_orders = run_baseline_simulation(...)
baseline_metrics = calculator.calculate(baseline_state, baseline_metrics_df, baseline_orders)

# Run agent (Week 3)
agent_state, agent_metrics_df, agent_orders = simulator.run(agent_strategy)
agent_metrics = calculator.calculate(agent_state, agent_metrics_df, agent_orders)

# Compare
comparison_df = calculator.compare(baseline_metrics, agent_metrics)
print_comparison(comparison_df)
```

### Test Custom Strategy
```python
from src.simulation import SupplyChainSimulator, SimulationConfig, OrderDecision

def my_custom_strategy(state, products):
    decisions = []
    
    for key, inv_data in state.inventory.items():
        product_id, warehouse_id = key
        product = products.loc[product_id]
        
        # Your logic here
        if should_order(inv_data, product):
            decisions.append(OrderDecision(
                date=state.current_date,
                product_id=product_id,
                warehouse_id=warehouse_id,
                supplier_id=select_best_supplier(product),
                units_ordered=optimize_quantity(product, inv_data),
                reason='custom_logic',
                metadata={'urgency': calculate_urgency(inv_data)}
            ))
    
    return decisions

# Run
config = SimulationConfig(start_date='2023-01-01', end_date='2024-12-31')
simulator = SupplyChainSimulator(products, suppliers, warehouses, sales, config)
state, metrics_df, orders_df = simulator.run(my_custom_strategy)
```

## Agent Development Workflow (Week 3)

1. **Develop Agent Logic** in `src/agents/`
2. **Create Strategy Function** that wraps agent decisions
3. **Run Simulation** with agent strategy
4. **Compare Results** vs baseline
5. **Iterate** on agent logic
6. **Repeat** until targets met

## Success Criteria for Agent

Agent must demonstrate improvement in **at least 3 of these 5 areas**:

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| Procurement Cost | $39.8M | <$37M | -7%+ |
| Discount Capture | 60.0% | >70% | +10pp |
| Stockout Rate | 1.19% | <0.8% | -33% |
| Lost Sales | $1.58M | <$1M | -37% |
| Shipping Cost | $1.45M | <$1.2M | -17% |

**Target Total Value**: $4M - $5M improvement

## Files Generated

### Baseline Run
- `data/processed/simulations/baseline_full_metrics.json`
- `data/processed/simulations/baseline_full_daily_metrics.csv`
- `data/processed/simulations/baseline_full_orders.csv`

### Agent Run (Week 3)
- `data/processed/simulations/agent_v1_metrics.json`
- `data/processed/simulations/agent_v1_daily_metrics.csv`
- `data/processed/simulations/agent_v1_orders.csv`

### Comparison
- `data/processed/simulations/baseline_vs_agent_comparison.csv`
- `data/processed/simulations/baseline_vs_agent_comparison.json`

## Testing & Validation

### Unit Tests
```bash
pytest tests/test_simulator.py
pytest tests/test_metrics.py
```

### Integration Tests
```bash
python scripts/test_simulation_framework.py
```

### Reproducibility
All simulations use `random_seed=42` for reproducible results.

## Next Steps

1. ✅ Simulation framework complete
2. ✅ Baseline benchmark established
3. 🔄 **Week 2 Day 3**: Create test scenarios for agents
4. 🎯 **Week 3**: Develop multi-agent system
5. 📊 **Week 4**: Run comprehensive A/B testing

---

**Document Version**: 1.0  
**Maintained By**: Oscar  
**Last Simulation Run**: January 31, 2026
```

---

## 🎯 Week 2 Day 2 - COMPLETE!

**What we accomplished today:**

✅ **Simulation Engine Built**
- Replays historical sales with any strategy
- Tracks inventory, costs, stockouts in real-time
- Supports different ordering strategies

✅ **Metrics Calculator Implemented**
- 20+ KPIs calculated automatically
- Comparison framework for A/B testing
- JSON export for analysis

✅ **Baseline Benchmark Established**
- Full 731-day simulation complete
- 997 orders, $39.8M procurement
- 60% discount capture, 1.19% stockout
- Official benchmark for agent comparison

✅ **Documentation Created**
- SIMULATION_FRAMEWORK.md
- Usage examples
- Success criteria defined

---

## 📊 Critical Numbers to Remember
```
YOUR BASELINE TO BEAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Orders:           997
Procurement:      $39,807,276
Shipping:         $1,454,315
Discount Rate:    60.0%
Stockout Rate:    1.19%
Lost Sales:       $1,578,701
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AGENT MUST ACHIEVE (Week 3-4)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Procurement:      <$37M     (save $2.8M+)
Discount Rate:    >70%      (+10pp)
Stockout Rate:    <0.8%     (-33%)
Lost Sales:       <$1M      (recover $600K)
Shipping:         <$1.2M    (save $250K)

TOTAL VALUE:      $4M - $5M
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
