from __future__ import annotations

from typing import TypedDict

import pandas as pd


class UniverseData(TypedDict):
    regime: pd.DataFrame
    frames: dict[str, pd.DataFrame]
