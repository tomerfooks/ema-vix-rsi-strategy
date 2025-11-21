"""
QuantConnect Strategy Implementations
Ported from OpenCL optimization system

Organized structure:
- Each strategy has its own folder with timeframe-specific versions
- Backward compatible with old imports
"""

from .base_strategy import BaseStrategy

# Import from organized folder structure
from .adaptive_ema_v2 import AdaptiveEMAV2
from .adaptive_ema_v2_1 import AdaptiveEMAV2_1
from .adaptive_ema_v2_2 import AdaptiveEMAV2_2
from .adaptive_ema_vol_v1 import AdaptiveEMAVolV1
from .adaptive_donchian_v1 import AdaptiveDonchianV1

__all__ = [
    'BaseStrategy',
    'AdaptiveEMAV2',
    'AdaptiveEMAV2_1',
    'AdaptiveEMAV2_2',
    'AdaptiveEMAVolV1',
    'AdaptiveDonchianV1',
]
