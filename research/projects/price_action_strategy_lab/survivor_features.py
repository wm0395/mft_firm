from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel


@dataclass(frozen=True)
class SurvivorFeatureFrames:
    volatility_expansion_value: pd.Series
    support_trendline_alpha_score: pd.DataFrame
    stock_vol20: pd.DataFrame
    stock_vol60: pd.DataFrame
    market_breadth: pd.Series
    gap_size: pd.DataFrame
    volume_shock: pd.DataFrame
    relative_strength: pd.DataFrame
    sector: pd.Series
    feature_table: pd.DataFrame


def build_survivor_features(
    panel: Alpha101Panel,
    signal: pd.DataFrame,
    intensity: pd.Series,
) -> SurvivorFeatureFrames:
    returns = panel.close.pct_change(fill_method=None)
    ret20 = panel.close.pct_change(20, fill_method=None)
    frames = {
        "support_trendline_alpha_score": signal,
        "stock_vol20": returns.rolling(20).std(),
        "stock_vol60": returns.rolling(60).std(),
        "gap_size": panel.open.div(panel.close.shift(1)).sub(1.0),
        "volume_shock": panel.volume.div(panel.volume.rolling(20).mean()).sub(1.0),
        "relative_strength": ret20.sub(ret20.mean(axis=1), axis=0),
    }
    return SurvivorFeatureFrames(
        volatility_expansion_value=intensity,
        support_trendline_alpha_score=frames["support_trendline_alpha_score"],
        stock_vol20=frames["stock_vol20"],
        stock_vol60=frames["stock_vol60"],
        market_breadth=returns.gt(0.0).mean(axis=1),
        gap_size=frames["gap_size"],
        volume_shock=frames["volume_shock"],
        relative_strength=frames["relative_strength"],
        sector=panel.industry.astype(str),
        feature_table=_feature_table(frames),
    )


def trade_feature_rows(
    positions: pd.DataFrame,
    future: pd.DataFrame,
    multiplier: pd.Series,
    features: SurvivorFeatureFrames,
    horizon: int,
) -> pd.DataFrame:
    base = positions.mul(future.reindex_like(positions).fillna(0.0)).div(float(horizon))
    scaled = base.mul(multiplier.reindex(base.index).fillna(1.0), axis=0)
    active = positions.ne(0.0) & base.ne(0.0)
    rows = _base_trade_frame(base.where(active), scaled.where(active), multiplier)
    return _attach_features(rows, features) if not rows.empty else rows


def saved_loser_lost_winner_summary(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame()
    groups = {"saved_loser": _saved_loser(rows), "lost_winner": _lost_winner(rows)}
    return pd.DataFrame([_summary_row(name, rows.loc[mask]) for name, mask in groups.items()])


def blocker_value_row(rows: pd.DataFrame) -> dict[str, float | int]:
    if rows.empty:
        return _empty_value_row()
    values = _value_fields(rows)
    values["net_blocker_value"] = _net_value(values)
    counts = rows["classification"].value_counts().to_dict()
    return {**{key: int(counts.get(key, 0)) for key in _classifications()}, **values}


def _base_trade_frame(base: pd.DataFrame, scaled: pd.DataFrame, multiplier: pd.Series) -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "baseline_trade_return": _stack(base).dropna(),
            "throttle_trade_return": _stack(scaled).dropna(),
        }
    )
    if frame.empty:
        return frame
    frame.index.names = ["date", "symbol"]
    frame = frame.reset_index()
    frame["multiplier"] = frame["date"].map(multiplier)
    frame["classification"] = _classify(frame["baseline_trade_return"], frame["multiplier"])
    frame["blocker_value"] = frame["throttle_trade_return"] - frame["baseline_trade_return"]
    return frame


def _attach_features(rows: pd.DataFrame, features: SurvivorFeatureFrames) -> pd.DataFrame:
    out = rows.copy()
    out["volatility_expansion_value"] = out["date"].map(features.volatility_expansion_value)
    out["market_breadth"] = out["date"].map(features.market_breadth)
    out["sector"] = out["symbol"].map(features.sector).fillna("unknown")
    index = pd.MultiIndex.from_frame(out[["date", "symbol"]])
    for column in features.feature_table.columns:
        out[column] = features.feature_table[column].reindex(index).to_numpy()
    return out


def _feature_table(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.concat([_stack(frame).rename(name) for name, frame in frames.items()], axis=1)


def _stack(frame: pd.DataFrame) -> pd.Series:
    return frame.stack(future_stack=True)


def _classify(base: pd.Series, multiplier: pd.Series) -> np.ndarray:
    winner = base.gt(0.0)
    loser = base.lt(0.0)
    choices = _classifications()
    masks = (
        multiplier.eq(1.0) & winner,
        multiplier.eq(1.0) & loser,
        multiplier.gt(0.0) & multiplier.lt(1.0) & winner,
        multiplier.gt(0.0) & multiplier.lt(1.0) & loser,
        multiplier.gt(1.0) & winner,
        multiplier.gt(1.0) & loser,
    )
    return np.select(masks, choices, default="other")


def _value_fields(rows: pd.DataFrame) -> dict[str, float]:
    base = rows["baseline_trade_return"]
    scaled = rows["throttle_trade_return"]
    cls = rows["classification"]
    return {
        "accepted_winner_pnl": _sum(scaled.where(cls.eq("accepted_winner"))),
        "accepted_loser_pnl": _sum(scaled.where(cls.eq("accepted_loser"))),
        "loss_reduced_from_reduced_losers": _sum((scaled - base).where(cls.eq("reduced_loser"))),
        "profit_reduced_from_reduced_winners": _sum((base - scaled).where(cls.eq("reduced_winner"))),
        "profit_added_from_increased_winners": _sum((scaled - base).where(cls.eq("increased_winner"))),
        "loss_added_from_increased_losers": _sum((base - scaled).where(cls.eq("increased_loser"))),
    }


def _summary_row(group: str, frame: pd.DataFrame) -> dict[str, float | int | str]:
    row: dict[str, float | int | str] = {"group": group, "count": int(len(frame))}
    row["total_blocker_value_pct"] = float(frame["blocker_value"].sum() * 100.0) if not frame.empty else 0.0
    for column in _summary_features():
        row[f"{column}_mean"] = float(pd.to_numeric(frame.get(column), errors="coerce").mean()) if not frame.empty else 0.0
    return row


def _net_value(values: dict[str, float]) -> float:
    return (
        values["loss_reduced_from_reduced_losers"]
        - values["profit_reduced_from_reduced_winners"]
        + values["profit_added_from_increased_winners"]
        - values["loss_added_from_increased_losers"]
    )


def _saved_loser(rows: pd.DataFrame) -> pd.Series:
    return rows["baseline_trade_return"].lt(0.0) & rows["blocker_value"].gt(0.0)


def _lost_winner(rows: pd.DataFrame) -> pd.Series:
    return rows["baseline_trade_return"].gt(0.0) & rows["blocker_value"].lt(0.0)


def _sum(series: pd.Series) -> float:
    return float(series.fillna(0.0).sum() * 100.0)


def _empty_value_row() -> dict[str, float | int]:
    return {**{key: 0 for key in _classifications()}, **{key: 0.0 for key in _value_keys()}}


def _classifications() -> tuple[str, ...]:
    return ("accepted_winner", "accepted_loser", "reduced_winner", "reduced_loser", "increased_winner", "increased_loser")


def _value_keys() -> tuple[str, ...]:
    return (
        "accepted_winner_pnl",
        "accepted_loser_pnl",
        "loss_reduced_from_reduced_losers",
        "profit_reduced_from_reduced_winners",
        "profit_added_from_increased_winners",
        "loss_added_from_increased_losers",
        "net_blocker_value",
    )


def _matrix_features() -> tuple[str, ...]:
    return ("support_trendline_alpha_score", "stock_vol20", "stock_vol60", "gap_size", "volume_shock", "relative_strength")


def _summary_features() -> tuple[str, ...]:
    return ("volatility_expansion_value", *_matrix_features(), "market_breadth")
