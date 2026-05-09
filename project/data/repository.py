from __future__ import annotations
import json
from datetime import datetime


from project.common.models import Asset, Decision, Position, RawDataPoint, Signal, TradeIdea, utc_now_iso
from project.data.db import DuckDBAccess
from project.data.models import HypothesisEvaluation, SignalEvaluation


class DataRepository:
    def __init__(self, db: DuckDBAccess) -> None:
        self._db = db

    def initialize(self) -> None:
        self._db.initialize_schema()

    def ingest_market_data(
        self, 
        asset_symbol: str, 
        timestamp: datetime, 
        open: float, 
        high: float, 
        low: float, 
        close: float, 
        volume: float
    ) -> None:
        self._db.execute(
            """
            insert into raw_market_data values (?, ?, ?, ?, ?, ?, ?)
            """,
            (asset_symbol, timestamp, open, high, low, close, volume),
        )

    def persist_signal_evaluation(self, eval: SignalEvaluation) -> None:
        self._db.execute(
            """
            insert into signal_evaluations values (?, ?, ?, ?, ?, ?)
            on conflict(signal_id) do update set
                hypothesis_id = excluded.hypothesis_id,
                forward_return_1 = excluded.forward_return_1,
                forward_return_5 = excluded.forward_return_5,
                forward_return_20 = excluded.forward_return_20,
                evaluation_timestamp = excluded.evaluation_timestamp
            """,
            (eval.signal_id, eval.hypothesis_id, eval.forward_return_1, eval.forward_return_5, eval.forward_return_20, eval.evaluation_timestamp),
        )

    def get_signal_evaluations(self) -> tuple[SignalEvaluation, ...]:
        rows = self._db.fetch_all(
            "select signal_id, hypothesis_id, forward_return_1, forward_return_5, forward_return_20, evaluation_timestamp from signal_evaluations"
        )
        return tuple(SignalEvaluation(*row) for row in rows)

    def add_asset(self, symbol: str, name: str, sector: str, market: str) -> Asset:
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
        self._db.execute(
            """
            insert into assets values (?, ?, ?, ?, ?, ?, ?)
            on conflict(asset_id) do nothing
            """,
            (asset.asset_id, asset.symbol, asset.name, asset.sector, asset.market, asset.is_active, asset.created_at),
        )
        return asset

    def list_assets(self) -> tuple[Asset, ...]:
        rows = self._db.fetch_all(
            "select asset_id, symbol, name, sector, market, is_active, created_at from assets order by symbol"
        )
        return tuple(Asset(*row) for row in rows)

    def get_market_data(self, asset_symbol: str, start_timestamp: datetime, end_timestamp: datetime) -> tuple[tuple, ...]:
        rows = self._db.fetch_all(
            """
            select timestamp, open, high, low, close, volume
            from raw_market_data
            where asset_symbol = ? and timestamp between ? and ?
            order by timestamp
            """,
            (asset_symbol, start_timestamp, end_timestamp),
        )
        return tuple(rows)

    def ingest_raw(self, point: RawDataPoint) -> None:
        self._db.execute(
            """
            insert into raw_data values (?, ?, ?, ?, ?, ?)
            on conflict(asset_id, timestamp, data_type, source) do nothing
            """,
            (
                point.data_id,
                point.asset_id,
                point.timestamp,
                point.data_type,
                json.dumps(point.value, sort_keys=True),
                point.source,
            ),
        )

    def read_raw_values(self, asset_id: str, data_type: str) -> tuple[RawDataPoint, ...]:
        rows = self._db.fetch_all(
            """
            select data_id, asset_id, timestamp, data_type, value_json, source
            from raw_data
            where asset_id = ? and data_type = ?
            order by timestamp
            """,
            (asset_id, data_type),
        )
        return tuple(RawDataPoint(row[0], row[1], row[2], row[3], json.loads(row[4]), row[5]) for row in rows)

    def persist_signal(self, signal: Signal) -> None:
        signal_id = f"signal:{signal.asset_id}:{signal.timestamp}:{signal.signal_type}"
        self._db.execute(
            """
            insert into signals values (?, ?, ?, ?, ?, ?, ?)
            on conflict(asset_id, timestamp, signal_type) do nothing
            """,
            (
                signal_id,
                signal.asset_id,
                signal.timestamp,
                signal.signal_type,
                signal.value,
                json.dumps(signal.metadata, sort_keys=True),
                signal.is_persistent,
            ),
        )

    def persist_trade_idea(self, trade: TradeIdea) -> None:
        self._db.execute(
            """
            insert into trade_ideas values (?, ?, ?, ?, ?, ?, ?)
            on conflict(trade_id) do nothing
            """,
            (
                trade.trade_id,
                trade.asset_id,
                trade.hypothesis_id,
                trade.version,
                trade.direction,
                trade.confidence,
                json.dumps(trade.signals_snapshot, sort_keys=True),
            ),
        )

    def persist_hypothesis_evaluation(self, evaluation: HypothesisEvaluation) -> None:
        self._db.execute(
            """
            insert into hypothesis_evaluations values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(evaluation_id) do nothing
            """,
            (
                evaluation.evaluation_id,
                evaluation.asset_id,
                evaluation.hypothesis_id,
                evaluation.hypothesis_version,
                evaluation.timestamp,
                evaluation.direction,
                evaluation.confidence,
                evaluation.signals_snapshot_json,
                evaluation.explanation_json,
                evaluation.generated_trade_idea,
                evaluation.validation_result_json,
                evaluation.created_at,
            ),
        )

    def get_hypothesis_evaluations(self, asset_id: str | None = None, hypothesis_id: str | None = None) -> tuple[HypothesisEvaluation, ...]:
        conditions = []
        params = []
        
        if asset_id is not None:
            conditions.append("asset_id = ?")
            params.append(asset_id)
            
        if hypothesis_id is not None:
            conditions.append("hypothesis_id = ?")
            params.append(hypothesis_id)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        rows = self._db.fetch_all(
            f"""
            select evaluation_id, asset_id, hypothesis_id, hypothesis_version, timestamp, 
                   direction, confidence, signals_snapshot_json, explanation_json, 
                   generated_trade_idea, validation_result_json, created_at
            from hypothesis_evaluations
            where {where_clause}
            order by timestamp
            """,
            params,
        )
        
        return tuple(
            HypothesisEvaluation(
                evaluation_id=row[0],
                asset_id=row[1],
                hypothesis_id=row[2],
                hypothesis_version=row[3],
                timestamp=row[4],
                direction=row[5],
                confidence=row[6],
                signals_snapshot_json=row[7],
                explanation_json=row[8],
                generated_trade_idea=bool(row[9]),
                validation_result_json=row[10],
                created_at=row[11],
            )
            for row in rows
        )

    def get_trade_ideas(self, asset_id: str | None = None, hypothesis_id: str | None = None, direction: str | None = None) -> tuple[TradeIdea, ...]:
        from project.common.models import TradeIdea
        import json
        
        conditions = []
        params = []
        
        if asset_id is not None:
            conditions.append("asset_id = ?")
            params.append(asset_id)
            
        if hypothesis_id is not None:
            conditions.append("hypothesis_id = ?")
            params.append(hypothesis_id)
            
        if direction is not None:
            conditions.append("direction = ?")
            params.append(direction)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        rows = self._db.fetch_all(
            f"""
            select trade_id, asset_id, hypothesis_id, version, direction, confidence, signals_snapshot_json
            from trade_ideas
            where {where_clause}
            """,
            params,
        )
        
        return tuple(
            TradeIdea(
                trade_id=row[0],
                asset_id=row[1],
                hypothesis_id=row[2],
                version=row[3],
                direction=row[4],
                confidence=row[5],
                signals_snapshot=json.loads(row[6]),
            )
            for row in rows
        )

    def persist_position(self, position: Position) -> None:
        self._db.execute(
            """
            insert into positions values (?, ?, ?, ?, ?, ?)
            on conflict(position_id) do update set
                exit_price = excluded.exit_price,
                pnl = excluded.pnl,
                status = excluded.status
            """,
            (
                position.position_id,
                position.trade_id,
                position.entry_price,
                position.exit_price,
                position.pnl,
                position.status,
            ),
        )

    def get_positions(
        self, 
        asset_id: str | None = None, 
        hypothesis_id: str | None = None, 
        direction: str | None = None, 
        status: str | None = None
    ) -> tuple[Position, ...]:
        from project.common.models import Position
        
        conditions = []
        params = []
        
        if asset_id is not None:
            conditions.append("ti.asset_id = ?")
            params.append(asset_id)
            
        if hypothesis_id is not None:
            conditions.append("ti.hypothesis_id = ?")
            params.append(hypothesis_id)
            
        if direction is not None:
            conditions.append("ti.direction = ?")
            params.append(direction)
            
        if status is not None:
            conditions.append("p.status = ?")
            params.append(status)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        rows = self._db.fetch_all(
            f"""
            select p.position_id, p.trade_id, p.entry_price, p.exit_price, p.pnl, p.status
            from positions p
            join trade_ideas ti on p.trade_id = ti.trade_id
            where {where_clause}
            """,
            params,
        )
        
        return tuple(
            Position(
                position_id=row[0],
                trade_id=row[1],
                entry_price=row[2],
                exit_price=row[3],
                pnl=row[4],
                status=row[5],
            )
            for row in rows
        )

    def get_open_trade_ideas(self, asset_id: str | None = None, hypothesis_id: str | None = None, direction: str | None = None) -> tuple[TradeIdea, ...]:
        from project.common.models import TradeIdea
        import json
        
        conditions = []
        params = []
        
        if asset_id is not None:
            conditions.append("ti.asset_id = ?")
            params.append(asset_id)
            
        if hypothesis_id is not None:
            conditions.append("ti.hypothesis_id = ?")
            params.append(hypothesis_id)
            
        if direction is not None:
            conditions.append("ti.direction = ?")
            params.append(direction)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        rows = self._db.fetch_all(
            f"""
            select ti.trade_id, ti.asset_id, ti.hypothesis_id, ti.version, ti.direction, ti.confidence, ti.signals_snapshot_json
            from trade_ideas ti
            left join decisions d on ti.trade_id = d.trade_id
            where d.decision_id is null and {where_clause}
            """,
            params,
        )
        
        return tuple(
            TradeIdea(
                trade_id=row[0],
                asset_id=row[1],
                hypothesis_id=row[2],
                version=row[3],
                direction=row[4],
                confidence=row[5],
                signals_snapshot=json.loads(row[6]),
            )
            for row in rows
        )

    def persist_decision(self, decision: Decision) -> None:
        self._db.execute(
            """
            insert into decisions values (?, ?, ?, ?, ?, ?)
            on conflict(decision_id) do nothing
            """,
            (
                decision.decision_id,
                decision.trade_id,
                decision.action,
                decision.structured_reason,
                decision.notes,
                decision.created_at,
            ),
        )

    def get_decisions(self, trade_id: str | None = None) -> tuple[tuple, ...]:
        conditions = []
        params = []
        
        if trade_id is not None:
            conditions.append("trade_id = ?")
            params.append(trade_id)
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        rows = self._db.fetch_all(
            f"""
            select decision_id, trade_id, action, structured_reason, notes, created_at
            from decisions
            where {where_clause}
            """,
            params,
        )
        
        return tuple(tuple(row) for row in rows)
