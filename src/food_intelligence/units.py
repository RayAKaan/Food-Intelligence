"""Strict, dependency-free unit definitions and quantity conversion.

Conversions are allowed only between registered units with the same physical
dimension. Unknown/custom units can still be represented by Quantity, but
cannot be converted until explicitly supported here.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Final

from .world_contracts import Quantity, UncertaintyEstimate


@dataclass(frozen=True)
class UnitDefinition:
    symbol: str
    dimension: str
    scale: float = 1.0
    offset: float = 0.0
    base_unit: str | None = None

    def __post_init__(self) -> None:
        if not self.symbol.strip() or not self.dimension.strip():
            raise ValueError("unit symbol and dimension must be non-empty")
        if not math.isfinite(self.scale) or self.scale <= 0:
            raise ValueError("unit scale must be finite and positive")
        if not math.isfinite(self.offset):
            raise ValueError("unit offset must be finite")


# Base transform: base_value = value * scale + offset.
# Dimensions intentionally prevent conversions between mass/volume and mass/mass.
_UNIT_ROWS = (
    ("kg", "mass", 1.0, 0.0, "kg"),
    ("g", "mass", 1e-3, 0.0, "kg"),
    ("mg", "mass", 1e-6, 0.0, "kg"),
    ("ug", "mass", 1e-9, 0.0, "kg"),
    ("µg", "mass", 1e-9, 0.0, "kg"),
    ("m3", "volume", 1.0, 0.0, "m3"),
    ("L", "volume", 1e-3, 0.0, "m3"),
    ("mL", "volume", 1e-6, 0.0, "m3"),
    ("uL", "volume", 1e-9, 0.0, "m3"),
    ("µL", "volume", 1e-9, 0.0, "m3"),
    ("m", "length", 1.0, 0.0, "m"),
    ("cm", "length", 1e-2, 0.0, "m"),
    ("mm", "length", 1e-3, 0.0, "m"),
    ("s", "time", 1.0, 0.0, "s"),
    ("min", "time", 60.0, 0.0, "s"),
    ("h", "time", 3600.0, 0.0, "s"),
    ("K", "temperature", 1.0, 0.0, "K"),
    ("degC", "temperature", 1.0, 273.15, "K"),
    ("°C", "temperature", 1.0, 273.15, "K"),
    ("degF", "temperature", 5.0 / 9.0, 255.3722222222222, "K"),
    ("°F", "temperature", 5.0 / 9.0, 255.3722222222222, "K"),
    ("Pa", "pressure", 1.0, 0.0, "Pa"),
    ("kPa", "pressure", 1e3, 0.0, "Pa"),
    ("bar", "pressure", 1e5, 0.0, "Pa"),
    ("atm", "pressure", 101325.0, 0.0, "Pa"),
    ("J", "energy", 1.0, 0.0, "J"),
    ("kJ", "energy", 1e3, 0.0, "J"),
    ("cal", "energy", 4.184, 0.0, "J"),
    ("kcal", "energy", 4184.0, 0.0, "J"),
    ("W", "power", 1.0, 0.0, "W"),
    ("kW", "power", 1e3, 0.0, "W"),
    ("mol", "amount_of_substance", 1.0, 0.0, "mol"),
    ("mmol", "amount_of_substance", 1e-3, 0.0, "mol"),
    ("mol/m3", "amount_concentration", 1.0, 0.0, "mol/m3"),
    ("mol/L", "amount_concentration", 1e3, 0.0, "mol/m3"),
    ("mmol/L", "amount_concentration", 1.0, 0.0, "mol/m3"),
    ("kg/m3", "mass_concentration", 1.0, 0.0, "kg/m3"),
    ("g/L", "mass_concentration", 1.0, 0.0, "kg/m3"),
    ("mg/L", "mass_concentration", 1e-3, 0.0, "kg/m3"),
    ("g/kg", "mass_fraction", 1e-3, 0.0, "kg/kg"),
    ("mg/kg", "mass_fraction", 1e-6, 0.0, "kg/kg"),
    ("kg/kg", "mass_fraction", 1.0, 0.0, "kg/kg"),
    ("1", "dimensionless", 1.0, 0.0, "1"),
    ("ratio", "dimensionless", 1.0, 0.0, "1"),
    ("%", "dimensionless", 1e-2, 0.0, "1"),
    ("pH", "pH", 1.0, 0.0, "pH"),
    ("score", "sensory_score", 1.0, 0.0, "score"),
    ("relative", "relative_measure", 1.0, 0.0, "relative"),
)

UNIT_REGISTRY: Final[dict[str, UnitDefinition]] = {
    symbol: UnitDefinition(symbol, dimension, scale, offset, base)
    for symbol, dimension, scale, offset, base in _UNIT_ROWS
}


def unit_definition(unit: str) -> UnitDefinition:
    """Return a registered unit definition; fail closed for unknown units."""
    try:
        return UNIT_REGISTRY[unit]
    except KeyError:
        raise ValueError(f"unsupported unit: {unit}") from None


def unit_dimension(unit: str) -> str:
    """Return the physical dimension associated with a registered unit."""
    return unit_definition(unit).dimension


def assert_compatible_units(source_unit: str, target_unit: str) -> None:
    """Raise when two registered units do not describe the same dimension."""
    source = unit_definition(source_unit)
    target = unit_definition(target_unit)
    if source.dimension != target.dimension:
        raise ValueError(
            f"incompatible units: {source_unit} ({source.dimension}) and "
            f"{target_unit} ({target.dimension})"
        )


def convert_value(value: float, source_unit: str, target_unit: str) -> float:
    """Convert a finite scalar, rejecting unknown or dimensionally incompatible units."""
    if not math.isfinite(value):
        raise ValueError("value must be finite")
    assert_compatible_units(source_unit, target_unit)
    source = unit_definition(source_unit)
    target = unit_definition(target_unit)
    base_value = value * source.scale + source.offset
    result = (base_value - target.offset) / target.scale
    if not math.isfinite(result):
        raise ValueError("converted value is not finite")
    return result


def _convert_uncertainty(
    uncertainty: UncertaintyEstimate | None, source_unit: str, target_unit: str
) -> UncertaintyEstimate | None:
    if uncertainty is None:
        return None
    source = unit_definition(source_unit)
    target = unit_definition(target_unit)
    # Standard deviations scale but are not translated by affine offsets.
    scale_ratio = source.scale / target.scale
    return replace(
        uncertainty,
        standard_deviation=(
            None if uncertainty.standard_deviation is None
            else uncertainty.standard_deviation * abs(scale_ratio)
        ),
        lower_bound=(
            None if uncertainty.lower_bound is None
            else convert_value(uncertainty.lower_bound, source_unit, target_unit)
        ),
        upper_bound=(
            None if uncertainty.upper_bound is None
            else convert_value(uncertainty.upper_bound, source_unit, target_unit)
        ),
    )


def convert_quantity(quantity: Quantity, target_unit: str) -> Quantity:
    """Convert a Quantity, including its uncertainty, without changing missingness."""
    assert_compatible_units(quantity.unit, target_unit)
    value = (
        None if quantity.value is None
        else convert_value(quantity.value, quantity.unit, target_unit)
    )
    uncertainty = _convert_uncertainty(quantity.uncertainty, quantity.unit, target_unit)
    return Quantity(value=value, unit=target_unit, uncertainty=uncertainty)


def normalize_quantity(quantity: Quantity) -> Quantity:
    """Express a quantity in the registry's canonical base unit for its dimension."""
    definition = unit_definition(quantity.unit)
    base = definition.base_unit or definition.symbol
    return convert_quantity(quantity, base)
