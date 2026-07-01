"""Rappresentazione del prodotto digitale che l'ufficio virtuale
costruisce e raffina ciclo dopo ciclo."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class ProductSpec:
    name: str = "Da definire"
    tagline: str = ""
    description: str = ""
    target_market: str = ""
    key_features: List[str] = field(default_factory=list)
    pricing_model: str = ""
    revenue_strategy: str = ""
    differentiators: List[str] = field(default_factory=list)
    main_risks: List[str] = field(default_factory=list)
    version: int = 0
    viability_score: float = 0.0

    def apply_update(self, data: dict) -> None:
        for key in (
            "name",
            "tagline",
            "description",
            "target_market",
            "pricing_model",
            "revenue_strategy",
        ):
            if data.get(key):
                setattr(self, key, data[key])
        for key in ("key_features", "differentiators", "main_risks"):
            value = data.get(key)
            if isinstance(value, list) and value:
                setattr(self, key, [str(v) for v in value])
        self.version += 1

    def to_dict(self) -> dict:
        return asdict(self)

    def to_markdown(self) -> str:
        def bullets(items: List[str]) -> List[str]:
            return [f"- {item}" for item in items] if items else ["-"]

        lines = [
            f"# {self.name}",
            f"_{self.tagline}_" if self.tagline else "",
            "",
            f"**Versione:** {self.version}  |  **Punteggio di viabilita':** {self.viability_score:.0f}/100",
            "",
            "## Descrizione",
            self.description or "-",
            "",
            "## Mercato di riferimento",
            self.target_market or "-",
            "",
            "## Funzionalita' chiave",
            *bullets(self.key_features),
            "",
            "## Elementi distintivi",
            *bullets(self.differentiators),
            "",
            "## Modello di pricing",
            self.pricing_model or "-",
            "",
            "## Strategia di ricavo",
            self.revenue_strategy or "-",
            "",
            "## Rischi principali",
            *bullets(self.main_risks),
        ]
        return "\n".join(lines)
