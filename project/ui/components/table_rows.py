from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from typing import overload


@dataclass(frozen=True)
class TableRows(Sequence[dict[str, object]]):
    rows: tuple[dict[str, object], ...]

    def __iter__(self) -> Iterator[dict[str, object]]:
        return iter(self.rows)

    def __len__(self) -> int:
        return len(self.rows)

    @overload
    def __getitem__(self, index: int) -> dict[str, object]:
        ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[dict[str, object]]:
        ...

    def __getitem__(
        self, index: int | slice
    ) -> dict[str, object] | Sequence[dict[str, object]]:
        return self.rows[index]

    def to_dict(self, orient: str = "records") -> list[dict[str, object]]:
        if orient != "records":
            raise ValueError(f"Unsupported orient: {orient}")
        return [dict(row) for row in self.rows]


def build_table_rows(rows: Iterable[object]) -> TableRows:
    return TableRows(tuple(_row_data(row) for row in rows))


def _row_data(row: object) -> dict[str, object]:
    if isinstance(row, dict):
        return dict(row)
    data = getattr(row, "__dict__", None)
    if isinstance(data, dict):
        return dict(data)
    raise TypeError(f"Unsupported row type: {type(row).__name__}")
