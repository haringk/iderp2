# iderp
Custom app per ERPNext che gestisce prodotti venduti al metro quadro, aggiungendo campi “base” e “altezza” su tutti i documenti vendita.


## Funzionalità
- Campi “base” e “altezza” (da aggiungere via Custom Field su Quotation Item, Sales Order Item, ecc.)
- Calcolo automatico del prezzo totale lato client


## Setup
- Installa come una normale app bench.
- Aggiungi i Custom Field nei DocType Item desiderati.
- Verifica che iderp.js sia incluso.


## Note
- il file apps.txt nel quale deve esserci il nome del plugin è quello nella directory /sites/


## Utilità
```bash
bench update --reset
bench --site sito.local set-maintenance-mode off
bench --site sito.local install-app iderp
```

Per refresh
```bash
bench --site sito.local clear-cache
bench clear-compiled # questo non va 
bench restart
```

Disinstalla:
```bash
bench --site sito.local uninstall-app iderp
```
Rimuovi manualmente la diga "iderp" da ```sites/sito.local/apps.txt``` (aggiungila dopo la reinstallazione.
```bash
bench build
bench --site sito.local clear-cache
bench restart
```
Cancella la cartella "iderp" 


Console:
```bash
bench --site sito.local console
```

Installa:
```
bench get-app iderp https://github.com/haringk/iderp2.git
bench --site sito.local install-app iderp
```
Verifica che in ```sites/sito.local/apps.txt``` ci sia la voce del plugin.


## Avvio
```bash
source ~/frappe-bench/bench-env/bin/activate
cd ~/frappe-bench
bench start
```

# iderp

**Custom ERPNext App** per gestione prodotti a metratura (base/altezza/mq) e sincronizzazione automatica tra documenti (Preventivi, Ordini, Fatture, ecc).

## Installazione

```bash
cd ~/frappe-bench/apps
git clone <repo> iderp
cd ~/frappe-bench
bench --site <nome_sito> install-app iderp
```

