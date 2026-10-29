from dataclasses import dataclass


@dataclass
class SectionProperties:
    area_mm2: float = 150.0
    E_GPa: float = 210.0
    yield_MPa: float = 235.0
    section_shape: str = "square"
