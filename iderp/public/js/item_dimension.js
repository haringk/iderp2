console.log("IDERP: Calculator DEBUG VERSION");

// Flag per prevenire loop infiniti
var iderp_calculating = false;
var selected_item_row = null;

// FUNZIONE DEBUG per controllare stato
function debug_form_state(frm, context = "") {
    console.log(`[DEBUG ${context}] Form state:`, {
        customer: frm.doc.customer,
        party_name: frm.doc.party_name,
        customer_name: frm.doc.customer_name,
        items_count: frm.doc.items ? frm.doc.items.length : 0,
        doctype: frm.doc.doctype,
        docstatus: frm.doc.docstatus
    });
    
    if (frm.doc.items) {
        frm.doc.items.forEach((item, idx) => {
            console.log(`[DEBUG ${context}] Item ${idx}:`, {
                name: item.name,
                item_code: item.item_code,
                rate: item.rate,
                base: item.base,
                altezza: item.altezza,
                price_locked: item.price_locked
            });
        });
    }
}

// CALCOLO SICURO con debug
function calculate_item_pricing_safe(frm, cdt, cdn, force_recalc = false) {
    console.log(`[CALC] Inizio calcolo per ${cdn}, force: ${force_recalc}`);
    
    if (iderp_calculating) {
        console.log("[CALC] BLOCCATO - iderp_calculating = true");
        return;
    }
    
    let row = locals[cdt][cdn];
    if (!row) {
        console.log("[CALC] ERRORE - Row non trovata in locals");
        return;
    }
    
    console.log("[CALC] Row trovata:", {
        name: row.name,
        item_code: row.item_code,
        tipo_vendita: row.tipo_vendita,
        base: row.base,
        altezza: row.altezza,
        price_locked: row.price_locked
    });
    
    if (!row.item_code || row.tipo_vendita !== "Metro Quadrato") {
        console.log("[CALC] SKIP - Non è metro quadrato o manca item_code");
        return;
    }
    
    // Non ricalcolare se è bloccato
    if (row.price_locked && !force_recalc) {
        console.log("[CALC] SKIP - Prezzo bloccato");
        return;
    }
    
    let base = parseFloat(row.base) || 0;
    let altezza = parseFloat(row.altezza) || 0;
    let qty = parseFloat(row.qty) || 1;
    
    if (!base || !altezza) {
        console.log("[CALC] SKIP - Mancano base/altezza");
        row.mq_singolo = 0;
        row.mq_calcolati = 0;
        row.note_calcolo = "Inserire base e altezza";
        
        // REFRESH SICURO - solo questa riga
        frm.refresh_field("items");
        return;
    }
    
    // Calcola m² sempre
    let mq_singolo = (base * altezza) / 10000;
    let mq_totali = mq_singolo * qty;
    
    row.mq_singolo = parseFloat(mq_singolo.toFixed(4));
    row.mq_calcolati = parseFloat(mq_totali.toFixed(3));
    
    // DEBUG: Controllo cliente
    let customer = frm.doc.customer || frm.doc.party_name || frm.doc.customer_name;
    console.log("[CALC] Cliente rilevato:", {
        customer: frm.doc.customer,
        party_name: frm.doc.party_name,
        customer_name: frm.doc.customer_name,
        final_customer: customer
    });
    
    if (!customer) {
        console.log("[CALC] SKIP - Nessun cliente selezionato");
        row.note_calcolo = `📊 ${mq_totali.toFixed(3)} m² totali - Seleziona cliente per prezzi`;
        frm.refresh_field("items");
        return;
    }
    
    // FLAG IMPORTANTE: blocca altri eventi
    iderp_calculating = true;
    console.log("[CALC] API call in corso...");
    
    // Chiamata API SICURA
    frappe.call({
        method: 'iderp.pricing_utils.calculate_item_pricing',
        args: {
            item_code: row.item_code,
            base: base,
            altezza: altezza,
            qty: qty,
            customer: customer
        },
        freeze: false,
        async: true,
        callback: function(r) {
            console.log("[API] Risposta ricevuta:", r);
            
            try {
                if (r.message && r.message.success && !r.message.error) {
                    console.log("[API] Successo - aggiornamento valori");
                    
                    // Verifica che la riga esista ancora
                    let current_row = locals[cdt][cdn];
                    if (!current_row || current_row.name !== row.name) {
                        console.log("[API] ERRORE - Riga cambiata durante API call");
                        return;
                    }
                    
                    // Aggiorna SOLO i valori necessari
                    current_row.rate = r.message.rate;
                    current_row.prezzo_mq = r.message.tier_info.price_per_sqm;
                    current_row.note_calcolo = r.message.note_calcolo + "\n\n🤖 CALCOLO AUTOMATICO";
                    current_row.auto_calculated = 1;
                    current_row.manual_rate_override = 0;
                    current_row.price_locked = 0;
                    current_row.amount = parseFloat((current_row.rate * qty).toFixed(2));
                    
                    console.log("[API] Valori aggiornati:", {
                        rate: current_row.rate,
                        amount: current_row.amount,
                        prezzo_mq: current_row.prezzo_mq
                    });
                    
                    // REFRESH MINIMO
                    frm.refresh_field("items");
                    
                    frappe.show_alert({
                        message: `✅ ${row.item_code}: €${current_row.rate}`,
                        indicator: 'green'
                    });
                    
                } else {
                    console.log("[API] Errore:", r.message?.error);
                    row.note_calcolo = `📊 ${mq_totali.toFixed(3)} m² - Errore: ${r.message?.error || "API error"}`;
                    frm.refresh_field("items");
                }
            } catch (err) {
                console.error("[API] Errore callback:", err);
            } finally {
                // SEMPRE sblocca
                setTimeout(() => {
                    iderp_calculating = false;
                    console.log("[CALC] Flag sbloccato");
                }, 200);
            }
        },
        error: function(err) {
            console.error("[API] Errore chiamata:", err);
            setTimeout(() => {
                iderp_calculating = false;
            }, 200);
        }
    });
}

// EVENTI SEMPLIFICATI
frappe.ui.form.on('Quotation Item', {
    // Solo calcolo m² immediato
    base: function(frm, cdt, cdn) {
        console.log("[EVENT] Base changed");
        debug_form_state(frm, "base_change");
        
        let row = locals[cdt][cdn];
        if (row && row.base && row.altezza) {
            let mq_singolo = (parseFloat(row.base) * parseFloat(row.altezza)) / 10000;
            let mq_totali = mq_singolo * (parseFloat(row.qty) || 1);
            row.mq_singolo = parseFloat(mq_singolo.toFixed(4));
            row.mq_calcolati = parseFloat(mq_totali.toFixed(3));
            
            console.log("[EVENT] m² calcolati:", mq_totali);
            
            // DELAY per calcolo prezzo
            if (!row.price_locked) {
                setTimeout(() => {
                    calculate_item_pricing_safe(frm, cdt, cdn);
                }, 500);
            }
        }
    },
    
    altezza: function(frm, cdt, cdn) {
        console.log("[EVENT] Altezza changed");
        debug_form_state(frm, "altezza_change");
        
        let row = locals[cdt][cdn];
        if (row && row.base && row.altezza) {
            let mq_singolo = (parseFloat(row.base) * parseFloat(row.altezza)) / 10000;
            let mq_totali = mq_singolo * (parseFloat(row.qty) || 1);
            row.mq_singolo = parseFloat(mq_singolo.toFixed(4));
            row.mq_calcolati = parseFloat(mq_totali.toFixed(3));
            
            console.log("[EVENT] m² calcolati:", mq_totali);
            
            // DELAY per calcolo prezzo
            if (!row.price_locked) {
                setTimeout(() => {
                    calculate_item_pricing_safe(frm, cdt, cdn);
                }, 500);
            }
        }
    },
    
    // Item code - NO refresh automatico
    item_code: function(frm, cdt, cdn) {
        console.log("[EVENT] Item code changed");
        debug_form_state(frm, "item_change");
        
        let row = locals[cdt][cdn];
        if (row) {
            console.log("[EVENT] Nuovo item:", row.item_code);
            // NON triggerare calcolo automatico qui
        }
    },
    
    // Rate manuale
    rate: function(frm, cdt, cdn) {
        if (iderp_calculating) {
            console.log("[EVENT] Rate change ignorato - calculating");
            return;
        }
        
        console.log("[EVENT] Rate changed manually");
        
        let row = locals[cdt][cdn];
        if (row) {
            row.manual_rate_override = 1;
            row.auto_calculated = 0;
            row.price_locked = 0;
            
            let qty = parseFloat(row.qty) || 1;
            let rate = parseFloat(row.rate) || 0;
            row.amount = parseFloat((rate * qty).toFixed(2));
            
            row.note_calcolo = (row.note_calcolo || "").split('\n🤖')[0] + "\n🖊️ PREZZO MANUALE";
            
            console.log("[EVENT] Rate manuale impostato:", rate);
        }
    }
});

// Eventi form
frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        console.log("[FORM] Refresh");
        debug_form_state(frm, "refresh");
        
        if (frm.doc.docstatus === 0) {
            frm.page.set_indicator("🔍 DEBUG MODE - Controlla console", "orange");
        }
    },
    
    customer: function(frm) {
        console.log("[FORM] Cliente cambiato");
        debug_form_state(frm, "customer_change");
        
        // Ricalcola tutto se c'è un cliente
        if (frm.doc.customer && frm.doc.items) {
            setTimeout(() => {
                frm.doc.items.forEach(function(item) {
                    if (item.tipo_vendita === "Metro Quadrato" && 
                        item.base && item.altezza && !item.price_locked) {
                        console.log("[FORM] Ricalcolo per item:", item.item_code);
                        calculate_item_pricing_safe(frm, item.doctype, item.name, true);
                    }
                });
            }, 1000);
        }
    }
});

console.log("✅ IDERP DEBUG Calculator caricato");