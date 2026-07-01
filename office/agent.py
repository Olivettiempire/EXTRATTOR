"""Agenti dell'ufficio virtuale: ogni agente e' un ruolo specializzato
che ragiona tramite un modello Claude e accumula esperienza/apprendimenti
tra un ciclo di lavoro e l'altro."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from anthropic import Anthropic

LEARNING_PATTERN = re.compile(r"^\s*LEZIONE:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
MAX_LEARNINGS = 8


@dataclass
class AgentMemory:
    learnings: List[str] = field(default_factory=list)
    experience: int = 0

    def add(self, note: str) -> None:
        note = note.strip()
        if not note:
            return
        self.learnings.append(note)
        # Mantiene solo le lezioni piu' recenti: la specializzazione si
        # concentra su cio' che e' servito negli ultimi cicli, non su
        # tutta la storia.
        del self.learnings[:-MAX_LEARNINGS]


class BaseAgent:
    """Un membro dell'ufficio virtuale con un ruolo e una specializzazione."""

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model: str = "claude-sonnet-5",
        client: Optional[Anthropic] = None,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model = model
        self.memory = AgentMemory()
        self._client = client

    @property
    def client(self) -> Anthropic:
        if self._client is None:
            self._client = Anthropic()
        return self._client

    def _build_system_prompt(self) -> str:
        if self.memory.learnings:
            learnings = "\n".join(f"- {note}" for note in self.memory.learnings)
        else:
            learnings = "Nessuna nota da cicli precedenti: questo e' il primo contributo."
        return (
            f"{self.system_prompt}\n\n"
            f"Ruolo: {self.role}.\n"
            f"Esperienza accumulata: {self.memory.experience} cicli di lavoro completati.\n"
            f"Lezioni apprese dai cicli precedenti (usale per specializzarti e migliorare):\n"
            f"{learnings}\n\n"
            "Concludi sempre la risposta con una singola riga nel formato "
            "'LEZIONE: <cosa migliorare nel prossimo ciclo>'."
        )

    def respond(self, prompt: str, max_tokens: int = 1024) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=self._build_system_prompt(),
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        self.memory.experience += 1
        learning_match = LEARNING_PATTERN.search(text)
        if learning_match:
            self.memory.add(learning_match.group(1))
        return text
