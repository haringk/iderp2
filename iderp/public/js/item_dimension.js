console.log("IDERP: Calculator con controlli toolbar");

// Flag per prevenire loop infiniti
var iderp_calculating = false;
var selected_item_row = null;

// CALCOLO INTELLIGENTE
function calculate_item_pricing(frm, cdt, cdn, force_recalc = false) {
    if (iderp_calculating) return;
    
    let row = locals[cdt][cdn];
    if (!row || !row.item_code || row.tipo_vendita !== "Metro Quadrato") {
        return;
    }
    
    // Non ricalcolare se è bloccato (a meno che force_recalc)
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
    
    // Calcola m²
    let mq_singolo = (base * altezza) / 10000;
    let mq_totali = mq_singolo * qty;
    
    row.mq_singolo = parseFloat(mq_singolo.toFixed(4));
    row.mq_calcolati = parseFloat(mq_totali.toFixed(3));
    
    // Chiamata API per calcolo prezzo
    if (frm.doc.customer && row.item_code) {
        frappe.call({
            method: 'iderp.pricing_utils.calculate_item_pricing',
            args: {
                item_code: row.item_code,
                base: base,
                altezza: altezza,
                qty: qty,
                customer: frm.doc.customer
            },
            callback: function(r) {
                if (r.message && r.message.success) {
                    iderp_calculating = true;
                    
                    row.rate = r.message.rate;
                    row.prezzo_mq = r.message.tier_info.price_per_sqm;
                    row.auto_calculated = 1;
                    row.manual_rate_override = 0;
                    row.price_locked = 0;
                    
                    // Status nelle note
                    row.note_calcolo = r.message.note_calcolo + 
                        "\n\n🤖 CALCOLO AUTOMATICO - Usa toolbar per controlli";
                    
                    frm.refresh_field("items");
                    update_toolbar_status(frm);
                    
                    frappe.show_alert({
                        message: `✅ Prezzo calcolato: €${row.rate}`,
                        indicator: 'green'
                    });
                    
                    setTimeout(() => {
                        iderp_calculating = false;
                    }, 100);
                }
            }
        });
    }
}

// AGGIORNA STATUS TOOLBAR
function update_toolbar_status(frm) {
    if (!selected_item_row) return;
    
    let row = selected_item_row;
    let status = "";
    
    if (row.price_locked) {
        status = "🔒 PREZZO BLOCCATO";
    } else if (row.manual_rate_override) {
        status = "🖊️ PREZZO MANUALE";
    } else if (row.auto_calculated) {
        status = "🤖 CALCOLO AUTOMATICO";
    } else {
        status = "⚪ NON CALCOLATO";
    }
    
    // Aggiorna indicator
    frm.page.set_indicator(`${status} | Item: ${row.item_code || 'nessuno'}`, 
                          row.price_locked ? "red" : (row.auto_calculated ? "green" : "orange"));
}

// PULSANTI TOOLBAR
function add_toolbar_buttons(frm) {
    // Rimuovi pulsanti esistenti
    frm.page.remove_inner_button("🔄 Ricalcola Prezzo");
    frm.page.remove_inner_button("🔒 Blocca Prezzo");
    frm.page.remove_inner_button("🔓 Sblocca Prezzo");
    
    // Pulsante Ricalcola
    frm.page.add_inner_button("🔄 Ricalcola Prezzo", function() {
        if (!selected_item_row) {
            frappe.msgprint("Seleziona prima una riga nella tabella items!");
            return;
        }
        
        if (selected_item_row.tipo_vendita !== "Metro Quadrato") {
            frappe.msgprint("Funzione disponibile solo per vendita al metro quadrato!");
            return;
        }
        
        // Reset flag e forza ricalcolo
        selected_item_row.manual_rate_override = 0;
        selected_item_row.price_locked = 0;
        selected_item_row.auto_calculated = 0;
        
        calculate_item_pricing(frm, selected_item_row.doctype, selected_item_row.name, true);
    });
    
    // Pulsante Blocca
    frm.page.add_inner_button("🔒 Blocca Prezzo", function() {
        if (!selected_item_row) {
            frappe.msgprint("Seleziona prima una riga nella tabella items!");
            return;
        }
        
        selected_item_row.price_locked = 1;
        selected_item_row.manual_rate_override = 1;
        selected_item_row.auto_calculated = 0;
        
        // Aggiorna note
        let base_note = selected_item_row.note_calcolo.split('\n\n🤖')[0];
        selected_item_row.note_calcolo = base_note + 
            "\n\n🔒 PREZZO BLOCCATO - Non verrà ricalcolato automaticamente";
        
        frm.refresh_field("items");
        update_toolbar_status(frm);
        
        frappe.show_alert({
            message: `🔒 Prezzo bloccato: €${selected_item_row.rate}`,
            indicator: 'orange'
        });
    });
    
    // Pulsante Sblocca
    frm.page.add_inner_button("🔓 Sblocca Prezzo", function() {
        if (!selected_item_row) {
            frappe.msgprint("Seleziona prima una riga nella tabella items!");
            return;
        }
        
        selected_item_row.price_locked = 0;
        selected_item_row.manual_rate_override = 0;
        
        // Aggiorna note
        let base_note = selected_item_row.note_calcolo.split('\n\n🔒')[0];
        selected_item_row.note_calcolo = base_note + 
            "\n\n🔓 PREZZO SBLOCCATO - Sarà ricalcolato alle prossime modifiche";
        
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
        }
    },
    
    // Selezione riga
    form_render: function(frm, cdt, cdn) {
        selected_item_row = locals[cdt][cdn];
        update_toolbar_status(frm);
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
        let base_note = row.note_calcolo.split('\n\n🤖')[0];
        row.note_calcolo = base_note + "\n\n🖊️ PREZZO MODIFICATO MANUALMENTE";
        
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
    
    // Tracking selezione riga
    items_on_form_rendered: function(frm) {
        update_toolbar_status(frm);
    }
});

// Event listener per click su righe
$(document).on('click', '[data-fieldname="items"] .grid-row', function() {
    let grid_row = $(this).closest('.grid-row');
    let docname = grid_row.attr('data-name');
    
    if (docname && cur_frm && cur_frm.doc.items) {
        let item = cur_frm.doc.items.find(i => i.name === docname);
        if (item) {
            selected_item_row = item;
            update_toolbar_status(cur_frm);
        }
    }
});

console.log("✅ IDERP Calculator con controlli toolbar attivo");