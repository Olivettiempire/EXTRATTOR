"""Orchestratore dell'ufficio virtuale: fa collaborare gli agenti in
cicli successivi finche' il prodotto non raggiunge una soglia di
viabilita' accettabile oppure si esauriscono i cicli disponibili."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .agent import BaseAgent, QueryFn
from .product import ProductSpec
from .roles import build_office_agents

SCORE_PATTERN = re.compile(r"PUNTEGGIO:\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
JSON_BLOCK_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class RoundLog:
    round_number: int
    contributions: dict
    viability_score: float


@dataclass
class OfficeSession:
    topic: str
    product: ProductSpec = field(default_factory=ProductSpec)
    rounds: List[RoundLog] = field(default_factory=list)


class VirtualOffice:
    """Coordina un piccolo team di agenti specializzati che collaborano,
    si confrontano e si aggiornano per costruire un prodotto digitale.

    Nota: il punteggio di viabilita' e' una stima euristica prodotta
    dagli agenti stessi, non una garanzia di successo commerciale -
    nessun sistema software puo' garantire un tasso di successo del
    100% nella vendita di un prodotto reale.
    """

    def __init__(
        self,
        query_fn: Optional[QueryFn] = None,
        model: Optional[str] = "sonnet",
        viability_threshold: float = 90.0,
        max_rounds: int = 3,
    ):
        self.agents = build_office_agents(query_fn=query_fn, model=model)
        self.viability_threshold = viability_threshold
        self.max_rounds = max_rounds

    def run(self, topic: str) -> OfficeSession:
        session = OfficeSession(topic=topic)

        for round_number in range(1, self.max_rounds + 1):
            contributions = self._run_round(session, round_number)
            score = self._extract_score(contributions["optimizer"])
            session.product.viability_score = score
            session.rounds.append(
                RoundLog(round_number=round_number, contributions=contributions, viability_score=score)
            )
            if score >= self.viability_threshold:
                break

        return session

    def _run_round(self, session: OfficeSession, round_number: int) -> dict:
        context = self._describe_context(session, round_number)

        strategist_reply = self.agents["strategist"].respond(
            f"{context}\n\nProponi o affina la value proposition, il target di mercato e "
            "le funzionalita' chiave del prodotto."
        )
        engineer_reply = self.agents["engineer"].respond(
            f"{context}\n\nContributo dello strategist:\n{strategist_reply}\n\n"
            "Valuta la fattibilita' tecnica e proponi uno scope MVP realistico."
        )
        marketer_reply = self.agents["marketer"].respond(
            f"{context}\n\nContributo dello strategist:\n{strategist_reply}\n\n"
            f"Contributo dell'ingegnere:\n{engineer_reply}\n\n"
            "Proponi pricing, canali di acquisizione e posizionamento di marketing."
        )
        optimizer_reply = self.agents["optimizer"].respond(
            f"{context}\n\nContributo dello strategist:\n{strategist_reply}\n\n"
            f"Contributo dell'ingegnere:\n{engineer_reply}\n\n"
            f"Contributo del marketer:\n{marketer_reply}\n\n"
            "Critica il lavoro del team, individua rischi e stima onestamente il "
            "punteggio di viabilita' commerciale."
        )
        coordinator_reply = self.agents["coordinator"].respond(
            f"{context}\n\nContributo dello strategist:\n{strategist_reply}\n\n"
            f"Contributo dell'ingegnere:\n{engineer_reply}\n\n"
            f"Contributo del marketer:\n{marketer_reply}\n\n"
            f"Critica dell'optimizer:\n{optimizer_reply}\n\n"
            "Sintetizza tutto in un aggiornamento della scheda di prodotto in formato JSON."
        )

        update = self._parse_json(coordinator_reply)
        if update:
            session.product.apply_update(update)

        return {
            "strategist": strategist_reply,
            "engineer": engineer_reply,
            "marketer": marketer_reply,
            "optimizer": optimizer_reply,
            "coordinator": coordinator_reply,
        }

    def _describe_context(self, session: OfficeSession, round_number: int) -> str:
        return (
            f"Argomento/idea di partenza: {session.topic}\n"
            f"Ciclo di lavoro numero: {round_number} (massimo {self.max_rounds}).\n"
            f"Scheda di prodotto attuale:\n{json.dumps(session.product.to_dict(), ensure_ascii=False, indent=2)}"
        )

    @staticmethod
    def _extract_score(optimizer_reply: str) -> float:
        match = SCORE_PATTERN.search(optimizer_reply)
        if not match:
            return 0.0
        return max(0.0, min(100.0, float(match.group(1))))

    @staticmethod
    def _parse_json(text: str) -> Optional[dict]:
        match = JSON_BLOCK_PATTERN.search(text)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    def write_report(self, session: OfficeSession, output_dir: str = "outputs") -> Path:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = Path(output_dir) / f"office-session-{timestamp}.md"

        parts = [
            session.product.to_markdown(),
            "",
            "---",
            "",
            "## Cronologia dei cicli di collaborazione",
        ]
        for round_log in session.rounds:
            parts.append(f"\n### Ciclo {round_log.round_number} (punteggio: {round_log.viability_score:.0f}/100)")
            for role_key, agent in self.agents.items():
                reply = round_log.contributions.get(role_key)
                if reply is None:
                    continue
                parts.append(f"\n**{agent.name} ({agent.role})**\n\n{reply}")

        path.write_text("\n".join(parts), encoding="utf-8")
        return path
