from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from research.notebooks.alpha_001.research.alpha101_engine import Alpha101Panel


@dataclass(frozen=True)
class StrategySpec:
    name: str
    family: str
    description: str
    builder: Callable[[Alpha101Panel], pd.DataFrame]
