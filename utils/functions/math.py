import os
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any

def kaufmaennisch_runden(x):
    """Rundet nach kaufmännischer Regel: ab 0.5 wird aufgerundet.
       Dies ist standardmäßig bei Python nicht der Fall.
    """
    return int(Decimal(str(round(x, 3))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))