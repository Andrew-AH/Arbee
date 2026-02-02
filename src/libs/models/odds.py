from dataclasses import dataclass
from datetime import datetime
from typing import Tuple


@dataclass(frozen=True)
class PriceData:
    timestamp: datetime
    data: dict[str, float | Tuple[float, float]]

    def copy(self):
        return PriceData(timestamp=self.timestamp, data=dict(self.data))

    def __repr__(self) -> str:
        return str(self.data)
