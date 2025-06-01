from dataclasses import dataclass, field
from typing import List, Optional, Dict, Union

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
    # Non-default fields first
    symbol: str
    timeframe: str
    range_low: float
    range_high: float
    directional_bias: str
    support_levels: List[float]
    resistance_levels: List[float]
    targets: List[Target]
    manipulations: List[ManipulationEvent]
    retracements: List[Retracement]

    # Default fields below
    irz_zone: Optional[str] = None
    irz_message: Optional[str] = None
    trendline_summary: Optional[str] = None
    trendlines: List = field(default_factory=list)
    chart_path: Optional[str] = None
    current_price: Optional[float] = None
    current_price_time: Optional[str] = None

    # ✅ HTF alignment confidence tagging
    confidence: Dict[str, Dict[Union[str, float], Dict[str, Union[str, List[str]]]]] = field(default_factory=dict)

    # 🌸 Kawaii Buy flag
    kawaii_buy: bool = False
