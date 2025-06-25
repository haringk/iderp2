# iderp 2.0 - Custom ERPNext App per Gestione Metrature

App personalizzata per ERPNext 15 che gestisce prodotti venduti al metro quadro, metro lineare o cadauno, con sistema avanzato di prezzi per gruppi cliente e articoli opzionali.

## 🚀 Caratteristiche Principali

### Gestione Metrature
- **Articoli a Metro Quadro**: Campi base e altezza con calcolo automatico mq
- **Articoli a Metro Lineare**: Gestione dimensioni lineari
- **Calcolo Automatico**: Prezzi calcolati in tempo reale lato client
- **Validazione Dimensioni**: Controllo limiti min/max per articolo

### Prezzi Gruppo Cliente
- **Regole Prezzo Personalizzate**: Prezzi differenziati per gruppo cliente
- **Sconti Automatici**: Applicazione sconti percentuali o fissi
- **Fasce Quantità**: Prezzi scalari basati su quantità
- **Priorità Regole**: Sistema di priorità per gestire sovrapposizioni

### Articoli Opzionali
- **Template Opzionali**: Gruppi predefiniti di articoli correlati
- **Selezione Dinamica**: Aggiunta opzionali durante creazione ordine
- **Prezzi Speciali**: Regole prezzo dedicate per opzionali

### Ordini Minimi
- **Minimi per Gruppo**: Valore o quantità minima ordine per gruppo cliente
- **Validazione Automatica**: Controllo in fase di conferma documento
- **Notifiche**: Avvisi per ordini sotto soglia

## 📋 Requisiti

- **ERPNext**: Versione 15.x
- **Frappe Framework**: Versione 15.x
- **Python**: 3.10+
- **Node.js**: 18+
- **MariaDB**: 10.6+ o MySQL 8.0+

## 🛠️ Installazione

### 1. Clona la repository nell'ambiente bench

```bash
cd ~/frappe-bench/apps
git clone https://github.com/haringk/iderp2.git iderp
```

### 2. Installa l'app nel sito

```bash
cd ~/frappe-bench
bench --site [nome-sito] install-app iderp
```

### 3. Esegui le migrazioni

```bash
bench --site [nome-sito] migrate
```

### 4. Ricostruisci assets

```bash
bench build --app iderp
bench clear-cache
```

### 5. Riavvia i servizi

```bash
bench restart
```

## 🔍 Verifica ambiente

Dopo aver installato l'app è possibile controllare che il sito sia configurato correttamente eseguendo lo script `check_iderp_env.sh` incluso nella root del progetto.

```bash
cd ~/frappe-bench
./apps/iderp/check_iderp_env.sh [nome-sito]
```

Lo script verifica la presenza di Python e Node nelle versioni consigliate, controlla che il comando `bench` sia disponibile e che sul sito indicato siano installate le app `frappe`, `erpnext` e `iderp`. In seguito esegue `bench --site [nome-sito] execute iderp.__init__.check_installation` mostrando in output eventuali DocType o campi mancanti.

## 🔧 Configurazione

### Custom Fields Automatici

L'app crea automaticamente i seguenti custom fields:

#### Su Item (Articolo):
- `base_default`: Base predefinita in mm
- `altezza_default`: Altezza predefinita in mm
- `min_base`, `max_base`: Limiti base
- `min_altezza`, `max_altezza`: Limiti altezza

#### Su documenti vendita (Quotation, Sales Order, etc.):
- `base`: Base articolo in mm
- `altezza`: Altezza articolo in mm
- `mq_totali`: Metri quadri totali calcolati

### Configurazione Workspace

Il workspace iDERP viene creato automaticamente con shortcuts a:
- Gestione articoli e documenti
- Configurazione prezzi gruppo cliente
- Report e analisi metrature

## 📊 Utilizzo

### Creazione Articolo a Metratura

1. Crea nuovo articolo
2. Imposta UOM = "Mq" per metro quadro
3. Compila dimensioni predefinite (opzionale)
4. Imposta limiti dimensionali (opzionale)

### Configurazione Prezzi Gruppo Cliente

1. Vai a **iDERP → Regole Prezzo Gruppo Cliente**
2. Crea nuova regola
3. Seleziona gruppo cliente
4. Aggiungi articoli con prezzi personalizzati
5. Imposta priorità e periodo validità

### Creazione Preventivo con Metrature

1. Crea nuovo preventivo
2. Aggiungi articolo con UOM "Mq"
3. Inserisci base e altezza in mm
4. Il sistema calcola automaticamente:
   - Mq unitari
   - Mq totali
   - Prezzo totale

### Gestione Articoli Opzionali

1. Configura template opzionali
2. Associa template ad articoli principali
3. Durante creazione ordine, seleziona opzionali desiderati

## 🔄 Aggiornamento

### Da ERPNext 14 a 15

```bash
# Aggiorna codice
cd ~/frappe-bench/apps/iderp
git pull origin master

# Esegui migrazioni
cd ~/frappe-bench
bench --site [nome-sito] migrate
bench build --app iderp
bench restart
```

## 🐛 Risoluzione Problemi

### Campi metratura non visibili

```bash
bench --site [nome-sito] clear-cache
bench --site [nome-sito] reload-doc iderp
```

### Errori JavaScript

```bash
bench build --force --app iderp
```

### Problemi permessi

Verifica permessi ruoli in:
- Impostazioni → Permessi Ruolo
- Assegna ruoli appropriati agli utenti

## 📝 API Disponibili

### Python API

```python
# Recupera dettagli articolo con prezzi gruppo
from iderp.api.item import get_item_details
details = get_item_details(item_code, customer, company)

# Calcola metriche articolo
from iderp.api.item import calculate_item_metrics
metrics = calculate_item_metrics(base_mm, altezza_mm, qty, uom)

# Applica prezzi gruppo cliente
from iderp.pricing import get_customer_group_price
price_info = get_customer_group_price(item_code, customer, qty)
```

### JavaScript API

```javascript
// Calcola metrature
iderp.calculate_metrics(frm, cdt, cdn);

// Applica prezzi gruppo
iderp.apply_customer_group_pricing(frm, cdt, cdn);

// Valida minimi ordine
iderp.validate_minimum_qty(frm);
```

## 🧪 Test

E' possibile eseguire i test unitari con `pytest`.

```bash
pip install -e .[dev]
pytest
```

## 🤝 Contribuire

1. Fork la repository
2. Crea branch per feature (`git checkout -b feature/AmazingFeature`)
3. Commit modifiche (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri Pull Request

## 📄 Licenza

Distribuito sotto licenza MIT. Vedi `LICENSE` per maggiori informazioni.

## 🙏 Ringraziamenti

- Team Frappe/ERPNext per il framework eccellente
- Comunità ERPNext per supporto e suggerimenti
