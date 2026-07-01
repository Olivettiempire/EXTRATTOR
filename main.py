"""CLI per avviare l'ufficio virtuale: un team di agenti Claude che
collabora per definire e raffinare un prodotto digitale.

Gli agenti usano il Claude Agent SDK, che si autentica tramite la CLI di
Claude Code e il tuo abbonamento Pro/Max. Nessuna API key richiesta.
Prerequisiti: Claude Code installato (`npm install -g @anthropic-ai/claude-code`)
ed eseguito il login (`claude login`)."""
from __future__ import annotations

import argparse

from office.virtual_office import VirtualOffice


def main() -> int:
    parser = argparse.ArgumentParser(description="Avvia l'ufficio virtuale multi-agente.")
    parser.add_argument("--topic", required=True, help="Idea o argomento di partenza del prodotto digitale.")
    parser.add_argument("--rounds", type=int, default=3, help="Numero massimo di cicli di collaborazione.")
    parser.add_argument("--threshold", type=float, default=90.0, help="Punteggio di viabilita' che interrompe i cicli in anticipo.")
    parser.add_argument("--model", default="sonnet", help="Modello Claude usato dagli agenti (es. sonnet, opus).")
    parser.add_argument("--output-dir", default="outputs", help="Cartella dove salvare il report finale.")
    args = parser.parse_args()

    office = VirtualOffice(model=args.model, viability_threshold=args.threshold, max_rounds=args.rounds)
    session = office.run(args.topic)
    report_path = office.write_report(session, output_dir=args.output_dir)

    print(f"Report salvato in: {report_path}")
    print(f"Punteggio finale di viabilita': {session.product.viability_score:.0f}/100")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
