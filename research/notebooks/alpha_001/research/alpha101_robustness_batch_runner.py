from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd  # type: ignore[import-untyped]

NOTEBOOK_ROOT = Path(__file__).resolve().parents[1]
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))

if __package__:
    from .alpha101_robustness import (  # noqa: E402
        ROBUSTNESS_DIR,
        ROBUSTNESS_REPORT,
        ROBUSTNESS_TABLES,
        candidate_lanes,
        classify_shortlist,
        final_report,
        industry_snapshot_risk,
        proxy_sensitivity,
        run_walk_forward,
        strict_liquidity_primary_report,
        validation_report,
    )
else:  # pragma: no cover
    from alpha101_robustness import (  # noqa: E402
        ROBUSTNESS_DIR,
        ROBUSTNESS_REPORT,
        ROBUSTNESS_TABLES,
        candidate_lanes,
        classify_shortlist,
        final_report,
        industry_snapshot_risk,
        proxy_sensitivity,
        run_walk_forward,
        strict_liquidity_primary_report,
        validation_report,
    )


BATCH_ROOT = ROBUSTNESS_DIR / "_robustness_batches"
BATCH_SIZE = 4
BATCH_TABLES = ("walk_forward", "cost_sensitivity", "universe_sensitivity", "proxy_sensitivity", "industry_snapshot_risk")


def batch_ranges(total: int, size: int) -> list[tuple[int, int]]:
    return [(start, min(total, start + size)) for start in range(0, total, size)]


def final_paths() -> dict[str, Path]:
    return {key: ROBUSTNESS_DIR / name for key, name in ROBUSTNESS_TABLES.items()}


def batch_dir(start: int, end: int) -> Path:
    return BATCH_ROOT / f"robust_{start:03d}_{end:03d}"


def batch_paths(start: int, end: int) -> dict[str, Path]:
    directory = batch_dir(start, end)
    return {name: directory / f"{name}.csv" for name in BATCH_TABLES}


def load_batch_outputs(start: int, end: int) -> dict[str, pd.DataFrame] | None:
    paths = batch_paths(start, end)
    if not all(path.exists() for path in paths.values()):
        return None
    return {name: pd.read_csv(path) for name, path in paths.items()}


def write_batch_outputs(frame: pd.DataFrame, start: int, end: int, progress: bool) -> dict[str, pd.DataFrame]:
    directory = batch_dir(start, end)
    directory.mkdir(parents=True, exist_ok=True)
    if progress:
        print(f"[alpha101 robustness] batch {start}:{end}", flush=True)
    walk_forward, cost_sensitivity, universe_sensitivity = run_walk_forward(frame, progress=progress)
    proxy_report = proxy_sensitivity(frame, progress=progress)
    industry_report = industry_snapshot_risk(frame, progress=progress)
    outputs = {
        "walk_forward": walk_forward,
        "cost_sensitivity": cost_sensitivity,
        "universe_sensitivity": universe_sensitivity,
        "proxy_sensitivity": proxy_report,
        "industry_snapshot_risk": industry_report,
    }
    for name, batch_frame in outputs.items():
        batch_frame.to_csv(directory / f"{name}.csv", index=False)
    return outputs


def load_or_write_batch(frame: pd.DataFrame, start: int, end: int, refresh: bool, progress: bool) -> dict[str, pd.DataFrame]:
    if not refresh:
        cached = load_batch_outputs(start, end)
        if cached is not None:
            return cached
    return write_batch_outputs(frame, start, end, progress)


def build_final_outputs(
    candidate_frame: pd.DataFrame,
    walk_forward: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    universe_sensitivity: pd.DataFrame,
    proxy_report: pd.DataFrame,
    industry_report: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    shortlist = classify_shortlist(candidate_frame, walk_forward, proxy_report)
    strict_liquidity_report = strict_liquidity_primary_report(walk_forward, shortlist)
    validation = validation_report(candidate_frame, walk_forward, shortlist, strict_liquidity_report)
    return {
        "candidate_lanes": candidate_frame,
        "walk_forward": walk_forward,
        "strict_liquidity_primary": strict_liquidity_report,
        "cost_sensitivity": cost_sensitivity,
        "universe_sensitivity": universe_sensitivity,
        "proxy_sensitivity": proxy_report,
        "industry_snapshot_risk": industry_report,
        "validation": validation,
        "shortlist": shortlist,
    }


def write_final_outputs(outputs: dict[str, pd.DataFrame]) -> None:
    paths = final_paths()
    for key, frame in outputs.items():
        frame.to_csv(paths[key], index=False)
    report_path = ROBUSTNESS_DIR / ROBUSTNESS_REPORT
    report_path.write_text(
        final_report(
            outputs["shortlist"],
            outputs["candidate_lanes"],
            outputs["proxy_sensitivity"],
            outputs["industry_snapshot_risk"],
            outputs["strict_liquidity_primary"],
        )
    )


def concat_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def batch_slice_ranges(total: int, size: int, start_batch: int = 0, end_batch: int | None = None) -> list[tuple[int, int]]:
    ranges = batch_ranges(total, size)
    return ranges[start_batch:end_batch]


def run_robustness_batch_slice(
    refresh: bool = False,
    clean_n: int = 12,
    proxy_n: int = 8,
    snapshot_n: int = 8,
    batch_size: int = BATCH_SIZE,
    start_batch: int = 0,
    end_batch: int | None = None,
    progress: bool = True,
) -> dict[str, pd.DataFrame]:
    candidate_frame = candidate_lanes(clean_n=clean_n, proxy_n=proxy_n, snapshot_n=snapshot_n)
    batch_frames: dict[str, list[pd.DataFrame]] = {name: [] for name in BATCH_TABLES}
    for batch_index, (start, end) in enumerate(batch_slice_ranges(len(candidate_frame), batch_size, start_batch, end_batch), start=start_batch):
        if progress:
            print(f"[alpha101 robustness] slice {batch_index} {start}:{end}", flush=True)
        batch_frame = candidate_frame.iloc[start:end].copy()
        cached = load_or_write_batch(batch_frame, start, end, refresh=refresh, progress=progress)
        for name in BATCH_TABLES:
            batch_frames[name].append(cached[name])
    return {name: concat_frames(frames) for name, frames in batch_frames.items()}


def assemble_robustness_outputs(
    clean_n: int = 12,
    proxy_n: int = 8,
    snapshot_n: int = 8,
    batch_size: int = BATCH_SIZE,
    progress: bool = True,
) -> dict[str, pd.DataFrame]:
    candidate_frame = candidate_lanes(clean_n=clean_n, proxy_n=proxy_n, snapshot_n=snapshot_n)
    candidate_frame.to_csv(final_paths()["candidate_lanes"], index=False)
    batch_frames: dict[str, list[pd.DataFrame]] = {name: [] for name in BATCH_TABLES}
    for start, end in batch_ranges(len(candidate_frame), batch_size):
        cached = load_batch_outputs(start, end)
        if cached is None:
            raise FileNotFoundError(f"Missing robustness batch cache: {batch_dir(start, end)}")
        for name in BATCH_TABLES:
            batch_frames[name].append(cached[name])
    outputs = build_final_outputs(
        candidate_frame,
        concat_frames(batch_frames["walk_forward"]),
        concat_frames(batch_frames["cost_sensitivity"]),
        concat_frames(batch_frames["universe_sensitivity"]),
        concat_frames(batch_frames["proxy_sensitivity"]),
        concat_frames(batch_frames["industry_snapshot_risk"]),
    )
    write_final_outputs(outputs)
    if progress:
        print(f"[alpha101 robustness] assembled {len(candidate_frame)} candidates", flush=True)
    return outputs


def run_alpha101_robustness_batches(
    refresh: bool = False,
    clean_n: int = 12,
    proxy_n: int = 8,
    snapshot_n: int = 8,
    batch_size: int = BATCH_SIZE,
    progress: bool = True,
) -> dict[str, pd.DataFrame]:
    ROBUSTNESS_DIR.mkdir(parents=True, exist_ok=True)
    BATCH_ROOT.mkdir(parents=True, exist_ok=True)
    paths = final_paths()
    if not refresh and all(path.exists() for path in paths.values()) and (ROBUSTNESS_DIR / ROBUSTNESS_REPORT).exists():
        return {key: pd.read_csv(path) for key, path in paths.items()}

    candidate_frame = candidate_lanes(clean_n=clean_n, proxy_n=proxy_n, snapshot_n=snapshot_n)
    candidate_frame.to_csv(paths["candidate_lanes"], index=False)

    batch_frames: dict[str, list[pd.DataFrame]] = {name: [] for name in BATCH_TABLES}
    for start, end in batch_ranges(len(candidate_frame), batch_size):
        batch_frame = candidate_frame.iloc[start:end].copy()
        cached = load_or_write_batch(batch_frame, start, end, refresh=refresh, progress=progress)
        for name in BATCH_TABLES:
            batch_frames[name].append(cached[name])

    walk_forward = concat_frames(batch_frames["walk_forward"])
    cost_sensitivity = concat_frames(batch_frames["cost_sensitivity"])
    universe_sensitivity = concat_frames(batch_frames["universe_sensitivity"])
    proxy_report = concat_frames(batch_frames["proxy_sensitivity"])
    industry_report = concat_frames(batch_frames["industry_snapshot_risk"])
    outputs = build_final_outputs(
        candidate_frame,
        walk_forward,
        cost_sensitivity,
        universe_sensitivity,
        proxy_report,
        industry_report,
    )
    write_final_outputs(outputs)
    return outputs


if __name__ == "__main__":
    out = run_alpha101_robustness_batches(refresh=False)
    print({key: value.shape for key, value in out.items()})
    print(out["shortlist"].head(25).to_string(index=False))
