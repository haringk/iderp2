console.log("IDERP: Calculator semplificato - no API conflicts");

// Flag per prevenire loop infiniti
var iderp_calculating = false;
var selected_item_row = null;

// CALCOLO DIRETTO (senza API per evitare conflitti)
function calculate_item_pricing_direct(frm, cdt, cdn, force_recalc = false) {
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
    
    iderp_calculating = true;
    
    // Calcola m²
    let mq_singolo = (base * altezza) / 10000;
    let mq_totali = mq_singolo * qty;
    
    row.mq_singolo = parseFloat(mq_singolo.toFixed(4));
    row.mq_calcolati = parseFloat(mq_totali.toFixed(3));
    
    // Calcolo prezzo semplificato (usa prezzo_mq se disponibile)
    if (row.prezzo_mq && row.prezzo_mq > 0) {
        let calculated_rate = mq_singolo * row.prezzo_mq;
        row.rate = parseFloat(calculated_rate.toFixed(2));
        row.amount = parseFloat((row.rate * qty).toFixed(2));
        
        row.note_calcolo = 
            `📐 Dimensioni: ${base}×${altezza}cm\n` +
            `🔢 m² singolo: ${mq_singolo.toFixed(4)} m²\n` +
            `💰 Prezzo: €${row.prezzo_mq}/m²\n` +
            `💵 Prezzo unitario: €${row.rate}\n` +
            `📦 Quantità: ${qty} pz\n` +
            `📊 m² totali: ${mq_totali.toFixed(3)} m²\n` +
            `💸 Totale riga: €${row.amount}\n` +
            `🤖 CALCOLO AUTOMATICO`;
        
        row.auto_calculated = 1;
        row.manual_rate_override = 0;
        row.price_locked = 0;
        
        frappe.show_alert({
            message: `✅ Prezzo calcolato: €${row.rate}`,
            indicator: 'green'
        });
    } else {
        row.note_calcolo = `📊 ${mq_totali.toFixed(3)} m² totali - Inserire prezzo al m²`;
        row.rate = 0;
        row.amount = 0;
    }
    
    frm.refresh_field("items");
    update_toolbar_status(frm);
    
    // Ricalcola totali senza triggerare eventi
    setTimeout(() => {
        frm.script_manager.trigger("calculate_taxes_and_totals");
        iderp_calculating = false;
    }, 100);
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
    frm.page.remove_inner_button("💰 Prezzo m²");
    
    // Pulsante per impostare prezzo al m²
    frm.page.add_inner_button("💰 Prezzo m²", function() {
        if (!selected_item_row) {
            frappe.msgprint("Seleziona prima una riga nella tabella items!");
            return;
        }
        
        frappe.prompt([
            {
                'fieldname': 'prezzo_mq',
                'label': 'Prezzo al m²',
                'fieldtype': 'Currency',
                'default': selected_item_row.prezzo_mq || 0,
                'reqd': 1
            }
        ], function(values) {
            selected_item_row.prezzo_mq = values.prezzo_mq;
            frm.refresh_field("items");
            
            // Ricalcola automaticamente se non bloccato
            if (!selected_item_row.price_locked) {
                calculate_item_pricing_direct(frm, selected_item_row.doctype, selected_item_row.name, true);
            }
        }, 'Imposta Prezzo al m²', 'Salva');
    });
    
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
        
        if (!selected_item_row.prezzo_mq || selected_item_row.prezzo_mq <= 0) {
            frappe.msgprint("Imposta prima il prezzo al m² usando il pulsante '💰 Prezzo m²'!");
            return;
        }
        
        // Reset flag e forza ricalcolo
        selected_item_row.manual_rate_override = 0;
        selected_item_row.price_locked = 0;
        selected_item_row.auto_calculated = 0;
        
        calculate_item_pricing_direct(frm, selected_item_row.doctype, selected_item_row.name, true);
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
        
        // Aggiorna note
        let base_note = selected_item_row.note_calcolo.split('\n🤖')[0];
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
        
        // Aggiorna note
        let base_note = selected_item_row.note_calcolo.split('\n🔒')[0];
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
    // Calcolo m² in tempo reale
    base: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.base && row.altezza) {
            let mq_singolo = (parseFloat(row.base) * parseFloat(row.altezza)) / 10000;
            let mq_totali = mq_singolo * (parseFloat(row.qty) || 1);
            row.mq_singolo = parseFloat(mq_singolo.toFixed(4));
            row.mq_calcolati = parseFloat(mq_totali.toFixed(3));
            frm.refresh_field("items");
            
            // Auto-calcolo se non bloccato e ha prezzo
            if (!row.price_locked && row.prezzo_mq && row.prezzo_mq > 0) {
                setTimeout(() => {
                    calculate_item_pricing_direct(frm, cdt, cdn);
                }, 200);
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
            
            // Auto-calcolo se non bloccato e ha prezzo
            if (!row.price_locked && row.prezzo_mq && row.prezzo_mq > 0) {
                setTimeout(() => {
                    calculate_item_pricing_direct(frm, cdt, cdn);
                }, 200);
            }
        }
    },
    
    // Rate manuale
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
        
        // Aggiorna note
        let base_note = row.note_calcolo.split('\n🤖')[0] || row.note_calcolo.split('\n🔒')[0] || row.note_calcolo;
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

console.log("✅ IDERP Calculator semplificato - no API conflicts");