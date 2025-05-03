from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Target:
    label: str
    level: float

@dataclass
class ManipulationEvent:
    direction: str
    price: float
    timestamp: str

@dataclass
class Retracement:
    label: str
    level: float

@dataclass
class Report:
    symbol: str
    timeframe: str
    range_low: float
    range_high: float
    directional_bias: str
    irz_zone: Optional[str]
    irz_message: Optional[str]
    trendline_summary: Optional[str]
    support_levels: List[float]
    resistance_levels: List[float]
    chart_path: Optional[str]
    targets: List[Target]
    manipulations: List[ManipulationEvent]
    retracements: List[Retracement]  # ✅ NEW: For IRZ retracement levels
