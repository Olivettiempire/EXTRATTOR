"""Agenti dell'ufficio virtuale: ogni agente e' un ruolo specializzato
che ragiona tramite Claude e accumula esperienza/apprendimenti tra un
ciclo di lavoro e l'altro.

Gli agenti NON usano una API key: si appoggiano al Claude Agent SDK, che
comunica con la CLI di Claude Code autenticata tramite l'abbonamento
Pro/Max. Vedi README per i prerequisiti."""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, List, Optional

LEARNING_PATTERN = re.compile(r"^\s*LEZIONE:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
MAX_LEARNINGS = 8

# Una funzione che, dati prompt/system_prompt/model, restituisce un
# iteratore asincrono di messaggi (come quello prodotto da
# claude_agent_sdk.query). Iniettabile per rendere gli agenti testabili
# senza dipendere dalla CLI di Claude Code.
QueryFn = Callable[[str, str, Optional[str]], AsyncIterator[Any]]


def _sdk_query(prompt: str, system_prompt: str, model: Optional[str]) -> AsyncIterator[Any]:
    """Backend di default: usa il Claude Agent SDK (abbonamento Pro/Max,
    nessuna API key). L'import e' lazy cosi' i test non richiedono il
    pacchetto ne' la CLI installata."""
    from claude_agent_sdk import ClaudeAgentOptions, query

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=model,
        allowed_tools=[],  # nessuno strumento: vogliamo solo una risposta testuale
        # Diamo margine sul numero di turni: senza strumenti l'agente
        # risponde comunque in un turno, ma con prompt molto lunghi la CLI
        # puo' contare un turno extra. Con max_turns=1 questo faceva
        # fallire il run ("Reached maximum number of turns"); l'headroom
        # e' sicuro perche' non essendoci strumenti non ci sono loop.
        max_turns=8,
    )
    return query(prompt=prompt, options=options)


async def _collect_text(message_iter: AsyncIterator[Any]) -> str:
    """Estrae il testo finale dal flusso di messaggi dell'SDK.

    Preferisce il campo `result` del ResultMessage; in mancanza ricade
    sull'accumulo dei blocchi di testo dei messaggi dell'assistente. Usa
    duck-typing per non dipendere dai tipi interni dell'SDK."""
    final_result: Optional[str] = None
    assistant_text: List[str] = []
    async for message in message_iter:
        result = getattr(message, "result", None)
        if isinstance(result, str):
            final_result = result
        content = getattr(message, "content", None)
        if isinstance(content, list):
            for block in content:
                text = getattr(block, "text", None)
                if isinstance(text, str):
                    assistant_text.append(text)
    if final_result is not None:
        return final_result
    return "".join(assistant_text)


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
        model: Optional[str] = "sonnet",
        query_fn: Optional[QueryFn] = None,
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.model = model
        self.memory = AgentMemory()
        self.query_fn = query_fn or _sdk_query

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

    async def respond_async(self, prompt: str) -> str:
        message_iter = self.query_fn(prompt, self._build_system_prompt(), self.model)
        text = await _collect_text(message_iter)
        self.memory.experience += 1
        learning_match = LEARNING_PATTERN.search(text)
        if learning_match:
            self.memory.add(learning_match.group(1))
        return text

    def respond(self, prompt: str) -> str:
        """Wrapper sincrono attorno a respond_async, comodo per la CLI."""
        return asyncio.run(self.respond_async(prompt))
