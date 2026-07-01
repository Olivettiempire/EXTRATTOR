# EXTRATTOR - Ufficio Virtuale Multi-Agente

Un piccolo team di agenti Claude che collaborano come in un ufficio
virtuale per definire, criticare e raffinare un prodotto digitale
partendo da un'idea di base.

Gli agenti usano il **Claude Agent SDK**, che si autentica tramite la CLI
di Claude Code e il tuo **abbonamento Pro/Max** — **nessuna API key** e
nessun costo a token.

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

Ingegnere e marketer partono entrambi dal contributo dello strategist e
non dipendono l'uno dall'altro, quindi vengono eseguiti **in parallelo**
(asyncio) per ridurre la latenza del round.

I cicli si ripetono finche' il punteggio di viabilita' supera la
soglia scelta (default 90/100) oppure si raggiunge il numero massimo
di cicli. Ogni agente accumula "lezioni apprese" dai cicli precedenti
(estratte da una riga `LEZIONE:` nella propria risposta) e le usa per
specializzarsi e migliorare i contributi successivi.

Durante l'esecuzione, ogni contributo viene stampato a schermo appena
l'agente lo completa (avanzamento live). Usa `--quiet` per disattivare
questa stampa.

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

## Prerequisiti (uso con abbonamento, senza API key)

1. Installa la CLI di Claude Code:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```
2. Effettua il login con il tuo account (abbonamento Pro/Max):
   ```bash
   claude login
   ```
   L'autenticazione avviene via browser; il Claude Agent SDK riusa
   automaticamente questa sessione, quindi **non serve** impostare
   `ANTHROPIC_API_KEY`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
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
- `--model`: modello Claude usato dagli agenti (default `sonnet`; es.
  `opus`).
- `--output-dir`: cartella dove salvare il report (default `outputs/`).
- `--quiet`: non stampare i contributi degli agenti man mano che arrivano.

Il report viene salvato in `outputs/office-session-<timestamp>.md`.

## Test

```bash
python -m unittest discover -s tests
```

I test iniettano una `query_fn` simulata al posto del Claude Agent SDK,
quindi **non** serve la CLI installata ne' il login per eseguirli.

## Struttura del progetto

```
office/
  agent.py           # Classe base degli agenti (memoria, chiamata via Agent SDK)
  product.py          # Scheda di prodotto e sua serializzazione
  roles.py             # Definizione dei ruoli specializzati
  virtual_office.py    # Orchestratore dei cicli di collaborazione
main.py                # Entry point da riga di comando
tests/                  # Test unitari con query_fn simulata
```
