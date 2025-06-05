# 📋 Checklist Deployment iDERP 2.0 per ERPNext 15

## Pre-Deployment

### 1. Verifica Ambiente
- [ ] ERPNext versione 15.x installato
- [ ] Python 3.10+ disponibile
- [ ] Node.js 18+ installato
- [ ] Backup completo del database effettuato
- [ ] Backup dei file custom effettuato

### 2. Preparazione Codice
- [ ] Repository clonata in `apps/iderp`
- [ ] Branch corretto selezionato (`master` o `v15`)
- [ ] Nessun conflitto git presente
- [ ] File `pyproject.toml` presente nella root

## Deployment

### 3. Installazione App
```bash
# Naviga alla directory bench
cd ~/frappe-bench

# Installa app nel sito
bench --site [nome-sito] install-app iderp

# Esegui migrazioni
bench --site [nome-sito] migrate
```

### 4. Build Assets
```bash
# Build JavaScript e CSS
bench build --app iderp

# Clear cache
bench --site [nome-sito] clear-cache
bench clear-compiled-cache
```

### 5. Riavvio Servizi
```bash
# Riavvia tutti i servizi
bench restart

# Oppure riavvio selettivo
sudo supervisorctl restart all
```

## Post-Deployment

### 6. Verifica Funzionalità

#### Custom Fields
- [ ] Verifica campi metratura su Item
- [ ] Verifica campi su Quotation Item
- [ ] Verifica campi su Sales Order Item
- [ ] Verifica campi su Sales Invoice Item
- [ ] Verifica campi su Delivery Note Item

#### DocType Personalizzati
- [ ] Customer Group Price Rule accessibile
- [ ] Item Pricing Tier funzionante
- [ ] Customer Group Minimum operativo
- [ ] Item Optional configurabile
- [ ] Optional Template utilizzabile

#### JavaScript
- [ ] Calcolo metrature funzionante in Preventivi
- [ ] Calcolo metrature funzionante in Ordini
- [ ] Prezzi gruppo cliente applicati correttamente
- [ ] Validazione dimensioni operativa

#### Workspace
- [ ] Workspace iDERP visibile
- [ ] Tutti gli shortcut funzionanti
- [ ] Icone caricate correttamente

### 7. Configurazione Permessi
- [ ] Ruolo "Sales Manager" può accedere ai DocType custom
- [ ] Ruolo "Sales User" ha permessi appropriati
- [ ] Ruolo "System Manager" ha accesso completo

### 8. Test Funzionali

#### Test Articolo Metratura
1. [ ] Crea nuovo articolo con UOM = "Mq"
2. [ ] Imposta dimensioni predefinite
3. [ ] Verifica limiti dimensionali

#### Test Preventivo
1. [ ] Crea preventivo con articolo a metratura
2. [ ] Inserisci base e altezza
3. [ ] Verifica calcolo automatico mq
4. [ ] Verifica calcolo prezzo totale

#### Test Prezzi Gruppo
1. [ ] Crea regola prezzo per gruppo cliente
2. [ ] Associa cliente al gruppo
3. [ ] Verifica applicazione prezzo in preventivo

#### Test Ordine Minimo
1. [ ] Configura minimo ordine per gruppo
2. [ ] Tenta creazione ordine sotto soglia
3. [ ] Verifica messaggio validazione

### 9. Monitoraggio Post-Deploy
- [ ] Controlla log errori: `bench --site [nome-sito] show-error-log`
- [ ] Verifica performance: tempi caricamento pagine
- [ ] Monitora utilizzo risorse server

## Troubleshooting

### Errori Comuni

#### ImportError moduli Python
```bash
bench pip install -r apps/iderp/requirements.txt
```

#### JavaScript non caricato
```bash
bench build --force --app iderp
bench clear-cache
```

#### Custom fields non visibili
```bash
bench --site [nome-sito] reload-doc iderp
bench --site [nome-sito] migrate
```

#### Permessi negati
- Verifica Role Permission Manager
- Controlla assegnazione ruoli utenti

### Rollback (se necessario)
```bash
# Disinstalla app
bench --site [nome-sito] uninstall-app iderp

# Ripristina backup
bench --site [nome-sito] restore [backup-file]
```

## Documentazione

### Per Utenti Finali
- [ ] Guida creazione articoli metratura
- [ ] Tutorial configurazione prezzi gruppo
- [ ] Manuale gestione opzionali

### Per Amministratori
- [ ] Documentazione API Python
- [ ] Riferimento JavaScript functions
- [ ] Guida configurazione avanzata

## Sign-off

- [ ] Test completati con successo
- [ ] Utente chiave ha verificato funzionalità
- [ ] Backup post-deployment effettuato
- [ ] Documentazione aggiornata

**Data Deployment**: _______________

**Eseguito da**: _______________

**Approvato da**: _______________