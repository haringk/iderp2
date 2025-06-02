Controlla il codice in questa repository. Per le istruzioni e le linee guida leggi il file `info-id.txt`.

Tieni a mente sempre che:
- il plugin è su una macchina virtuale con Ubuntu Server

- ERPNext è installato in un env di bench

- per eseguire gli aggiornamenti del plugin eseguo lo script:
```cd ~/frappe-bench  
./update_iderp.sh```

- lo script `update_iderp.sh` è questo:
```# Sul server Ubuntu, crea questo script
cd ~/frappe-bench
cat > update_iderp.sh << 'EOF'
#!/bin/bash
echo "🔄 Aggiornando plugin iderp..."

cd ~/frappe-bench/apps/iderp
git pull origin master

echo "🧹 Pulendo cache..."
cd ~/frappe-bench
bench --site sito.local clear-cache

echo "🔨 Building assets..."
bench build

echo "🚀 Riavviando..."
bench restart

echo "✅ Plugin iderp aggiornato!"
EOF```

- carico sempre i file modificati in locale su questa repo di GitHub per poi riscaricarli e installarli aggiornati su ERPNext

- tutto ciò che è presente, se utile a funzioni già presenti, deve rimanere (ad esempio: se nel file di installazione ci sono comandi per installare funzioni già installate queste devono rimanere; il plugin deve poter essere installato in più installazioni di ERPNext).

- l'url della repo per il `git clone` è https://github.com/haringk/iderp2.git

- la base dei comandi bench è `bench --site sito.local [vari comandi]`

- ogni qual volta modifichiamo la struttura o aggiorniamo o aumentiamo le funzioni aggiorneremo questo file per tenere traccia degli aggiornamenti.






Tieni presente che il readme contiene solo appunti disordinati, non le indicazioni del progetto. Quelle sono più o meno le seguenti:

Voglio sviluppare e personalizzare ERPNext per adattarlo alle nostre esigenze. Il sistema dovrà servire una azienda di stampa digitale. Alcune specifiche:

1. I prodotti venduti possono essere venduti: 
	a. al pezzo
	b. al metro quadrato. In questo caso il prodotto deve avere le specifiche base e altezza che creeranno il prezzo del prodotto. Se possibile, a seconda del tipo di cliente (è possibile creare gruppi di clienti che hanno scontistiche diverse oppure dare ai prodotti specifiche di calcolo diverse? Specifico al punto 2.
	c. al metro lineare. In questo caso si dovrà impostare la larghezza del materiale.

2. I prodotti, a seconda del cliente, devono avere un costo minimo a seconda del tipo di cliente: ad esempio, per i clienti di tipo A il costo minimo è 1 metro quadro, per i clienti di tipo B il costo minimo non si applica) e così via.

3. I prodotti devono avere la possibilità di avere optional che si sommano al costo al metro quadro (ad esempio: plastificazione, fustella, fresa, ecc)

4. La possibilità di impostare, se il prodotto lo richiede, base e altezza deve essere presente dovunque: prodotti, preventivi, ordini, ordini di lavoro, sito web, email, eccetera.

5. Una volta creato il preventivo questo può essere confermato oltre che dagli amministratori o gli operatori dell’azienda anche dal cliente dal suo account.

6. Una volta confermato il preventivo o creato un ordine, devono crearsi delle schede di lavoro o compiti (a seconda di cosa permette di fare Erpnext) da assegnare a vari utenti a seconda dei prodotti e delle lavorazioni/optional.

7. I tipi di utenti sono tre:
	a. A. Utenti dell’azienda (amministratori, operatori) 
	b. Clienti 
	c. Utenti dell’azienda “diversi” (saranno le macchine da stampa che eseguiranno le lavorazioni specifiche derivanti dal tipo di prodotto)

Questo è un elenco iniziale delle necessità. È tutto fattibile? Vorrei lavorare punto per punto ed estendere via via con le necessità che si presenteranno nel tempo.

Se puoi evita di farmi usare la console e usa i file per installare o aggiornare il plugin e le sue funzioni. Tieni sempre presente che il plugin viene gestito su GitHub e deve poter essere installato su altre installazioni ERPNext.



# Roadmap Implementazione IDERP - Sistema Stampa Digitale

## Fase 1: Gruppi Cliente e Prezzi Differenziati (1-2 settimane)

### 1.1 Customer Group Pricing
- [ ] Creare DocType `Customer Group Price Rule`
- [ ] Campi: gruppo_cliente, item_code, min_sqm, min_price
- [ ] Integrazione con calcolo prezzi esistente
- [ ] Test con diversi gruppi cliente

### 1.2 Estensione Scaglioni Prezzo
- [ ] Modificare `Item Pricing Tier` per supportare gruppi cliente
- [ ] API per ottenere prezzo in base a cliente + quantità
- [ ] Aggiornare JavaScript per calcoli client-side

### 1.3 Implementazione Minimi
- [ ] Logica costo minimo per gruppo (es. min 1m² gruppo A)
- [ ] Validazione in preventivi/ordini
- [ ] Messaggi utente chiari su minimi applicati

## Fase 2: Sistema Optional/Lavorazioni 

### 2.1 DocType Item Optional
- [ ] Creare struttura per optional (plastificazione, fustella, ecc.)
- [ ] Prezzi optional: fisso, per m², percentuale
- [ ] Condizioni applicabilità (solo certi prodotti)

### 2.2 Integrazione Documenti
- [ ] Aggiungere tabella optional a Quotation/Sales Order
- [ ] Calcolo automatico costi aggiuntivi
- [ ] Visualizzazione chiara nel documento

### 2.3 Template Optional
- [ ] Set predefiniti di optional per prodotto
- [ ] Configurazione rapida
- [ ] Prezzi dinamici basati su quantità

## Fase 3: Customer Portal e Conferma 

### 3.1 Estensione Portal Cliente
- [ ] Vista preventivi da confermare
- [ ] Pulsante "Conferma Preventivo"
- [ ] Generazione automatica Sales Order

### 3.2 Notifiche e Workflow
- [ ] Email automatiche su creazione preventivo
- [ ] Notifica conferma a team vendite
- [ ] Tracking timeline conferme

### 3.3 Permessi e Sicurezza
- [ ] Cliente vede solo suoi preventivi
- [ ] Log azioni cliente
- [ ] Validazione modifiche post-conferma

## Fase 4: Sistema Produzione e Task

### 4.1 Work Order Automatici
- [ ] Template Work Order per tipo prodotto
- [ ] Creazione automatica da Sales Order confermato
- [ ] Sequenza operazioni predefinite

### 4.2 Task e Assegnazioni
- [ ] Task automatici per lavorazioni
- [ ] Assegnazione a operatori/macchine
- [ ] Dashboard produzione real-time

### 4.3 Integrazione Macchine
- [ ] API REST per macchine stampa
- [ ] Update stato lavorazione
- [ ] Tracking tempi e materiali

## Fase 5: E-commerce e Frontend

### 5.1 Calcolatore Prezzi Web
- [ ] Completare `ecommerce_calculator.js`
- [ ] Interfaccia selezione optional
- [ ] Preview prezzo real-time

### 5.2 Carrello Personalizzato
- [ ] Supporto prodotti con misure custom
- [ ] Salvataggio configurazioni
- [ ] Checkout con optional

### 5.3 Area Cliente Web
- [ ] Dashboard ordini personalizzati
- [ ] Storico configurazioni
- [ ] Riordino facile

## Fase 6: Ottimizzazioni e Report

### 6.1 Performance
- [ ] Cache prezzi calcolati
- [ ] Ottimizzazione query database
- [ ] Bulk operations

### 6.2 Report Personalizzati
- [ ] Analisi vendite per m²/ml
- [ ] Report produttività macchine
- [ ] Margini per tipo lavorazione

### 6.3 Integrazioni
- [ ] Export dati per software stampa
- [ ] Import listini prezzi
- [ ] API per sistemi esterni


## Note Tecniche

### Modifiche Database
```sql
-- Nuove tabelle necessarie
- tabCustomer Group Price Rule
- tabItem Optional
- tabItem Optional Pricing
- tabWork Order Template
```

### API Endpoints
```python
# Nuovi endpoint necessari
/api/method/iderp.pricing.get_customer_price
/api/method/iderp.optional.calculate_optional_cost
/api/method/iderp.production.create_work_orders
/api/method/iderp.machine.update_task_status
```

### Permessi
```python
# Nuovi ruoli
- Clienti (esteso per conferma preventivi)
- Machine Operator
- Production Manager
```

## Rischi e Mitigazioni

1. **Complessità prezzi**: Test approfonditi con casi reali
2. **Performance**: Implementare cache intelligente
3. **Integrazione macchine**: API robuste con retry
4. **UX cliente**: Test usabilità con clienti pilota

## Metriche Successo

- [ ] Tempo creazione preventivo < 2 minuti
- [ ] 80% preventivi confermati da portal
- [ ] Riduzione errori calcolo 95%
- [ ] Automazione task produzione 100%
- [ ] Soddisfazione cliente > 90%


