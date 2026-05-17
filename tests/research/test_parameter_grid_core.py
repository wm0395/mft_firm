from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

from project.data.db import DuckDBAccess
from project.data.loader import load_ohlcv_csv
from project.data.repository import DataRepository
from project.common.models import ResearchUniverse, DatasetSnapshot
from project.research.config import load_research_config, research_config_hash
from project.research.metrics import compute_metrics
from project.research.parameter_grid import expand_parameter_sets, parameter_set_hash
from project.research.promotion import PromotionCandidate, PromotionRules, validate_promotion
from project.research.runner import run_research


def test_research_config_parsing_and_hash_determinism() -> None:
    config_a = load_research_config(
        {
            "strategy_family": "momentum_continuation",
            "asset_symbol": "nifty",
            "start_date": "2026-04-20",
            "end_date": "2026-04-25",
            "parameter_grid": {
                "lookback_bars": [3, 5],
                "entry_threshold": [0.005],
                "exit_threshold": [0.0],
                "holding_bars": [2],
            },
            "promotion": {
                "minimum_total_trades": 1,
                "minimum_win_rate": 0.5,
                "minimum_total_return_pct": -10.0,
                "maximum_drawdown_pct": 100.0,
            },
        }
    )
    config_b = load_research_config(
        json.dumps(
            {
                "end_date": "2026-04-25",
                "asset_symbol": "NIFTY",
                "strategy_family": "momentum_continuation",
                "start_date": "2026-04-20",
                "promotion": {
                    "maximum_drawdown_pct": 100.0,
                    "minimum_total_return_pct": -10.0,
                    "minimum_win_rate": 0.5,
                    "minimum_total_trades": 1,
                },
                "parameter_grid": {
                    "holding_bars": [2],
                    "exit_threshold": [0.0],
                    "entry_threshold": [0.005],
                    "lookback_bars": [3, 5],
                },
            }
        )
    )

    sets_a = expand_parameter_sets(config_a.strategy_family, config_a.parameter_axes)
    sets_b = expand_parameter_sets(config_b.strategy_family, config_b.parameter_axes)

    assert config_a.asset_symbol == "NIFTY"
    assert config_a.strategy_family == "momentum_continuation"
    assert research_config_hash(config_a) == research_config_hash(config_b)
    assert [item.parameter_set_hash for item in sets_a] == [item.parameter_set_hash for item in sets_b]
    assert parameter_set_hash(
        "momentum_continuation",
        (("entry_threshold", 0.005), ("lookback_bars", 3)),
    ) == parameter_set_hash(
        "momentum_continuation",
        (("lookback_bars", 3), ("entry_threshold", 0.005)),
    )


def test_research_metrics_handle_empty_and_single_trade() -> None:
    empty = compute_metrics(())
    single = compute_metrics((5.0,))

    assert empty.trade_count == 0
    assert empty.win_rate == 0.0
    assert empty.total_return_pct == 0.0
    assert empty.sharpe_like_score == 0.0
    assert single.trade_count == 1
    assert single.winning_trades == 1
    assert single.win_rate == 1.0
    assert single.total_return_pct == 5.0
    assert single.volatility_pct == 0.0
    assert single.max_drawdown_pct == 0.0


def test_research_runner_writes_manifest_and_artifacts(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    fixture_path = Path("tests/fixtures/market_data/NIFTY.csv")
    load_ohlcv_csv(fixture_path, "NIFTY", repository)
    asset = repository.list_assets()[0]
    snapshot = _snapshot(repository, asset.asset_id)
    config = load_research_config(
        {
            "strategy_family": "mean_reversion",
            "asset_symbol": "NIFTY",
            "dataset_snapshot_id": snapshot.dataset_snapshot_id,
            "start_date": "2026-04-20",
            "end_date": "2026-05-14",
            "parameter_grid": {
                "lookback_bars": [5, 10],
                "entry_zscore": [0.75],
                "exit_zscore": [0.25],
                "holding_bars": [2, 4],
            },
            "promotion": {
                "minimum_total_trades": 1,
                "minimum_win_rate": 0.0,
                "minimum_total_return_pct": -100.0,
                "maximum_drawdown_pct": 1000.0,
            },
        }
    )

    outcome = run_research(repository, config, tmp_path / "artifacts")
    manifest_path = Path(outcome.artifact_manifest.manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert outcome.best_evaluation is not None
    assert len(outcome.evaluations) == 4
    assert manifest["config_hash"] == outcome.config_hash
    assert manifest["best_parameter_set_hash"] == outcome.best_evaluation.parameter_set.parameter_set_hash
    assert {item["name"] for item in manifest["files"]} == {
        "drawdown_curve.png",
        "equity_curve.png",
        "parameter_grid_results.csv",
        "parameter_grid_summary.md",
        "parameter_comparison.png",
        "trade_pnl_distribution.png",
    }
    assert all(Path(item["path"]).exists() for item in manifest["files"])
    assert (tmp_path / "artifacts" / "parameter_grid_results.csv").exists()
    assert (tmp_path / "artifacts" / "parameter_grid_summary.md").exists()
    assert (tmp_path / "artifacts" / "equity_curve.png").exists()
    assert (tmp_path / "artifacts" / "drawdown_curve.png").exists()
    assert (tmp_path / "artifacts" / "parameter_comparison.png").exists()
    assert (tmp_path / "artifacts" / "trade_pnl_distribution.png").exists()


def test_research_run_config_loads_example_workflow() -> None:
    from project.research.config import load_research_run_config

    config = load_research_run_config(
        Path("research/examples/nifty50_two_strategy_research/configs/research_run.yaml")
    )

    assert config.research_project_id == "research_project:nifty50_two_strategy_research"
    assert config.dataset_snapshot_id == "dataset_snapshot:csv:NIFTY.csv:1d:69f1606d573e"
    assert config.strategy_grid_paths == (
        "momentum_continuation_grid.yaml",
        "mean_reversion_grid.yaml",
    )


def test_promotion_validation_reports_blockers() -> None:
    rules = PromotionRules(
        minimum_total_trades=2,
        minimum_win_rate=0.5,
        minimum_total_return_pct=1.0,
        maximum_drawdown_pct=5.0,
        minimum_sharpe_like_score=0.0,
    )
    candidate = PromotionCandidate(
        strategy_family="momentum_continuation",
        parameter_set_hash="abc123",
        metrics=compute_metrics((2.0,)),
    )

    validation = validate_promotion(candidate, rules)
    blocked = validate_promotion(None, rules)

    assert validation.eligible is False
    assert "insufficient_trades" in validation.reasons
    assert blocked.eligible is False
    assert blocked.reasons == ("missing_candidate",)


def _repository(tmp_path: Path) -> DataRepository:
    db = DuckDBAccess(tmp_path / "mft.duckdb")
    repository = DataRepository(db)
    repository.initialize()
    return repository


def _snapshot(repository: DataRepository, asset_id: str) -> DatasetSnapshot:
    universe = ResearchUniverse(
        universe_id="research_universe:fixture:daily",
        name="Fixture Universe",
        market="NSE",
        description="Fixture-driven research universe",
        asset_ids=(asset_id,),
    )
    snapshot = DatasetSnapshot(
        dataset_snapshot_id="dataset_snapshot:fixture:2026-04-20:2026-05-14",
        universe_id=universe.universe_id,
        captured_at=datetime(2026, 5, 14, tzinfo=UTC).isoformat(),
        data_start="2026-04-20T00:00:00+00:00",
        data_end="2026-05-14T23:59:59+00:00",
        asset_ids=(asset_id,),
    )
    repository.persist_research_artifact(universe)
    repository.persist_research_artifact(snapshot)
    return snapshot
