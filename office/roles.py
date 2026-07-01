"""Definizione dei ruoli specializzati che popolano l'ufficio virtuale."""
from __future__ import annotations

from typing import Optional

from anthropic import Anthropic

from .agent import BaseAgent


def build_office_agents(client: Optional[Anthropic] = None, model: str = "claude-sonnet-5") -> dict:
    """Crea il team di agenti specializzati. Ogni ruolo ha un focus
    diverso cosi' da produrre critiche e contributi complementari."""

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
        client=client,
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
        client=client,
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
        client=client,
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
        client=client,
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
        client=client,
    )

    return {
        "strategist": strategist,
        "engineer": engineer,
        "marketer": marketer,
        "optimizer": optimizer,
        "coordinator": coordinator,
    }
