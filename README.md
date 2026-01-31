# Supply Chain Agentic AI Optimizer

**Multi-agent AI system that optimizes inventory management and procurement decisions for B2B electronics distribution.**

## 🎯 Project Overview

This project demonstrates how agentic AI can transform supply chain operations by replacing simple rule-based systems with intelligent, context-aware decision-making agents.

### The Challenge

Traditional inventory management relies on simple reorder point logic:
- **IF** inventory ≤ reorder point **THEN** place order
- No forecasting, no event awareness, no optimization
- Results in stockouts, excess inventory, and missed savings

### Our Solution

Multi-agent system with specialized agents:
- **Demand Forecaster Agent**: Predicts demand using seasonality, trends, and external events
- **Inventory Analyzer Agent**: Evaluates current state and risk levels
- **Supplier Coordinator Agent**: Optimizes supplier selection and order timing
- **Orchestrator**: Coordinates agents and makes final decisions

## 📊 Dataset

**Realistic synthetic data** for "TechGear Distribution Co." (B2B electronics):

- **Products**: 50 SKUs across 8 categories (Laptops, Tablets, Monitors, Accessories)
- **Timeframe**: 2 years (2023-2024), 731 days
- **Sales**: 92,535 transactions with realistic patterns:
  - Seasonality (Black Friday, Back-to-School, Summer slump)
  - Day-of-week patterns (B2B = weekdays high, weekends low)
  - 15% YoY growth trend
  - External events (product launches, supply disruptions)
- **Suppliers**: 3 suppliers with different characteristics:
  - SUP-A: Premium, reliable (94%), 14-day lead time, Net-60 terms
  - SUP-B: Fast, less reliable (88%), 7-day lead time, Net-30 terms
  - SUP-C: Bulk, very reliable (97%), 21-day lead time, Net-90 terms
- **Warehouses**: 3 locations (Newark, Chicago, LA) with capacity constraints

## 🎯 Baseline Performance

**Simple Reorder Point System (what we're beating):**

| Metric | Value |
|--------|-------|
| Total Orders | 1,098 |
| Total Procurement | $43.3M |
| Stockout Rate | 1.59% |
| Lost Revenue | $3.3M |
| Volume Discount Capture | 55.7% |
| On-Time Delivery | ~92% |

## 🚀 Agentic System Goals

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| Stockout Rate | 1.59% | < 1.0% | -37% |
| Procurement Costs | $43.3M | $39M | -10% ($4.3M saved) |
| Lost Revenue | $3.3M | < $1M | +$2.3M captured |
| Discount Capture | 55.7% | > 65% | +9.3pp |

**Total Value Creation Target: ~$6.6M** (savings + revenue capture)

## 🏗️ Project Structure
```
supply-chain-agent/
├── data/
│   ├── raw/                    # Generated CSV/Parquet files
│   │   ├── products.csv
│   │   ├── suppliers.csv
│   │   ├── warehouses.csv
│   │   ├── sales.csv           # 92K transactions
│   │   ├── inventory_snapshots.csv  # 110K daily snapshots
│   │   ├── purchase_orders.csv      # 1,098 baseline orders
│   │   └── external_events.csv
│   └── processed/
│       ├── supply_chain.duckdb      # DuckDB database
│       └── baseline_metrics.json    # Baseline performance
├── src/
│   ├── data_generation/        # Synthetic data generators
│   ├── baseline/               # Simple reorder point system
│   ├── agents/                 # Multi-agent AI system (Week 3-4)
│   ├── simulation/             # Replay & testing framework
│   └── utils/                  # Database, metrics, helpers
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_baseline_analysis.ipynb
│   └── 03_agent_comparison.ipynb
├── tests/                      # Unit tests
└── app/                        # Streamlit dashboard (Week 5)
```

## 🛠️ Tech Stack

### Data & Infrastructure
- **pandas, numpy**: Data manipulation
- **DuckDB**: Fast analytical queries
- **plotly**: Interactive visualizations

### AI & Agents (Week 3+)
- **LangChain / LangGraph**: Agent orchestration
- **OpenAI / Anthropic**: LLMs for decision-making
- **Instructor**: Structured outputs
- **Pydantic**: Data validation

### Deployment (Week 5)
- **Streamlit**: Interactive dashboard
- **Docker**: Containerization (optional)

## 🚀 Getting Started

### 1. Setup Environment
```bash
# Clone repository
git clone <your-repo>
cd supply-chain-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Data
```bash
# Option A: Generate all data at once (6-8 minutes)
python -m src.data_generation.orchestrator

# Option B: Generate step-by-step
python -m src.data_generation.generate_products
python -m src.data_generation.generate_suppliers
python -m src.data_generation.generate_warehouses
python -m src.data_generation.generate_sales
python -m src.data_generation.generate_inventory_and_orders
```

### 3. Setup Database
```bash
python -m src.utils.db
```

### 4. Explore Data
```bash
jupyter notebook notebooks/01_data_exploration.ipynb
```

## 📈 Development Roadmap

### ✅ Week 1: Data Foundation (COMPLETE)
- [x] Synthetic data generation
- [x] Baseline system simulation
- [x] Database setup
- [x] Data validation

### 🔄 Week 2: Analysis & Framework (Current)
- [ ] Baseline performance analysis
- [ ] Problem scenario documentation
- [ ] Simulation framework
- [ ] Metrics system

### 🎯 Week 3: Agent Development
- [ ] Demand Forecaster Agent
- [ ] Inventory Analyzer Agent
- [ ] Supplier Coordinator Agent
- [ ] Agent orchestration

### 📊 Week 4: Optimization & Testing
- [ ] A/B testing vs baseline
- [ ] Performance tuning
- [ ] Edge case handling
- [ ] Documentation

### 🎨 Week 5: Dashboard & Presentation
- [ ] Streamlit dashboard
- [ ] Real-time simulation
- [ ] Comparison visualizations
- [ ] Final documentation

## 💡 Key Insights from McKinsey Report

This project implements best practices from **"The State of AI: How Organizations are Rewiring to Capture Value" (March 2025)**:

1. **CEO Oversight** → System tracks KPIs that matter to leadership (EBIT impact)
2. **Workflow Redesign** → Fundamentally redesigning procurement process (not just automation)
3. **Risk Mitigation** → Addresses stockout, cost overrun, and supplier reliability risks
4. **Adoption Best Practices** → Clear KPIs, road map, change story
5. **Human-in-the-Loop** → Agent recommendations reviewed before execution

## 📊 Metrics Tracked

### Operational
- Stockout rate & incidents
- Inventory turnover
- Order frequency & size
- Lead time variance

### Financial
- Total procurement spend
- Shipping costs
- Volume discount capture
- Lost revenue from stockouts
- Working capital requirements

### Supplier Performance
- On-time delivery rate
- Lead time accuracy
- Reliability score
- Cost per unit

## 🔬 Validation & Testing

### Data Quality Checks
- ✅ No negative inventory
- ✅ Seasonality validation (Nov-Dec spike)
- ✅ Growth trend (15% YoY)
- ✅ Supplier reliability matches expectations
- ✅ Stockout rate realistic (1-10%)

### Agent Testing (Week 4)
- Backtesting on historical data
- A/B testing vs baseline
- Stress testing (supply disruptions)
- Edge case scenarios

## 📚 Documentation

- **Data Dictionary**: `data/README.md`
- **API Documentation**: Coming in Week 3
- **Agent Architecture**: Coming in Week 3
- **Deployment Guide**: Coming in Week 5

## 🤝 Contributing

This is a portfolio/learning project. Feedback welcome!

## 📝 License

MIT License - Feel free to use for learning/portfolio

## 👤 Author

**Oscar** - Data Engineer → AI Engineer transition project

Demonstrating:
- Production-grade data engineering
- System design & architecture
- AI/ML application development
- Business impact measurement

---

**Status**: Week 1 Complete ✅ | Week 2 In Progress 🔄

**Next Milestone**: Baseline analysis & problem scenario documentation