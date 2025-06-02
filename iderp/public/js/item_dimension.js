console.log("IDERP: Calculator con controlli manuali");

// Flag per prevenire loop infiniti
var iderp_calculating = false;

// CALCOLO INTELLIGENTE (SOLO su richiesta)
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
                    row.note_calcolo = r.message.note_calcolo;
                    row.auto_calculated = 1;
                    row.manual_rate_override = 0; // Reset flag manuale
                    row.price_locked = 0; // Reset lock
                    
                    // Aggiungi controlli in note
                    row.note_calcolo += "\n\n🎛️ CONTROLLI: Usa pulsanti per ricalcolare o bloccare prezzo";
                    
                    frm.refresh_field("items");
                    add_control_buttons(frm, cdt, cdn);
                    
                    setTimeout(() => {
                        iderp_calculating = false;
                    }, 100);
                }
            }
        });
    }
}

// AGGIUNGE PULSANTI DI CONTROLLO
function add_control_buttons(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let field_wrapper = frm.fields_dict.items.grid.grid_rows_by_docname[cdn];
    
    if (!field_wrapper) return;
    
    // Trova la cella delle note
    let note_field = field_wrapper.columns.note_calcolo;
    if (!note_field) return;
    
    // Rimuovi pulsanti esistenti
    $(note_field).find('.iderp-controls').remove();
    
    // Stato attuale
    let status_text = "";
    let status_color = "";
    
    if (row.price_locked) {
        status_text = "🔒 PREZZO BLOCCATO";
        status_color = "red";
    } else if (row.manual_rate_override) {
        status_text = "🖊️ PREZZO MANUALE";
        status_color = "orange";
    } else if (row.auto_calculated) {
        status_text = "🤖 CALCOLO AUTOMATICO";
        status_color = "green";
    } else {
        status_text = "⚪ NON CALCOLATO";
        status_color = "gray";
    }
    
    // HTML pulsanti
    let controls_html = `
        <div class="iderp-controls" style="margin-top: 10px; padding: 8px; background: #f8f9fa; border-radius: 4px;">
            <div style="margin-bottom: 5px; font-weight: bold; color: ${status_color};">
                ${status_text}
            </div>
            <button type="button" class="btn btn-xs btn-primary recalc-btn" 
                    style="margin-right: 5px;" 
                    onclick="force_recalculate('${cdn}')">
                🔄 Ricalcola
            </button>
            <button type="button" class="btn btn-xs btn-warning lock-btn" 
                    onclick="lock_price('${cdn}')">
                🔒 Blocca Prezzo
            </button>
            <button type="button" class="btn btn-xs btn-success unlock-btn" 
                    onclick="unlock_price('${cdn}')" 
                    style="margin-left: 5px;">
                🔓 Sblocca
            </button>
        </div>
    `;
    
    // Aggiungi dopo il campo note
    $(note_field).find('.form-control').after(controls_html);
}

// FUNZIONI PULSANTI (globali per onclick)
window.force_recalculate = function(cdn) {
    let frm = cur_frm;
    let row = locals[frm.doc.items[0].doctype][cdn];
    
    // Reset tutti i flag e forza ricalcolo
    row.manual_rate_override = 0;
    row.price_locked = 0;
    row.auto_calculated = 0;
    
    calculate_item_pricing(frm, row.doctype, cdn, true);
    
    frappe.show_alert({
        message: `🔄 Prezzo ricalcolato per ${row.item_code}`,
        indicator: 'blue'
    });
};

window.lock_price = function(cdn) {
    let frm = cur_frm;
    let row = locals[frm.doc.items[0].doctype][cdn];
    
    row.price_locked = 1;
    row.manual_rate_override = 1;
    row.auto_calculated = 0;
    
    // Aggiorna note
    let base_note = row.note_calcolo.split('\n\n🎛️')[0]; // Rimuovi controlli
    row.note_calcolo = base_note + "\n\n🔒 PREZZO BLOCCATO - Non verrà ricalcolato automaticamente";
    
    frm.refresh_field("items");
    add_control_buttons(frm, row.doctype, cdn);
    
    frappe.show_alert({
        message: `🔒 Prezzo bloccato per ${row.item_code} (€${row.rate})`,
        indicator: 'orange'
    });
};

window.unlock_price = function(cdn) {
    let frm = cur_frm;
    let row = locals[frm.doc.items[0].doctype][cdn];
    
    row.price_locked = 0;
    row.manual_rate_override = 0;
    
    // Aggiorna note
    let base_note = row.note_calcolo.split('\n\n🔒')[0]; // Rimuovi messaggio lock
    row.note_calcolo = base_note + "\n\n🔓 PREZZO SBLOCCATO - Sarà ricalcolato alle prossime modifiche";
    
    frm.refresh_field("items");
    add_control_buttons(frm, row.doctype, cdn);
    
    frappe.show_alert({
        message: `🔓 Prezzo sbloccato per ${row.item_code}`,
        indicator: 'green'
    });
};

// EVENTI QUOTATION ITEM
frappe.ui.form.on('Quotation Item', {
    // SOLO calcolo m² in tempo reale (non prezzo)
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
    
    // Aggiunge pulsanti quando si seleziona item
    item_code: function(frm, cdt, cdn) {
        setTimeout(() => {
            add_control_buttons(frm, cdt, cdn);
        }, 500);
    },
    
    // Rate manuale
    rate: function(frm, cdt, cdn) {
        if (iderp_calculating) return;
        
        let row = locals[cdt][cdn];
        row.manual_rate_override = 1;
        row.auto_calculated = 0;
        
        // Solo ricalcola amount
        let qty = parseFloat(row.qty) || 1;
        let rate = parseFloat(row.rate) || 0;
        row.amount = parseFloat((rate * qty).toFixed(2));
        
        frm.refresh_field("items");
        add_control_buttons(frm, cdt, cdn);
    }
});

// Evento refresh per aggiungere pulsanti
frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        // Aggiungi pulsanti a tutte le righe esistenti
        if (frm.doc.items) {
            frm.doc.items.forEach(function(item, idx) {
                setTimeout(() => {
                    add_control_buttons(frm, item.doctype, item.name);
                }, 100 * idx);
            });
        }
        
        frm.page.set_indicator("🎛️ Controllo prezzi manuale", "blue");
    }
});

console.log("✅ IDERP Calculator con controlli manuali attivo");