# EXTRATTOR - Ufficio Virtuale Multi-Agente

Un piccolo team di agenti Claude che collaborano come in un ufficio
virtuale per definire, criticare e raffinare un prodotto digitale
partendo da un'idea di base.

## Come funziona

Ogni "ciclo di lavoro" coinvolge cinque agenti specializzati, in
sequenza:

1. **Marco - Product Strategist**: definisce/affina value proposition,
   target di mercato e funzionalita' chiave.
2. **Giulia - Software Engineer**: valuta la fattibilita' tecnica e
   propone uno scope MVP realistico.
3. **Luca - Growth Marketer**: propone pricing, canali di acquisizione
   e posizionamento.
4. **Sara - Revenue & Quality Optimizer**: critica il lavoro del team e
   stima un punteggio di viabilita' commerciale (0-100).
5. **Alessia - Coordinatrice**: sintetizza tutti i contributi in un
   aggiornamento strutturato della scheda di prodotto.

I cicli si ripetono finche' il punteggio di viabilita' supera la
soglia scelta (default 90/100) oppure si raggiunge il numero massimo
di cicli. Ogni agente accumula "lezioni apprese" dai cicli precedenti
(estratte da una riga `LEZIONE:` nella propria risposta) e le usa per
specializzarsi e migliorare i contributi successivi.

Alla fine viene generato un report Markdown con la scheda di prodotto
finale e la cronologia completa della discussione tra gli agenti.

## Nota importante sul "successo garantito"

Nessun software puo' garantire onestamente un tasso di successo del
100% nella vendita di un prodotto reale: il mercato dipende da troppi
fattori esterni non controllabili dal codice. Questo sistema non
promette un risultato garantito, ma implementa un ciclo strutturato di
collaborazione, critica e iterazione pensato per massimizzare la
qualita' e la probabilita' di successo della proposta, in modo
onesto e verificabile (il punteggio di viabilita' e' una stima
euristica prodotta dagli agenti stessi, non una certezza).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # inserisci la tua ANTHROPIC_API_KEY
```

## Uso

```bash
python main.py --topic "Un'app per la gestione fiscale delle PMI" --rounds 3
```

Opzioni principali:

- `--topic` (obbligatorio): idea o argomento di partenza.
- `--rounds`: numero massimo di cicli di collaborazione (default 3).
- `--threshold`: punteggio di viabilita' che interrompe i cicli in
  anticipo (default 90).
- `--model`: modello Claude usato dagli agenti (default
  `claude-sonnet-5`).
- `--output-dir`: cartella dove salvare il report (default `outputs/`).

Il report viene salvato in `outputs/office-session-<timestamp>.md`.

## Test

```bash
pip install -r requirements.txt
python -m unittest discover -s tests
```

I test usano un client Anthropic simulato (mock), quindi non serve una
chiave API valida per eseguirli.

## Struttura del progetto

```
office/
  agent.py           # Classe base degli agenti (memoria, chiamata al modello)
  product.py          # Scheda di prodotto e sua serializzazione
  roles.py             # Definizione dei ruoli specializzati
  virtual_office.py    # Orchestratore dei cicli di collaborazione
main.py                # Entry point da riga di comando
tests/                  # Test unitari con client Anthropic simulato
```
