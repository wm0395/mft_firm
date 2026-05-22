from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
import math
from pathlib import Path
from time import sleep
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd  # type: ignore[import-untyped]


ANNUALIZATION = 252
DEFAULT_FETCH_START = "1970-01-01"
REPO_ROOT = Path(__file__).resolve().parents[4]
RESEARCH_ROOT = REPO_ROOT / "research"
ARTIFACT_DIR = RESEARCH_ROOT / "artifacts" / "alpha001_research_to_alpha"
NIFTY500_DATA_DIR = RESEARCH_ROOT / "data" / "nifty500_high_vol"
EXPANDED_DATA_DIR = RESEARCH_ROOT / "data" / "expanded_high_vol_parent"
VOLATILE_INDEX_DIR = NIFTY500_DATA_DIR / "volatile_index_constituents"

NIFTY500_CONSTITUENT_PATH = NIFTY500_DATA_DIR / "nifty500_constituents.csv"
EXPANDED_PARENT_CONSTITUENT_PATH = EXPANDED_DATA_DIR / "expanded_parent_constituents.csv"
NIFTY500_FIELD_FILES = {name: NIFTY500_DATA_DIR / f"{name}.csv" for name in ("open", "high", "low", "close", "adj_close", "volume")}
EXPANDED_FIELD_FILES = {name: EXPANDED_DATA_DIR / f"{name}.csv" for name in ("open", "high", "low", "close", "adj_close", "volume")}
NIFTY500_MASK_PATH = ARTIFACT_DIR / "dynamic_high_vol_universe_mask_top100.csv"
EXPANDED_MASK_PATH = ARTIFACT_DIR / "expanded_high_vol_universe_mask_top100.csv"
NIFTY500_REPORT_PATH = ARTIFACT_DIR / "dynamic_high_vol_universe_report.csv"
EXPANDED_REPORT_PATH = ARTIFACT_DIR / "expanded_high_vol_universe_report.csv"
NIFTY500_DOWNLOAD_REPORT_PATH = ARTIFACT_DIR / "nifty500_download_report.csv"
EXPANDED_DOWNLOAD_REPORT_PATH = ARTIFACT_DIR / "expanded_high_vol_download_report.csv"

BASE_CONSTITUENT_URLS = (
    "https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv",
    "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
)
VOLATILE_INDEX_SPECS = (
    ("nifty_high_beta_50", "NIFTY High Beta 50", ("https://www.niftyindices.com/IndexConstituent/nifty_high_beta50_index.csv", "https://archives.nseindia.com/content/indices/nifty_high_beta50_index.csv")),
    ("nifty_midcap_50", "NIFTY Midcap 50", ("https://www.niftyindices.com/IndexConstituent/ind_niftymidcap50list.csv", "https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv")),
    ("nifty_midcap_150", "NIFTY Midcap 150", ("https://www.niftyindices.com/IndexConstituent/ind_niftymidcap150list.csv", "https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv")),
    ("nifty_smallcap_250", "NIFTY Smallcap 250", ("https://www.niftyindices.com/IndexConstituent/ind_niftysmallcap250list.csv", "https://archives.nseindia.com/content/indices/ind_niftysmallcap250list.csv")),
    ("nifty_it", "NIFTY IT", ("https://www.niftyindices.com/IndexConstituent/ind_niftyitlist.csv", "https://archives.nseindia.com/content/indices/ind_niftyitlist.csv")),
    ("nifty_bank", "NIFTY Bank", ("https://www.niftyindices.com/IndexConstituent/ind_niftybanklist.csv", "https://archives.nseindia.com/content/indices/ind_niftybanklist.csv")),
)
EXPANDED_EXTRA_SPECS = (
    ("nifty_total_market", "NIFTY Total Market", ("https://www.niftyindices.com/IndexConstituent/ind_niftytotalmarket_list.csv", "https://archives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv")),
    ("nifty_microcap_250", "NIFTY Microcap 250", ("https://www.niftyindices.com/IndexConstituent/ind_niftymicrocap250_list.csv", "https://archives.nseindia.com/content/indices/ind_niftymicrocap250_list.csv")),
)


@dataclass(frozen=True)
class IndexSpec:
    slug: str
    name: str
    urls: tuple[str, ...]


@dataclass(frozen=True)
class SourceRebuildSummary:
    nifty500_symbols: int
    expanded_symbols: int
    nifty500_members_latest: int
    expanded_members_latest: int


def _ensure_dirs() -> None:
    for path in (ARTIFACT_DIR, NIFTY500_DATA_DIR, EXPANDED_DATA_DIR, VOLATILE_INDEX_DIR):
        path.mkdir(parents=True, exist_ok=True)


def read_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, index_col=0, parse_dates=True)
    frame.index = pd.to_datetime(frame.index).tz_localize(None)
    return frame.sort_index()


def write_frame(frame: pd.DataFrame | pd.Series, path: Path) -> None:
    target = frame.to_frame() if isinstance(frame, pd.Series) else frame
    target.to_csv(path)


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 Alpha101 rebuild", "Accept": "text/csv,*/*"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except URLError as error:
        raise RuntimeError(f"failed to fetch {url}: {error}") from error


def parse_constituent_csv(text: str, source_url: str) -> pd.DataFrame:
    frame = pd.read_csv(StringIO(text))
    frame.columns = [str(column).strip() for column in frame.columns]
    symbol_col = next((column for column in frame.columns if column.lower() == "symbol"), None)
    if symbol_col is None:
        raise ValueError(f"missing Symbol column in {source_url}")
    frame = frame.copy()
    frame["Symbol"] = frame[symbol_col].astype(str).str.strip().str.upper()
    frame = frame[frame["Symbol"].ne("") & frame["Symbol"].ne("NAN")]
    if "Series" in frame.columns:
        frame = frame[frame["Series"].fillna("EQ").astype(str).str.upper().eq("EQ")]
    frame["YahooTicker"] = frame["Symbol"].map(lambda symbol: f"{symbol}.NS")
    frame["source_url"] = source_url
    return frame.drop_duplicates("Symbol").sort_values("Symbol").reset_index(drop=True)


def load_constituents(spec: IndexSpec, path: Path, refresh: bool) -> pd.DataFrame:
    if path.exists() and not refresh:
        return pd.read_csv(path)
    errors = []
    for url in spec.urls:
        try:
            frame = parse_constituent_csv(fetch_text(url), url)
            frame.to_csv(path, index=False)
            return frame
        except Exception as error:
            errors.append({"url": url, "error": repr(error)})
    pd.DataFrame(errors).to_csv(path.with_name(f"{spec.slug}_fetch_errors.csv"), index=False)
    raise RuntimeError(f"could not fetch constituent CSV for {spec.name}")


def _clean_symbol_frame(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned["Symbol"] = cleaned["Symbol"].astype(str).str.strip().str.upper()
    return cleaned[cleaned["Symbol"].ne("") & cleaned["Symbol"].ne("NAN")]


def build_expanded_parent_constituents(base: pd.DataFrame, extras: dict[str, tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    pieces = []
    base_frame = base.copy()
    base_frame["index_slug"] = "nifty500"
    base_frame["index_name"] = "NIFTY 500"
    pieces.append(base_frame)
    for slug, (index_name, frame) in extras.items():
        indexed = frame.copy()
        indexed["index_slug"] = slug
        indexed["index_name"] = index_name
        pieces.append(indexed)
    expanded = _clean_symbol_frame(pd.concat(pieces, ignore_index=True, sort=False))
    company_col = "Company Name" if "Company Name" in expanded.columns else "company_name"
    industry_col = "Industry" if "Industry" in expanded.columns else "industry"
    grouped = (
        expanded.groupby("Symbol")
        .agg(
            company_name=(company_col, "first"),
            industry=(industry_col, "first"),
            source_indices=("index_name", lambda values: ",".join(sorted({str(value) for value in values}))),
            source_slugs=("index_slug", lambda values: ",".join(sorted({str(value) for value in values}))),
        )
        .reset_index()
        .sort_values("Symbol")
    )
    grouped["YahooTicker"] = grouped["Symbol"].map(lambda symbol: f"{symbol}.NS")
    return grouped


def _yfinance_module() -> Any:
    try:
        import yfinance as yf  # type: ignore[import-untyped]
    except ImportError as error:
        raise RuntimeError("yfinance is required to rebuild the Alpha101 source cache") from error
    return yf


def _extract_yf_field(raw: pd.DataFrame, tickers: list[str], ticker_to_symbol: dict[str, str], field: str) -> pd.DataFrame:
    frames = {}
    for ticker in tickers:
        series = None
        if isinstance(raw.columns, pd.MultiIndex):
            for key in ((ticker, field), (field, ticker)):
                if key in raw.columns:
                    series = raw[key]
                    break
        elif field in raw.columns and len(tickers) == 1:
            series = raw[field]
        if series is not None:
            frames[ticker_to_symbol[ticker]] = pd.to_numeric(series, errors="coerce")
    frame = pd.DataFrame(frames).sort_index()
    if not frame.empty:
        frame.index = pd.to_datetime(frame.index).tz_localize(None)
        frame = frame.loc[~frame.index.duplicated(keep="last")]
    return frame


def _download_chunk(yf: Any, chunk_tickers: list[str], start: str, end: str | None) -> pd.DataFrame:
    return yf.download(tickers=chunk_tickers, start=start, end=end, auto_adjust=False, group_by="ticker", threads=True, progress=False)


def download_ohlcv_panel(
    symbols: list[str],
    data_dir: Path,
    refresh: bool,
    report_path: Path,
    start: str = DEFAULT_FETCH_START,
    end: str | None = None,
    chunk_size: int = 75,
    seed_frames: dict[str, pd.DataFrame] | None = None,
) -> dict[str, pd.DataFrame]:
    cache_ready = all(path.exists() for path in {name: data_dir / f"{name}.csv" for name in ("open", "high", "low", "close", "adj_close", "volume")}.values())
    if cache_ready and not refresh:
        return {name: read_frame(data_dir / f"{name}.csv") for name in ("open", "high", "low", "close", "adj_close", "volume")}
    yf = _yfinance_module()
    seed_frames = seed_frames or {}
    existing = set(seed_frames.get("adj_close", pd.DataFrame()).columns)
    missing = [symbol for symbol in symbols if symbol not in existing]
    parts: dict[str, list[pd.DataFrame]] = {name: [] for name in ("open", "high", "low", "close", "adj_close", "volume")}
    for name, frame in seed_frames.items():
        if name in parts:
            parts[name].append(frame.reindex(columns=[symbol for symbol in symbols if symbol in existing]))
    report_rows = []
    for symbol in symbols:
        if symbol not in existing:
            continue
        close_frame = seed_frames.get("close", pd.DataFrame())
        close_rows = int(close_frame.get(symbol, pd.Series(dtype=float)).notna().sum()) if symbol in close_frame else 0
        report_rows.append({"symbol": symbol, "ticker": f"{symbol}.NS", "source": "seed_cache", "status": "ok", "close_rows": close_rows, "error": ""})
    ticker_map = {f"{symbol}.NS": symbol for symbol in missing}
    for start_at in range(0, len(missing), chunk_size):
        chunk_symbols = missing[start_at:start_at + chunk_size]
        if not chunk_symbols:
            continue
        chunk_tickers = [f"{symbol}.NS" for symbol in chunk_symbols]
        raw = _download_chunk(yf, chunk_tickers, start, end)
        for field, yf_field in (("open", "Open"), ("high", "High"), ("low", "Low"), ("close", "Close"), ("adj_close", "Adj Close"), ("volume", "Volume")):
            parts[field].append(_extract_yf_field(raw, chunk_tickers, ticker_map, yf_field))
        close_part = _extract_yf_field(raw, chunk_tickers, ticker_map, "Close")
        for symbol in chunk_symbols:
            count = int(close_part[symbol].notna().sum()) if symbol in close_part else 0
            report_rows.append({"symbol": symbol, "ticker": f"{symbol}.NS", "source": "download", "status": "ok" if count else "missing", "close_rows": count, "error": ""})
        sleep(0.25)
    frames = {}
    for name, collected in parts.items():
        combined = pd.concat([frame for frame in collected if not frame.empty], axis=1) if any(not frame.empty for frame in collected) else pd.DataFrame()
        if combined.empty and seed_frames.get(name) is not None:
            combined = seed_frames[name].copy()
        combined = combined.loc[:, ~combined.columns.duplicated()].sort_index().reindex(columns=symbols)
        write_frame(combined, data_dir / f"{name}.csv")
        frames[name] = combined
    pd.DataFrame(report_rows).to_csv(report_path, index=False)
    return frames


def weekly_reconstitution_mask(index: pd.DatetimeIndex) -> pd.Series:
    weeks = pd.Series(index.to_period("W-FRI"), index=index)
    mask = weeks.ne(weeks.shift(1))
    if len(mask):
        mask.iloc[0] = True
    return mask.astype(bool)


def build_dynamic_high_vol_universe(
    adjusted_close: pd.DataFrame,
    raw_close: pd.DataFrame,
    volume_frame: pd.DataFrame,
    basket_size: int = 100,
    buffer_size: int = 125,
    vol_lookback: int = 20,
    min_history: int = 126,
    min_price: float = 20.0,
    min_adv_rupees: float = 50_000_000.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    returns = adjusted_close.pct_change(fill_method=None)
    realized_vol = returns.rolling(vol_lookback, min_periods=vol_lookback).std().shift(1) * math.sqrt(ANNUALIZATION)
    adv20 = raw_close.mul(volume_frame).rolling(20, min_periods=20).mean().shift(1)
    history_ok = adjusted_close.notna().rolling(min_history, min_periods=min_history).sum().shift(1).ge(min_history)
    price_ok = raw_close.shift(1).ge(min_price)
    eligible = history_ok & price_ok & adv20.ge(min_adv_rupees) & realized_vol.notna()
    reconstitute = weekly_reconstitution_mask(adjusted_close.index)
    membership = pd.DataFrame(False, index=adjusted_close.index, columns=adjusted_close.columns)
    current_members: list[str] = []
    rows = []
    for date in adjusted_close.index:
        if bool(reconstitute.loc[date]):
            scores = realized_vol.loc[date].where(eligible.loc[date]).dropna().sort_values(ascending=False)
            previous = set(current_members)
            keepers = [name for name in current_members if name in set(scores.head(buffer_size).index)]
            additions = [name for name in scores.index if name not in set(keepers)]
            current_members = (keepers + additions)[:basket_size]
            current = set(current_members)
            rows.append(
                {
                    "date": date,
                    "eligible_count": len(scores),
                    "member_count": len(current_members),
                    "entries": len(current - previous),
                    "exits": len(previous - current),
                    "entry_symbols": ",".join(sorted(current - previous)),
                    "exit_symbols": ",".join(sorted(previous - current)),
                }
            )
        if current_members:
            membership.loc[date, current_members] = True
    report = pd.DataFrame(rows)
    if not report.empty:
        report["membership_turnover_fraction"] = (report["entries"] + report["exits"]) / (2 * basket_size)
    return membership, report


def build_source_cache(refresh: bool = True) -> SourceRebuildSummary:
    _ensure_dirs()
    base_spec = IndexSpec("nifty500", "NIFTY 500", BASE_CONSTITUENT_URLS)
    base_constituents = load_constituents(base_spec, NIFTY500_CONSTITUENT_PATH, refresh=refresh)
    base_symbols = base_constituents["Symbol"].dropna().astype(str).tolist()
    base_data = download_ohlcv_panel(
        base_symbols,
        NIFTY500_DATA_DIR,
        refresh,
        NIFTY500_DOWNLOAD_REPORT_PATH,
        start=DEFAULT_FETCH_START,
    )
    base_mask, base_report = build_dynamic_high_vol_universe(base_data["adj_close"], base_data["close"], base_data["volume"])
    write_frame(base_mask.astype(int), NIFTY500_MASK_PATH)
    base_report.to_csv(NIFTY500_REPORT_PATH, index=False)

    extra_frames = {
        slug: (name, load_constituents(IndexSpec(slug, name, urls), VOLATILE_INDEX_DIR / f"{slug}.csv", refresh=refresh))
        for slug, name, urls in (*VOLATILE_INDEX_SPECS, *EXPANDED_EXTRA_SPECS)
    }
    expanded_constituents = build_expanded_parent_constituents(base_constituents, extra_frames)
    expanded_constituents.to_csv(EXPANDED_PARENT_CONSTITUENT_PATH, index=False)
    expanded_symbols = expanded_constituents["Symbol"].dropna().astype(str).tolist()
    expanded_data = download_ohlcv_panel(
        expanded_symbols,
        EXPANDED_DATA_DIR,
        refresh,
        EXPANDED_DOWNLOAD_REPORT_PATH,
        start=DEFAULT_FETCH_START,
        seed_frames=base_data,
    )
    expanded_mask, expanded_report = build_dynamic_high_vol_universe(expanded_data["adj_close"], expanded_data["close"], expanded_data["volume"])
    write_frame(expanded_mask.astype(int), EXPANDED_MASK_PATH)
    expanded_report.to_csv(EXPANDED_REPORT_PATH, index=False)
    return SourceRebuildSummary(
        nifty500_symbols=len(base_symbols),
        expanded_symbols=len(expanded_symbols),
        nifty500_members_latest=int(base_mask.iloc[-1].sum()) if len(base_mask) else 0,
        expanded_members_latest=int(expanded_mask.iloc[-1].sum()) if len(expanded_mask) else 0,
    )


def rebuild_alpha101_sources(refresh: bool = True) -> SourceRebuildSummary:
    return build_source_cache(refresh=refresh)


if __name__ == "__main__":
    print(rebuild_alpha101_sources(refresh=True))
