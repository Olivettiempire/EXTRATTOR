"""Orchestratore dell'ufficio virtuale: fa collaborare gli agenti in
cicli successivi finche' il prodotto non raggiunge una soglia di
viabilita' accettabile oppure si esauriscono i cicli disponibili."""
from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional

from .agent import BaseAgent, QueryFn
from .product import ProductSpec
from .roles import build_office_agents

# Callback invocata appena un agente completa il suo contributo, cosi' la
# CLI puo' mostrare l'avanzamento in tempo reale invece di attendere la
# fine del round. Firma: (round_number, role_key, agent, text).
ProgressCallback = Callable[[int, str, BaseAgent, str], None]

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

    def run(self, topic: str, progress_callback: Optional[ProgressCallback] = None) -> OfficeSession:
        """Wrapper sincrono attorno a run_async, comodo per la CLI."""
        return asyncio.run(self.run_async(topic, progress_callback))

    async def run_async(
        self, topic: str, progress_callback: Optional[ProgressCallback] = None
    ) -> OfficeSession:
        session = OfficeSession(topic=topic)

        for round_number in range(1, self.max_rounds + 1):
            contributions = await self._run_round(session, round_number, progress_callback)
            score = self._extract_score(contributions["optimizer"])
            session.product.viability_score = score
            session.rounds.append(
                RoundLog(round_number=round_number, contributions=contributions, viability_score=score)
            )
            if score >= self.viability_threshold:
                break

        return session

    async def _run_round(
        self,
        session: OfficeSession,
        round_number: int,
        progress_callback: Optional[ProgressCallback],
    ) -> dict:
        context = self._describe_context(session, round_number)
        contributions: dict = {}

        def emit(role_key: str, reply: str) -> None:
            contributions[role_key] = reply
            if progress_callback:
                progress_callback(round_number, role_key, self.agents[role_key], reply)

        strategist_reply = await self.agents["strategist"].respond_async(
            f"{context}\n\nProponi o affina la value proposition, il target di mercato e "
            "le funzionalita' chiave del prodotto."
        )
        emit("strategist", strategist_reply)

        # Ingegnere e marketer partono entrambi dal contributo dello
        # strategist e non dipendono l'uno dall'altro: li eseguiamo in
        # parallelo per ridurre la latenza del round.
        engineer_reply, marketer_reply = await asyncio.gather(
            self.agents["engineer"].respond_async(
                f"{context}\n\nContributo dello strategist:\n{strategist_reply}\n\n"
                "Valuta la fattibilita' tecnica e proponi uno scope MVP realistico."
            ),
            self.agents["marketer"].respond_async(
                f"{context}\n\nContributo dello strategist:\n{strategist_reply}\n\n"
                "Proponi pricing, canali di acquisizione e posizionamento di marketing."
            ),
        )
        emit("engineer", engineer_reply)
        emit("marketer", marketer_reply)

        optimizer_reply = await self.agents["optimizer"].respond_async(
            f"{context}\n\nContributo dello strategist:\n{strategist_reply}\n\n"
            f"Contributo dell'ingegnere:\n{engineer_reply}\n\n"
            f"Contributo del marketer:\n{marketer_reply}\n\n"
            "Critica il lavoro del team, individua rischi e stima onestamente il "
            "punteggio di viabilita' commerciale."
        )
        emit("optimizer", optimizer_reply)

        coordinator_reply = await self.agents["coordinator"].respond_async(
            f"{context}\n\nContributo dello strategist:\n{strategist_reply}\n\n"
            f"Contributo dell'ingegnere:\n{engineer_reply}\n\n"
            f"Contributo del marketer:\n{marketer_reply}\n\n"
            f"Critica dell'optimizer:\n{optimizer_reply}\n\n"
            "Sintetizza tutto in un aggiornamento della scheda di prodotto in formato JSON."
        )
        emit("coordinator", coordinator_reply)

        update = self._parse_json(coordinator_reply)
        if update:
            session.product.apply_update(update)

        return contributions

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
