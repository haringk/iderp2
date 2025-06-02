console.log("IDERP: Calculator con API sicura per prezzi gruppo cliente");

// Flag per prevenire loop infiniti
var iderp_calculating = false;
var selected_item_row = null;

// CALCOLO CON API PER PREZZI GRUPPO CLIENTE
function calculate_item_pricing_safe(frm, cdt, cdn, force_recalc = false) {
    if (iderp_calculating) return;
    
    let row = locals[cdt][cdn];
    if (!row || !row.item_code || row.tipo_vendita !== "Metro Quadrato") {
        return;
    }
    
    // Non ricalcolare se è bloccato
    if (row.price_locked && !force_recalc) {
        return;
    }
    
    let base = parseFloat(row.base) || 0;
    let altezza = parseFloat(row.altezza) || 0;
    let qty = parseFloat(row.qty) || 1;
    
    if (!base || !altezza) {
        row.mq_singolo = 0;
        row.mq_calcolati = 0;
        row.note_calcolo = "Inserire base e altezza";
        frm.refresh_field("items");
        return;
    }
    
    // Calcola m² sempre
    let mq_singolo = (base * altezza) / 10000;
    let mq_totali = mq_singolo * qty;
    
    row.mq_singolo = parseFloat(mq_singolo.toFixed(4));
    row.mq_calcolati = parseFloat(mq_totali.toFixed(3));
    
    // Se non c'è cliente, calcolo base
    if (!frm.doc.customer) {
        row.note_calcolo = `📊 ${mq_totali.toFixed(3)} m² totali - Seleziona cliente per prezzi`;
        frm.refresh_field("items");
        return;
    }
    
    // FLAG IMPORTANTE: blocca altri eventi
    iderp_calculating = true;
    
    // Chiamata API SICURA per prezzo con customer group
    frappe.call({
        method: 'iderp.pricing_utils.calculate_item_pricing',
        args: {
            item_code: row.item_code,
            base: base,
            altezza: altezza,
            qty: qty,
            customer: frm.doc.customer
        },
        freeze: false, // Non bloccare UI
        async: true,   // Chiamata asincrona
        callback: function(r) {
            try {
                if (r.message && r.message.success && !r.message.error) {
                    // Aggiorna valori SOLO se la riga è ancora la stessa
                    let current_row = locals[cdt][cdn];
                    if (current_row && current_row.name === row.name && current_row.item_code === row.item_code) {
                        
                        current_row.rate = r.message.rate;
                        current_row.prezzo_mq = r.message.tier_info.price_per_sqm;
                        current_row.note_calcolo = r.message.note_calcolo + "\n\n🤖 CALCOLO AUTOMATICO (con minimi gruppo)";
                        current_row.auto_calculated = 1;
                        current_row.manual_rate_override = 0;
                        current_row.price_locked = 0;
                        
                        // Aggiorna amount
                        current_row.amount = parseFloat((current_row.rate * qty).toFixed(2));
                        
                        frm.refresh_field("items");
                        update_toolbar_status(frm);
                        
                        frappe.show_alert({
                            message: `✅ Prezzo calcolato: €${current_row.rate} (${r.message.tier_info.tier_name || 'scaglione'})`,
                            indicator: 'green'
                        });
                        
                        // Ricalcola totali documento DOPO un delay
                        setTimeout(() => {
                            if (frm && frm.script_manager) {
                                frm.script_manager.trigger("calculate_taxes_and_totals");
                            }
                        }, 300);
                    }
                } else {
                    // Errore API - fallback a calcolo base
                    console.log("API Error:", r.message?.error || "Unknown error");
                    
                    row.note_calcolo = `📊 ${mq_totali.toFixed(3)} m² totali - Errore calcolo prezzo: ${r.message?.error || "API non disponibile"}`;
                    frm.refresh_field("items");
                }
            } catch (err) {
                console.error("Errore callback API:", err);
                row.note_calcolo = `📊 ${mq_totali.toFixed(3)} m² totali - Errore interno`;
                frm.refresh_field("items");
            } finally {
                // SEMPRE sblocca il flag
                setTimeout(() => {
                    iderp_calculating = false;
                }, 500);
            }
        },
        error: function(err) {
            console.error("Errore API call:", err);
            row.note_calcolo = `📊 ${mq_totali.toFixed(3)} m² totali - Errore connessione API`;
            frm.refresh_field("items");
            
            // Sblocca flag anche in caso di errore
            setTimeout(() => {
                iderp_calculating = false;
            }, 500);
        }
    });
}

// AGGIORNA STATUS TOOLBAR
function update_toolbar_status(frm) {
    if (!selected_item_row) {
        frm.page.set_indicator("🎛️ Seleziona una riga per controlli", "blue");
        return;
    }
    
    let row = selected_item_row;
    let status = "";
    let color = "";
    
    if (row.price_locked) {
        status = "🔒 PREZZO BLOCCATO";
        color = "red";
    } else if (row.manual_rate_override) {
        status = "🖊️ PREZZO MANUALE";
        color = "orange";
    } else if (row.auto_calculated) {
        status = "🤖 CALCOLO AUTOMATICO";
        color = "green";
    } else {
        status = "⚪ NON CALCOLATO";
        color = "gray";
    }
    
    frm.page.set_indicator(`${status} | Item: ${row.item_code || 'nessuno'}`, color);
}

// PULSANTI TOOLBAR
function add_toolbar_buttons(frm) {
    // Rimuovi pulsanti esistenti
    frm.page.remove_inner_button("🔄 Ricalcola");
    frm.page.remove_inner_button("🔒 Blocca");
    frm.page.remove_inner_button("🔓 Sblocca");
    
    // Pulsante Ricalcola
    frm.page.add_inner_button("🔄 Ricalcola", function() {
        if (!selected_item_row) {
            frappe.msgprint("Seleziona prima una riga nella tabella items!");
            return;
        }
        
        if (selected_item_row.tipo_vendita !== "Metro Quadrato") {
            frappe.msgprint("Funzione disponibile solo per vendita al metro quadrato!");
            return;
        }
        
        if (!frm.doc.customer) {
            frappe.msgprint("Seleziona prima un cliente per calcolare i prezzi corretti!");
            return;
        }
        
        // Reset flag e forza ricalcolo
        selected_item_row.manual_rate_override = 0;
        selected_item_row.price_locked = 0;
        selected_item_row.auto_calculated = 0;
        
        calculate_item_pricing_safe(frm, selected_item_row.doctype, selected_item_row.name, true);
    });
    
    // Pulsante Blocca
    frm.page.add_inner_button("🔒 Blocca", function() {
        if (!selected_item_row) {
            frappe.msgprint("Seleziona prima una riga nella tabella items!");
            return;
        }
        
        selected_item_row.price_locked = 1;
        selected_item_row.manual_rate_override = 1;
        selected_item_row.auto_calculated = 0;
        
        // SAFE split - controlla se note_calcolo esiste
        let base_note = "";
        if (selected_item_row.note_calcolo) {
            base_note = selected_item_row.note_calcolo.split('\n🤖')[0];
        }
        selected_item_row.note_calcolo = base_note + "\n🔒 PREZZO BLOCCATO - Non verrà ricalcolato";
        
        frm.refresh_field("items");
        update_toolbar_status(frm);
        
        frappe.show_alert({
            message: `🔒 Prezzo bloccato: €${selected_item_row.rate}`,
            indicator: 'orange'
        });
    });
    
    // Pulsante Sblocca
    frm.page.add_inner_button("🔓 Sblocca", function() {
        if (!selected_item_row) {
            frappe.msgprint("Seleziona prima una riga nella tabella items!");
            return;
        }
        
        selected_item_row.price_locked = 0;
        selected_item_row.manual_rate_override = 0;
        
        // SAFE split - controlla se note_calcolo esiste
        let base_note = "";
        if (selected_item_row.note_calcolo) {
            base_note = selected_item_row.note_calcolo.split('\n🔒')[0];
        }
        selected_item_row.note_calcolo = base_note + "\n🔓 PREZZO SBLOCCATO";
        
        frm.refresh_field("items");
        update_toolbar_status(frm);
        
        frappe.show_alert({
            message: `🔓 Prezzo sbloccato per ${selected_item_row.item_code}`,
            indicator: 'green'
        });
    });
}

// EVENTI QUOTATION ITEM
frappe.ui.form.on('Quotation Item', {
    // Calcolo m² in tempo reale + auto-calcolo prezzo
    base: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.base && row.altezza) {
            let mq_singolo = (parseFloat(row.base) * parseFloat(row.altezza)) / 10000;
            let mq_totali = mq_singolo * (parseFloat(row.qty) || 1);
            row.mq_singolo = parseFloat(mq_singolo.toFixed(4));
            row.mq_calcolati = parseFloat(mq_totali.toFixed(3));
            frm.refresh_field("items");
            
            // Auto-calcolo se non bloccato
            if (!row.price_locked && frm.doc.customer) {
                setTimeout(() => {
                    calculate_item_pricing_safe(frm, cdt, cdn);
                }, 300);
            }
        }
    },
    
    altezza: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.base && row.altezza) {
            let mq_singolo = (parseFloat(row.base) * parseFloat(row.altezza)) / 10000;
            let mq_totali = mq_singolo * (parseFloat(row.qty) || 1);
            row.mq_singolo = parseFloat(mq_singolo.toFixed(4));
            row.mq_calcolati = parseFloat(mq_totali.toFixed(3));
            frm.refresh_field("items");
            
            // Auto-calcolo se non bloccato
            if (!row.price_locked && frm.doc.customer) {
                setTimeout(() => {
                    calculate_item_pricing_safe(frm, cdt, cdn);
                }, 300);
            }
        }
    },
    
    // Selezione item
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code && row.tipo_vendita === "Metro Quadrato" && 
            row.base && row.altezza && frm.doc.customer && !row.price_locked) {
            setTimeout(() => {
                calculate_item_pricing_safe(frm, cdt, cdn);
            }, 500);
        }
    },
    
    // Rate manuale - FIX per errore split
    rate: function(frm, cdt, cdn) {
        if (iderp_calculating) return;
        
        let row = locals[cdt][cdn];
        row.manual_rate_override = 1;
        row.auto_calculated = 0;
        row.price_locked = 0;
        
        // Solo ricalcola amount
        let qty = parseFloat(row.qty) || 1;
        let rate = parseFloat(row.rate) || 0;
        row.amount = parseFloat((rate * qty).toFixed(2));
        
        // SAFE split - FIX per errore undefined
        let base_note = "";
        if (row.note_calcolo && typeof row.note_calcolo === 'string') {
            base_note = row.note_calcolo.split('\n🤖')[0].split('\n🔒')[0];
        }
        row.note_calcolo = base_note + "\n🖊️ PREZZO MODIFICATO MANUALMENTE";
        
        selected_item_row = row;
        frm.refresh_field("items");
        update_toolbar_status(frm);
    }
});

// EVENTI QUOTATION
frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            add_toolbar_buttons(frm);
            update_toolbar_status(frm);
        }
    },
    
    // Ricalcola tutto quando cambia cliente
    customer: function(frm) {
        if (frm.doc.items && frm.doc.customer) {
            frm.doc.items.forEach(function(item) {
                if (item.tipo_vendita === "Metro Quadrato" && 
                    item.base && item.altezza && !item.price_locked) {
                    setTimeout(() => {
                        calculate_item_pricing_safe(frm, item.doctype, item.name, true);
                    }, 500);
                }
            });
        }
    }
});

// Event listener per selezione righe
$(document).on('click', '[data-fieldname="items"] .grid-row', function() {
    setTimeout(() => {
        let grid_row = $(this).closest('.grid-row');
        let docname = grid_row.attr('data-name');
        
        if (docname && cur_frm && cur_frm.doc.items) {
            let item = cur_frm.doc.items.find(i => i.name === docname);
            if (item) {
                selected_item_row = item;
                update_toolbar_status(cur_frm);
            }
        }
    }, 100);
});

console.log("✅ IDERP Calculator sicuro con API gruppi cliente");