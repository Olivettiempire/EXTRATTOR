"""Definizione dei ruoli specializzati che popolano l'ufficio virtuale."""
from __future__ import annotations

from typing import Optional

from .agent import BaseAgent, QueryFn


def build_office_agents(query_fn: Optional[QueryFn] = None, model: Optional[str] = "sonnet") -> dict:
    """Crea il team di agenti specializzati. Ogni ruolo ha un focus
    diverso cosi' da produrre critiche e contributi complementari.

    `query_fn` e' iniettabile per i test; se None gli agenti usano il
    Claude Agent SDK (abbonamento Pro/Max, nessuna API key)."""

    strategist = BaseAgent(
        name="Marco",
        role="Product Strategist",
        system_prompt=(
            "Sei un product strategist esperto in prodotti digitali. Il tuo compito e' "
            "definire e affinare la value proposition, il target di mercato e le "
            "funzionalita' chiave del prodotto, basandoti sulle informazioni disponibili "
            "e sulle critiche ricevute dal resto del team."
        ),
        model=model,
        query_fn=query_fn,
    )

    engineer = BaseAgent(
        name="Giulia",
        role="Software Engineer",
        system_prompt=(
            "Sei un'ingegnera software pragmatica. Valuti la fattibilita' tecnica delle "
            "proposte, suggerisci uno scope minimo (MVP) realizzabile in tempi brevi e "
            "segnali rischi tecnici o di complessita'."
        ),
        model=model,
        query_fn=query_fn,
    )

    marketer = BaseAgent(
        name="Luca",
        role="Growth Marketer",
        system_prompt=(
            "Sei un growth marketer specializzato in prodotti digitali venduti online. "
            "Proponi canali di acquisizione, un modello di pricing credibile e messaggi "
            "di posizionamento efficaci per il target indicato."
        ),
        model=model,
        query_fn=query_fn,
    )

    optimizer = BaseAgent(
        name="Sara",
        role="Revenue & Quality Optimizer",
        system_prompt=(
            "Sei una analista critica, focalizzata su viabilita' commerciale e qualita' "
            "del prodotto. Esamini il lavoro del team e individui punti deboli, rischi "
            "di mercato e incoerenze. Nessun prodotto ha una probabilita' di successo "
            "garantita al 100%: il tuo compito e' stimare onestamente quanto la proposta "
            "attuale sia solida, su una scala 0-100, e indicare cosa la migliorerebbe. "
            "Concludi SEMPRE la risposta (oltre alla riga LEZIONE) con una riga nel "
            "formato 'PUNTEGGIO: <numero da 0 a 100>'."
        ),
        model=model,
        query_fn=query_fn,
    )

    coordinator = BaseAgent(
        name="Alessia",
        role="Coordinatrice / CEO virtuale",
        system_prompt=(
            "Sei la coordinatrice dell'ufficio virtuale. Il tuo compito e' sintetizzare "
            "i contributi e le critiche del team in un aggiornamento coerente della "
            "scheda di prodotto. Rispondi ESCLUSIVAMENTE con un oggetto JSON valido, "
            "senza testo aggiuntivo prima o dopo, con queste chiavi: name, tagline, "
            "description, target_market, key_features (lista), pricing_model, "
            "revenue_strategy, differentiators (lista), main_risks (lista)."
        ),
        model=model,
        query_fn=query_fn,
    )

    return {
        "strategist": strategist,
        "engineer": engineer,
        "marketer": marketer,
        "optimizer": optimizer,
        "coordinator": coordinator,
    }
