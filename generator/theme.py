"""Dark ("polar night") and light ("midnight sun") palettes."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Theme:
    name: str
    ink: str
    ink2: str
    ink3: str
    line: str
    line2: str
    panel: str
    panel2: str
    sky: tuple[str, str]
    ridge_far: str
    ridge_near: str
    water: str
    aurora: tuple[str, ...]
    accent: dict = field(default_factory=dict)

    @property
    def dark(self) -> bool:
        return self.name == "dark"


DARK = Theme(
    name="dark",
    ink="#E6EDF3",
    ink2="#A3AEBB",
    ink3="#6A7480",
    line="#E6EDF31A",
    line2="#E6EDF32E",
    panel="#0F141C",
    panel2="#151C27",
    sky=("#03050A", "#0C1A31"),
    ridge_far="#0F1B2C",
    ridge_near="#060A12",
    water="#04070D",
    aurora=("#34D399", "#2DD4BF", "#22D3EE", "#818CF8", "#C084FC", "#F472B6"),
    accent={
        "data": "#2DD4BF",
        "ai": "#A78BFA",
        "bi": "#F5C542",
        "eng": "#4BA3FF",
        "hot": "#FF7A59",
        "pink": "#F472B6",
        "ok": "#3FB950",
    },
)

LIGHT = Theme(
    name="light",
    ink="#1F2328",
    ink2="#4F5A66",
    ink3="#86909B",
    line="#1F23281A",
    line2="#1F23282E",
    panel="#FFFFFF",
    panel2="#F5F7FA",
    sky=("#E6EDF6", "#FBF4EA"),
    ridge_far="#C3CEDB",
    ridge_near="#93A3B6",
    water="#EDF1F6",
    aurora=("#059669", "#0D9488", "#0891B2", "#4F46E5", "#7C3AED", "#DB2777"),
    accent={
        "data": "#0D9488",
        "ai": "#7C3AED",
        "bi": "#B7791F",
        "eng": "#0969DA",
        "hot": "#E0552F",
        "pink": "#DB2777",
        "ok": "#1A7F37",
    },
)

THEMES = (DARK, LIGHT)
