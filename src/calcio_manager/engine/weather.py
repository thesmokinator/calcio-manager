"""Weather generation for match days — realistic for Provincia di Varese.

Varese sits at the foot of the pre-Alps in northern Lombardy, with a
sub-continental climate influenced by nearby lakes. Winters are cold and
often foggy, summers warm and prone to thunderstorms.

CSI amateur season typically runs September → June, so the module
covers all twelve months but weather during matches will mostly fall
in that range.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Weather:
    """Weather conditions for a match.

    *key* is a translation key (e.g. ``"fog"``, ``"rain"``), looked up via
    ``t(f"weather.{key}")`` at display time.
    """

    key: str
    icon: str
    temperature: int


# ---------------------------------------------------------------------------
# Monthly weather tables for Provincia di Varese
#
# Each month defines a list of (condition, icon, probability_weight)
# and a (temp_min, temp_max) range.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _Condition:
    label: str
    icon: str
    weight: int


_MONTHLY_CONDITIONS: dict[int, list[_Condition]] = {
    1: [
        _Condition("fog", "\U0001f32b", 25),
        _Condition("overcast", "\u2601", 25),
        _Condition("rain", "\U0001f327", 15),
        _Condition("snow", "\u2744", 20),
        _Condition("partly_cloudy", "\u26c5", 10),
        _Condition("clear", "\u2600", 5),
    ],
    2: [
        _Condition("fog", "\U0001f32b", 20),
        _Condition("overcast", "\u2601", 25),
        _Condition("rain", "\U0001f327", 15),
        _Condition("snow", "\u2744", 15),
        _Condition("partly_cloudy", "\u26c5", 15),
        _Condition("clear", "\u2600", 10),
    ],
    3: [
        _Condition("rain", "\U0001f327", 25),
        _Condition("overcast", "\u2601", 20),
        _Condition("partly_cloudy", "\u26c5", 25),
        _Condition("clear", "\u2600", 15),
        _Condition("fog", "\U0001f32b", 10),
        _Condition("snow", "\u2744", 5),
    ],
    4: [
        _Condition("rain", "\U0001f327", 25),
        _Condition("partly_cloudy", "\u26c5", 25),
        _Condition("overcast", "\u2601", 15),
        _Condition("clear", "\u2600", 25),
        _Condition("thunderstorm", "\u26c8", 10),
    ],
    5: [
        _Condition("clear", "\u2600", 30),
        _Condition("partly_cloudy", "\u26c5", 25),
        _Condition("rain", "\U0001f327", 15),
        _Condition("thunderstorm", "\u26c8", 15),
        _Condition("overcast", "\u2601", 15),
    ],
    6: [
        _Condition("clear", "\u2600", 35),
        _Condition("partly_cloudy", "\u26c5", 20),
        _Condition("thunderstorm", "\u26c8", 20),
        _Condition("rain", "\U0001f327", 10),
        _Condition("overcast", "\u2601", 15),
    ],
    7: [
        _Condition("clear", "\u2600", 40),
        _Condition("partly_cloudy", "\u26c5", 20),
        _Condition("thunderstorm", "\u26c8", 25),
        _Condition("overcast", "\u2601", 10),
        _Condition("rain", "\U0001f327", 5),
    ],
    8: [
        _Condition("clear", "\u2600", 35),
        _Condition("partly_cloudy", "\u26c5", 20),
        _Condition("thunderstorm", "\u26c8", 25),
        _Condition("overcast", "\u2601", 10),
        _Condition("rain", "\U0001f327", 10),
    ],
    9: [
        _Condition("clear", "\u2600", 25),
        _Condition("partly_cloudy", "\u26c5", 25),
        _Condition("rain", "\U0001f327", 20),
        _Condition("overcast", "\u2601", 15),
        _Condition("thunderstorm", "\u26c8", 10),
        _Condition("fog", "\U0001f32b", 5),
    ],
    10: [
        _Condition("rain", "\U0001f327", 25),
        _Condition("fog", "\U0001f32b", 20),
        _Condition("overcast", "\u2601", 20),
        _Condition("partly_cloudy", "\u26c5", 20),
        _Condition("clear", "\u2600", 15),
    ],
    11: [
        _Condition("fog", "\U0001f32b", 25),
        _Condition("rain", "\U0001f327", 25),
        _Condition("overcast", "\u2601", 25),
        _Condition("partly_cloudy", "\u26c5", 15),
        _Condition("clear", "\u2600", 10),
    ],
    12: [
        _Condition("fog", "\U0001f32b", 25),
        _Condition("overcast", "\u2601", 25),
        _Condition("snow", "\u2744", 20),
        _Condition("rain", "\U0001f327", 15),
        _Condition("partly_cloudy", "\u26c5", 10),
        _Condition("clear", "\u2600", 5),
    ],
}

# Temperature ranges (min, max) per month — Varese area
_MONTHLY_TEMPS: dict[int, tuple[int, int]] = {
    1: (-3, 7),
    2: (-1, 9),
    3: (3, 14),
    4: (7, 18),
    5: (11, 23),
    6: (15, 28),
    7: (18, 31),
    8: (17, 30),
    9: (13, 25),
    10: (8, 18),
    11: (3, 11),
    12: (-2, 7),
}


def generate_weather(month: int) -> Weather:
    """Generate realistic weather for a match in the given month.

    Args:
        month: Calendar month (1-12).

    Returns:
        Weather conditions with label, icon and temperature.
    """
    conditions = _MONTHLY_CONDITIONS.get(month, _MONTHLY_CONDITIONS[9])
    weights = [c.weight for c in conditions]
    chosen = random.choices(conditions, weights=weights, k=1)[0]

    temp_min, temp_max = _MONTHLY_TEMPS.get(month, (10, 20))
    temperature = random.randint(temp_min, temp_max)

    return Weather(
        key=chosen.label,
        icon=chosen.icon,
        temperature=temperature,
    )
