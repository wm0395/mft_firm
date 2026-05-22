from __future__ import annotations

from pathlib import Path
import sys


NOTEBOOK_ROOT = Path(__file__).resolve().parents[1]
if str(NOTEBOOK_ROOT) not in sys.path:
    sys.path.insert(0, str(NOTEBOOK_ROOT))

from research.rebuild_alpha101_sources import rebuild_alpha101_sources  # noqa: E402
from research.alpha101_factory import run_alpha101_factory  # noqa: E402
from research.alpha101_robustness import run_alpha101_robustness_batch2  # noqa: E402
from research.alpha101_robustness_batch_runner import run_alpha101_robustness_batches  # noqa: E402
from research.alpha101_closed_loop import write_closed_loop_summary  # noqa: E402


def rebuild_alpha101(refresh: bool = True) -> None:
    rebuild_alpha101_sources(refresh=refresh)
    run_alpha101_factory(max_workers=1, refresh=refresh, progress=True, reaggregate=True)
    run_alpha101_robustness_batches(refresh=refresh, progress=True)
    run_alpha101_robustness_batch2(refresh=refresh, progress=True)
    write_closed_loop_summary(Path("research/artifacts/alpha101_research_factory"))


if __name__ == "__main__":
    rebuild_alpha101(refresh=True)
