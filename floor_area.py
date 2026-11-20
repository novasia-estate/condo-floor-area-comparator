"""Area boundaries for a single quoted condo."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class FloorQuote:
    ask: float
    quoted: float
    included_balcony_fraction: float
    included_common_share: bool
    balcony_m2: tuple[float, float]
    common_m2: tuple[float, float]
    storage_inside: float
    circulation_inside: float


@dataclass(frozen=True)
class Result:
    enclosed_m2: tuple[float, float]
    room_remainder_m2: tuple[float, float]
    ask_per_enclosed_m2: tuple[float, float]


def compare_area(quote: FloorQuote) -> Result:
    price, size = quote.ask, quote.quoted
    balcony_lo, balcony_hi = quote.balcony_m2
    common_lo, common_hi = quote.common_m2
    factors = [price, size, balcony_lo, balcony_hi, common_lo, common_hi,
               quote.storage_inside, quote.circulation_inside, quote.included_balcony_fraction]
    if not all(isfinite(number) and number >= 0 for number in factors):
        raise ValueError("Enter finite amounts at or above zero.")
    if price <= 0 or size <= 0:
        raise ValueError("The price and quoted area must be above zero.")
    if balcony_hi < balcony_lo or common_hi < common_lo:
        raise ValueError("The lower area bound cannot exceed its upper bound.")
    if quote.included_balcony_fraction > 1:
        raise ValueError("The balcony weight must be between zero and one.")
    if not quote.included_common_share:
        common_lo = common_hi = 0
    weight = quote.included_balcony_fraction
    enclosed = (size - balcony_hi * weight - common_hi,
                size - balcony_lo * weight - common_lo)
    reserved = quote.storage_inside + quote.circulation_inside
    if enclosed[0] <= 0:
        raise ValueError("The boundary assumptions consume the quoted area. Check the input areas.")
    if reserved >= enclosed[0]:
        raise ValueError("The storage and circulation figures must leave room in the smallest enclosed case.")
    return Result(enclosed, tuple(n - reserved for n in enclosed),
                  (price / enclosed[1], price / enclosed[0]))


def ranking(a, b):
    if a[0] > b[1]:
        return "Offer A remains larger across all the supplied boundaries."
    if b[0] > a[1]:
        return "Offer B remains larger across all the supplied boundaries."
    if a == b and a[0] == a[1]:
        return "The two offers have the same area on the supplied basis."
    return "The ranges overlap. Resolve the uncertain area boundaries before ranking the plans."
