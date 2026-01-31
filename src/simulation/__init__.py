# src/simulation/__init__.py

"""
Simulation framework for supply chain optimization

Provides tools to replay historical scenarios and compare strategies.
"""

from .simulator import (
    SupplyChainSimulator,
    SimulationConfig,
    OrderDecision,
    SimulationState,
    baseline_reorder_point_strategy,
    run_baseline_simulation
)

from .metrics import (
    PerformanceMetrics,
    MetricsCalculator,
    print_comparison
)

__all__ = [
    'SupplyChainSimulator',
    'SimulationConfig',
    'OrderDecision',
    'SimulationState',
    'baseline_reorder_point_strategy',
    'run_baseline_simulation',
    'PerformanceMetrics',
    'MetricsCalculator',
    'print_comparison'
]
