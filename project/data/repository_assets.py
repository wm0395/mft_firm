from __future__ import annotations

from typing import Any, cast

from project.data.db import DuckDBAccess
from project.common.models import Asset, utc_now_iso


class RepositoryAssetsMixin:
    _db: DuckDBAccess

    def add_asset(self, symbol: str, name: str, sector: str, market: str) -> Asset:
        db = _db(self)
        if not symbol or not name or not market:
            raise ValueError("symbol, name, and market are required")
        asset = Asset(
            asset_id=f"asset:{symbol.upper()}",
            symbol=symbol.upper(),
            name=name,
            sector=sector,
            market=market,
            is_active=True,
            created_at=utc_now_iso(),
        )
        db.execute(
            """
            insert into assets values (?, ?, ?, ?, ?, ?, ?)
            on conflict(asset_id) do nothing
            """,
            (
                asset.asset_id,
                asset.symbol,
                asset.name,
                asset.sector,
                asset.market,
                asset.is_active,
                asset.created_at,
            ),
        )
        return asset

    def list_assets(self) -> tuple[Asset, ...]:
        rows = _db(self).fetch_all(
            "select asset_id, symbol, name, sector, market, is_active, created_at "
            "from assets order by symbol"
        )
        return tuple(Asset(*row) for row in rows)


def _db(repository: Any) -> DuckDBAccess:
    return cast(DuckDBAccess, repository._db)
