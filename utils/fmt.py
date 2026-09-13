"""
Number, money and date formatting. One place, so a KPI, a tooltip and a table
cell can never disagree about the same figure.

The rules are section 6 of docs/design-system.md:

  * SI grouping with a narrow no-break space (U+202F) and a point decimal,
    because it is the one form every reader in the Nordic and European market
    reads the same way. "1,204" is a decimal to a Dane; "1.204" is a decimal
    to a Briton; "1 204" is a thousand to both.
  * Currency as an ISO code before the value, never a symbol, because the data
    spans EUR, SEK, NOK and DKK and "kr" is three currencies.
  * Abbreviated figures stop at three significant figures. Tables never
    abbreviate. A briefing quotes the exact figure so it survives being checked.
  * True minus sign U+2212, because a hyphen breaks column alignment in mono.
  * Rounding is half away from zero and happens here, once, at display time.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

NNBSP = " "
MINUS = "−"
NONE = "none"


def _is_missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _round(value: float, decimals: int) -> float:
    q = Decimal(1).scaleb(-decimals)
    return float(Decimal(repr(float(value))).quantize(q, rounding=ROUND_HALF_UP))


def group(value, decimals: int = 0) -> str:
    """The full figure with narrow no-break space grouping: 1 204 812.5"""
    if _is_missing(value):
        return NONE
    v = _round(abs(float(value)), decimals)
    body = f"{v:,.{decimals}f}".replace(",", NNBSP)
    return (MINUS if float(value) < 0 and v != 0 else "") + body


def count(value) -> str:
    """Integers with grouping, never abbreviated below 100 000."""
    return group(value, 0)


def compact(value) -> str:
    """Three significant figures at most: 812, 1.5k, 184k, 1.24M, 12.4M, 1.2bn."""
    if _is_missing(value):
        return NONE
    v = abs(float(value))
    sign = MINUS if float(value) < 0 else ""
    if v >= 1e9:
        body = f"{_round(v / 1e9, 1):.1f}bn"
    elif v >= 1e7:
        body = f"{_round(v / 1e6, 1):.1f}M"
    elif v >= 1e6:
        body = f"{_round(v / 1e6, 2):.2f}M"
    elif v >= 1e4:
        body = f"{_round(v / 1e3, 0):.0f}k"
    elif v >= 1e3:
        # One decimal below 10k: rounding 1 530 to "2k" overstates it by 31%,
        # which is not a rounding error, it is a wrong number.
        body = f"{_round(v / 1e3, 1):.1f}k"
    else:
        body = f"{_round(v, 0):.0f}"
    return sign + body


def money(value, currency: str = "EUR", exact: bool = False) -> str:
    """'EUR 184k' for KPIs and figures, 'EUR 184 212' for tables and briefings."""
    if _is_missing(value):
        return NONE
    body = group(value, 0) if exact else compact(value)
    return f"{currency}{NNBSP}{body}"


def pct(value, decimals: int | None = None, signed: bool = False) -> str:
    """'12.4%', two decimals under 1%, no space before the sign."""
    if _is_missing(value):
        return NONE
    value = float(value)
    if decimals is None:
        decimals = 2 if 0 < abs(value) < 1 else 1
    v = _round(abs(value), decimals)
    sign = MINUS if value < 0 and v != 0 else ("+" if signed and v > 0 else "")
    return f"{sign}{v:.{decimals}f}%"


def pts(value, decimals: int = 1) -> str:
    """A change in a rate, in points: '+1.8 pts'."""
    if _is_missing(value):
        return NONE
    value = float(value)
    v = _round(abs(value), decimals)
    sign = MINUS if value < 0 and v != 0 else ("+" if v > 0 else "")
    return f"{sign}{v:.{decimals}f} pts"


def signed_pct_change(new, old) -> str | None:
    """Relative change as a signed percent, or None when there is no basis."""
    if _is_missing(new) or _is_missing(old) or not old:
        return None
    return pct(100.0 * (float(new) / float(old) - 1.0), decimals=1, signed=True)


def days(value, decimals: int = 1) -> str:
    if _is_missing(value):
        return NONE
    return f"{_round(float(value), decimals):.{decimals}f} days"


def ratio(value, decimals: int = 2) -> str:
    if _is_missing(value):
        return NONE
    return f"{_round(float(value), decimals):.{decimals}f}"


# --- Dates -----------------------------------------------------------------

def iso(ts) -> str:
    """2026-09-11. Everywhere a date is data."""
    if _is_missing(ts):
        return NONE
    return pd.Timestamp(ts).strftime("%Y-%m-%d")


def iso_range(start, end) -> str:
    """'2026-06-01 to 2026-08-31'. The word, never a dash."""
    return f"{iso(start)} to {iso(end)}"


def week(ts) -> str:
    """ISO week with year: 'W36 2026'."""
    if _is_missing(ts):
        return NONE
    y, w, _ = pd.Timestamp(ts).isocalendar()
    return f"W{int(w):02d} {int(y)}"


def week_range(start, end) -> str:
    return f"{week(start)} to {week(end)}"


def month(ts) -> str:
    """'September 2026' in prose."""
    if _is_missing(ts):
        return NONE
    return pd.Timestamp(ts).strftime("%B %Y")


def prose_date(ts) -> str:
    """'11 September 2026'. Never numeric day/month order, because 11/09 is two dates."""
    if _is_missing(ts):
        return NONE
    t = pd.Timestamp(ts)
    return f"{t.day} {t.strftime('%B %Y')}"


def prose_range(start, end) -> str:
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    if s.year == e.year and s.month == e.month:
        return f"{s.day} to {e.day} {e.strftime('%B %Y')}"
    if s.year == e.year:
        return f"{s.day} {s.strftime('%B')} to {e.day} {e.strftime('%B %Y')}"
    return f"{prose_date(s)} to {prose_date(e)}"


def timestamp(ts, zone: str = "UTC") -> str:
    """'2026-09-11 06:00 UTC'. Timestamps always carry the zone."""
    if _is_missing(ts):
        return NONE
    return f"{pd.Timestamp(ts).strftime('%Y-%m-%d %H:%M')} {zone}"


def plain(value) -> str:
    """Text cells: the value as a string, or the missing marker."""
    return NONE if _is_missing(value) else str(value)
