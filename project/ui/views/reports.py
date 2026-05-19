from __future__ import annotations

from dataclasses import dataclass

from project.cli_support import load_json
from project.data.repository import DataRepository
from project.learning.engine import analyze_hypothesis_performance


@dataclass(frozen=True)
class BacktestRowView:
    hypothesis_id: str
    asset_id: str
    total_trades: int
    total_return_pct: float
    sharpe_ratio: float
    research_run_id: str | None


@dataclass(frozen=True)
class PerformanceRowView:
    hypothesis_id: str
    trades: int
    total_pnl: float
    average_pnl: float


@dataclass(frozen=True)
class RejectedRowView:
    evaluation_id: str
    hypothesis_id: str
    asset_id: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ReportsPageView:
    backtests: tuple[BacktestRowView, ...]
    performance: tuple[PerformanceRowView, ...]
    rejected: tuple[RejectedRowView, ...]
    debug_payload: dict[str, object]


def get_reports_page_view(repository: DataRepository) -> ReportsPageView:
    backtests = repository.get_backtest_results()
    rejected = tuple(_rejected_rows(repository))
    performance = tuple(_performance_rows(repository))
    return ReportsPageView(
        backtests=tuple(
            BacktestRowView(
                backtest.hypothesis_id,
                backtest.asset_id,
                backtest.total_trades,
                backtest.total_return_pct,
                backtest.sharpe_ratio,
                backtest.research_run_id,
            )
            for backtest in backtests
        ),
        performance=performance,
        rejected=rejected,
        debug_payload={
            "backtests": [backtest.__dict__ for backtest in backtests],
            "rejected": [row.__dict__ for row in rejected],
        },
    )


def _performance_rows(repository: DataRepository) -> tuple[PerformanceRowView, ...]:
    summary = analyze_hypothesis_performance(repository.get_trade_outcomes())
    return tuple(
        PerformanceRowView(
            hypothesis_id=hypothesis_id,
            trades=int(values["trades"]),
            total_pnl=float(values["total_pnl"]),
            average_pnl=float(values["average_pnl"]),
        )
        for hypothesis_id, values in summary.items()
    )


def _rejected_rows(repository: DataRepository) -> list[RejectedRowView]:
    rejected: list[RejectedRowView] = []
    for evaluation in repository.get_hypothesis_evaluations():
        payload = load_json(evaluation.validation_result_json)
        if payload and not payload.get("is_valid", True):
            rejected.append(
                RejectedRowView(
                    evaluation.evaluation_id,
                    evaluation.hypothesis_id,
                    evaluation.asset_id,
                    tuple(str(reason) for reason in payload.get("reasons", ())),
                )
            )
    return rejected

