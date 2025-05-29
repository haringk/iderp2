# iderp
Custom app per ERPNext che gestisce prodotti venduti al metro quadro, aggiungendo campi “base” e “altezza” su tutti i documenti vendita.


## Funzionalità
- Campi “base” e “altezza” (da aggiungere via Custom Field su Quotation Item, Sales Order Item, ecc.)
- Calcolo automatico del prezzo totale lato client


## Setup
- Installa come una normale app bench.
- Aggiungi i Custom Field nei DocType Item desiderati.
- Verifica che iderp.js sia incluso.


## Avvio
- source ~/frappe-bench/bench-env/bin/activate
- cd ~/frappe-bench
- bench start

# iderp

**Custom ERPNext App** per gestione prodotti a metratura (base/altezza/mq) e sincronizzazione automatica tra documenti (Preventivi, Ordini, Fatture, ecc).

## Installazione

```bash
cd ~/frappe-bench/apps
git clone <repo> iderp
cd ~/frappe-bench
bench --site <nome_sito> install-app iderp
