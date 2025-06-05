// iderp - Sistema Calcolatore Universale ERPNext 15 Compatible
// Versione 2.0 - Supporta Metro Quadrato, Metro Lineare, Pezzo + Customer Groups
console.log("iderp v2.0: Loading Universal Calculator for ERPNext 15");

// Variabili globali per controllo stato
var iderp_calculating = false;
var selected_item_row = null;
var calculation_timeout = null;

// ================================
// CALCOLO UNIVERSALE PRINCIPALE
// ================================

function calculate_universal_pricing_v15(frm, cdt, cdn, force_recalc = false) {
    // Previeni loop infiniti
    if (iderp_calculating && !force_recalc) {
        return;
    }
    
    let row = locals[cdt][cdn];
    if (!row || !row.item_code) {
        return;
    }
    
    let tipo_vendita = row.tipo_vendita || "Pezzo";
    
    // Non ricalcolare se bloccato (a meno che non sia forzato)
    if (row.price_locked && !force_recalc) {
        console.log(`iderp: Riga ${row.idx} bloccata, skip calcolo`);
        return;
    }
    
    // Calcola quantità base per il tipo selezionato
    let qty_info = calculate_base_quantities_v15(row, tipo_vendita);
    if (!qty_info || qty_info.total_qty <= 0) {
        // Aggiorna comunque i campi calcolati
        if (qty_info) {
            Object.assign(row, qty_info.fields);
            frm.refresh_field("items");
        }
        return;
    }
    
    // Aggiorna campi calcolati
    Object.assign(row, qty_info.fields);
    
    // Se non c'è cliente, mostra solo quantità
    if (!frm.doc.customer) {
        row.note_calcolo = `📊 ${qty_info.display_text}\n💡 Seleziona cliente per calcolo prezzi automatico`;
        frm.refresh_field("items");
        return;
    }
    
    // Debounce per evitare chiamate multiple
    if (calculation_timeout) {
        clearTimeout(calculation_timeout);
    }
    
    calculation_timeout = setTimeout(() => {
        call_pricing_api_v15(frm, row, tipo_vendita, qty_info);
    }, 300);
}

function calculate_base_quantities_v15(row, tipo_vendita) {
    try {
        let qty = parseFloat(row.qty) || 1;
        
        if (tipo_vendita === "Metro Quadrato") {
            let base = parseFloat(row.base) || 0;
            let altezza = parseFloat(row.altezza) || 0;
            
            if (!base || !altezza) {
                return {
                    total_qty: 0,
                    display_text: "Inserire base e altezza in cm",
                    fields: {
                        mq_singolo: 0,
                        mq_calcolati: 0
                    }
                };
            }
            
            let mq_singolo = (base * altezza) / 10000;
            let mq_totali = mq_singolo * qty;
            
            return {
                total_qty: mq_totali,
                display_text: `${base}×${altezza}cm × ${qty}pz = ${mq_totali.toFixed(3)} m²`,
                fields: {
                    mq_singolo: parseFloat(mq_singolo.toFixed(4)),
                    mq_calcolati: parseFloat(mq_totali.toFixed(3))
                }
            };
            
        } else if (tipo_vendita === "Metro Lineare") {
            let lunghezza = parseFloat(row.lunghezza) || 0;
            let larghezza_materiale = parseFloat(row.larghezza_materiale) || 0;
            
            if (!lunghezza) {
                return {
                    total_qty: 0,
                    display_text: "Inserire lunghezza in cm",
                    fields: {
                        ml_calcolati: 0
                    }
                };
            }
            
            let ml_singolo = lunghezza / 100; // da cm a metri
            let ml_totali = ml_singolo * qty;
            
            let display_larghezza = larghezza_materiale ? ` (largh: ${larghezza_materiale}cm)` : "";
            
            return {
                total_qty: ml_totali,
                display_text: `${lunghezza}cm × ${qty}pz = ${ml_totali.toFixed(2)} ml${display_larghezza}`,
                fields: {
                    ml_calcolati: parseFloat(ml_totali.toFixed(2))
                }
            };
            
        } else if (tipo_vendita === "Pezzo") {
            return {
                total_qty: qty,
                display_text: `${qty} pezzi`,
                fields: {
                    pz_totali: qty
                }
            };
        }
        
        return null;
        
    } catch (e) {
        console.error("iderp: Errore calcolo quantità", e);
        return null;
    }
}

function call_pricing_api_v15(frm, row, tipo_vendita, qty_info) {
    iderp_calculating = true;
    
    // Mostra indicator di calcolo
    frm.page.set_indicator("🔄 Calcolando prezzi...", "blue");
    
    let api_args = {
        item_code: row.item_code,
        tipo_vendita: tipo_vendita,
        qty: row.qty || 1,
        customer: frm.doc.customer
    };
    
    // Aggiungi parametri specifici per tipo
    if (tipo_vendita === "Metro Quadrato") {
        api_args.base = row.base || 0;
        api_args.altezza = row.altezza || 0;
    } else if (tipo_vendita === "Metro Lineare") {
        api_args.lunghezza = row.lunghezza || 0;
    }
    
    frappe.call({
        method: 'iderp.pricing_utils.calculate_universal_item_pricing_with_fallback',
        args: api_args,
        freeze: false,
        callback: function(r) {
            try {
                if (r.message && r.message.success && !r.message.error) {
                    // Verifica che la riga sia ancora valida
                    let current_row = locals[row.doctype][row.name];
                    if (current_row && current_row.item_code === row.item_code) {
                        
                        // Aggiorna prezzi
                        current_row.rate = r.message.rate;
                        current_row.amount = parseFloat((current_row.rate * (current_row.qty || 1)).toFixed(2));
                        
                        // Aggiorna prezzo specifico per tipo
                        if (tipo_vendita === "Metro Quadrato") {
                            current_row.prezzo_mq = r.message.price_per_unit;
                        } else if (tipo_vendita === "Metro Lineare") {
                            current_row.prezzo_ml = r.message.price_per_unit;
                        }
                        
                        // Note dettagliate
                        current_row.note_calcolo = r.message.note_calcolo + "\n\n🤖 CALCOLATO AUTOMATICAMENTE";
                        
                        // Flag di stato
                        current_row.auto_calculated = 1;
                        current_row.manual_rate_override = 0;
                        current_row.price_locked = 0;
                        
                        // Refresh
                        frm.refresh_field("items");
                        update_toolbar_status_v15(frm);
                        
                        // Alert successo
                        frappe.show_alert({
                            message: `✅ ${tipo_vendita}: €${current_row.rate} (${r.message.tier_info?.tier_name || 'Standard'})`,
                            indicator: 'green'
                        });
                        
                        // Ricalcola totali
                        setTimeout(() => {
                            frm.script_manager.trigger("calculate_taxes_and_totals");
                        }, 100);
                    }
                } else {
                    // Errore API
                    row.note_calcolo = `📊 ${qty_info.display_text}\n❌ Errore: ${r.message?.error || "API non disponibile"}`;
                    frm.refresh_field("items");
                    
                    frappe.show_alert({
                        message: `❌ Errore calcolo: ${r.message?.error || "Sconosciuto"}`,
                        indicator: 'red'
                    });
                }
            } catch (err) {
                console.error("iderp: Errore callback", err);
                row.note_calcolo = `📊 ${qty_info.display_text}\n💥 Errore interno calcolo`;
                frm.refresh_field("items");
            } finally {
                iderp_calculating = false;
                frm.page.set_indicator("", "");
            }
        },
        error: function(err) {
            console.error("iderp: Errore API", err);
            row.note_calcolo = `📊 ${qty_info.display_text}\n🔌 Errore connessione API`;
            frm.refresh_field("items");
            iderp_calculating = false;
            frm.page.set_indicator("", "");
            
            frappe.show_alert({
                message: "❌ Errore connessione server",
                indicator: 'red'
            });
        }
    });
}

// ================================
// TOOLBAR E CONTROLLI
// ================================

function update_toolbar_status_v15(frm) {
    if (!selected_item_row) {
        frm.page.set_indicator("🎛️ iderp: Seleziona riga per controlli", "blue");
        return;
    }
    
    let row = selected_item_row;
    let tipo_vendita = row.tipo_vendita || "Pezzo";
    let status = "";
    let color = "";
    
    if (row.price_locked) {
        status = "🔒 BLOCCATO";
        color = "red";
    } else if (row.manual_rate_override) {
        status = "🖊️ MANUALE";
        color = "orange";
    } else if (row.auto_calculated) {
        status = "🤖 AUTOMATICO";
        color = "green";
    } else {
        status = "⚪ DA CALCOLARE";
        color = "gray";
    }
    
    frm.page.set_indicator(`${status} | ${tipo_vendita} | ${row.item_code || 'n/a'}`, color);
}

function add_toolbar_buttons_v15(frm) {
    // Rimuovi pulsanti esistenti
    frm.page.remove_inner_button("🔄 Ricalcola Tutto");
    frm.page.remove_inner_button("🔒 Blocca Riga");
    frm.page.remove_inner_button("🔓 Sblocca Riga");
    frm.page.remove_inner_button("🧮 Calcola Riga");
    
    // Pulsante Calcola Riga Selezionata
    frm.page.add_inner_button("🧮 Calcola Riga", function() {
        if (!selected_item_row) {
            frappe.msgprint("Seleziona prima una riga cliccando su di essa!");
            return;
        }
        
        if (!frm.doc.customer) {
            frappe.msgprint("Seleziona prima un cliente!");
            return;
        }
        
        // Reset flags e forza calcolo
        selected_item_row.manual_rate_override = 0;
        selected_item_row.price_locked = 0;
        selected_item_row.auto_calculated = 0;
        
        calculate_universal_pricing_v15(frm, selected_item_row.doctype, selected_item_row.name, true);
    });
    
    // Pulsante Ricalcola Tutto
    frm.page.add_inner_button("🔄 Ricalcola Tutto", function() {
        if (!frm.doc.customer) {
            frappe.msgprint("Seleziona prima un cliente!");
            return;
        }
        
        frappe.confirm(
            "Ricalcolare automaticamente tutte le righe? Questo sovrascriverà i prezzi attuali (eccetto quelli bloccati).",
            function() {
                let recalculated = 0;
                frm.doc.items.forEach(function(item) {
                    if (!item.price_locked && item.item_code && item.tipo_vendita) {
                        item.manual_rate_override = 0;
                        item.auto_calculated = 0;
                        
                        setTimeout(() => {
                            calculate_universal_pricing_v15(frm, item.doctype, item.name, true);
                        }, recalculated * 500); // Spazia i calcoli
                        
                        recalculated++;
                    }
                });
                
                frappe.show_alert({
                    message: `🔄 Ricalcolando ${recalculated} righe...`,
                    indicator: 'blue'
                });
            }
        );
    });
    
    // Pulsante Blocca
    frm.page.add_inner_button("🔒 Blocca Riga", function() {
        if (!selected_item_row) {
            frappe.msgprint("Seleziona prima una riga!");
            return;
        }
        
        selected_item_row.price_locked = 1;
        selected_item_row.manual_rate_override = 1;
        selected_item_row.auto_calculated = 0;
        
        // Aggiorna note preservando calcolo esistente
        let base_note = selected_item_row.note_calcolo ? 
            selected_item_row.note_calcolo.split('\n🤖')[0].split('\n🔒')[0] : '';
        selected_item_row.note_calcolo = base_note + "\n🔒 PREZZO BLOCCATO - Non verrà ricalcolato automaticamente";
        
        frm.refresh_field("items");
        update_toolbar_status_v15(frm);
        
        frappe.show_alert({
            message: `🔒 Riga bloccata: ${selected_item_row.item_code} - €${selected_item_row.rate}`,
            indicator: 'orange'
        });
    });
    
    // Pulsante Sblocca
    frm.page.add_inner_button("🔓 Sblocca Riga", function() {
        if (!selected_item_row) {
            frappe.msgprint("Seleziona prima una riga!");
            return;
        }
        
        selected_item_row.price_locked = 0;
        selected_item_row.manual_rate_override = 0;
        
        // Rimuovi note di blocco
        let base_note = selected_item_row.note_calcolo ? 
            selected_item_row.note_calcolo.split('\n🔒')[0].split('\n🤖')[0] : '';
        selected_item_row.note_calcolo = base_note + "\n🔓 SBLOCCATO - Calcolo automatico riattivato";
        
        frm.refresh_field("items");
        update_toolbar_status_v15(frm);
        
        frappe.show_alert({
            message: `🔓 Riga sbloccata: ${selected_item_row.item_code}`,
            indicator: 'green'
        });
    });
}

// ================================
// EVENTI FORM ITEMS
// ================================

// Eventi per Quotation Item
frappe.ui.form.on('Quotation Item', {
    // Cambio tipo vendita
    tipo_vendita: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        
        console.log(`iderp: Tipo vendita cambiato in: ${row.tipo_vendita}`);
        
        // Reset campi quando cambia tipo
        reset_measurement_fields(row);
        frm.refresh_field("items");
        
        // Aggiorna visibilità campi se possibile
        setTimeout(() => {
            frm.fields_dict.items.grid.refresh();
        }, 100);
    },
    
    // Eventi Metro Quadrato
    base: function(frm, cdt, cdn) {
        handle_measurement_change(frm, cdt, cdn, 'base');
    },
    
    altezza: function(frm, cdt, cdn) {
        handle_measurement_change(frm, cdt, cdn, 'altezza');
    },
    
    // Eventi Metro Lineare
    lunghezza: function(frm, cdt, cdn) {
        handle_measurement_change(frm, cdt, cdn, 'lunghezza');
    },
    
    larghezza_materiale: function(frm, cdt, cdn) {
        handle_measurement_change(frm, cdt, cdn, 'larghezza_materiale');
    },
    
    // Quantità (tutti i tipi)
    qty: function(frm, cdt, cdn) {
        handle_measurement_change(frm, cdt, cdn, 'qty');
    },
    
    // Item code
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code && frm.doc.customer) {
            // Carica configurazione item se disponibile
            setTimeout(() => {
                if (row.tipo_vendita) {
                    calculate_universal_pricing_v15(frm, cdt, cdn);
                }
            }, 1000);
        }
    },
    
    // Rate modificato manualmente
    rate: function(frm, cdt, cdn) {
        if (iderp_calculating) {
            return; // Evita loop quando aggiorniamo il rate via API
        }
        
        let row = locals[cdt][cdn];
        if (row) {
            // Marca come modificato manualmente
            row.manual_rate_override = 1;
            row.auto_calculated = 0;
            row.price_locked = 0;
            
            // Aggiorna amount
            let qty = parseFloat(row.qty) || 1;
            let rate = parseFloat(row.rate) || 0;
            row.amount = parseFloat((rate * qty).toFixed(2));
            
            // Aggiorna note
            let base_note = row.note_calcolo ? 
                row.note_calcolo.split('\n🤖')[0].split('\n🔒')[0].split('\n🖊️')[0] : '';
            row.note_calcolo = base_note + "\n🖊️ PREZZO MODIFICATO MANUALMENTE";
            
            // Aggiorna stato
            selected_item_row = row;
            update_toolbar_status_v15(frm);
            frm.refresh_field("items");
        }
    }
});

// Eventi per altri DocTypes (Sales Order, etc.)
['Sales Order Item', 'Sales Invoice Item', 'Delivery Note Item'].forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        tipo_vendita: frappe.ui.form.get_event_handler('Quotation Item', 'tipo_vendita'),
        base: frappe.ui.form.get_event_handler('Quotation Item', 'base'),
        altezza: frappe.ui.form.get_event_handler('Quotation Item', 'altezza'),
        lunghezza: frappe.ui.form.get_event_handler('Quotation Item', 'lunghezza'),
        larghezza_materiale: frappe.ui.form.get_event_handler('Quotation Item', 'larghezza_materiale'),
        qty: frappe.ui.form.get_event_handler('Quotation Item', 'qty'),
        item_code: frappe.ui.form.get_event_handler('Quotation Item', 'item_code'),
        rate: frappe.ui.form.get_event_handler('Quotation Item', 'rate')
    });
});

// ================================
// EVENTI FORM PRINCIPALE
// ================================

// Eventi Quotation
frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            add_toolbar_buttons_v15(frm);
            update_toolbar_status_v15(frm);
            
            // Messaggio informativo se non c'è cliente
            if (!frm.doc.customer) {
                frm.page.set_indicator("💡 Seleziona cliente per calcoli automatici", "orange");
            }
        }
    },
    
    customer: function(frm) {
        if (frm.doc.items && frm.doc.customer) {
            frappe.show_alert({
                message: "🔄 Cliente selezionato - Ricalcolando prezzi...",
                indicator: 'blue'
            });
            
            // Ricalcola automaticamente tutte le righe non bloccate
            let delay = 0;
            frm.doc.items.forEach(function(item) {
                if (!item.price_locked && item.tipo_vendita && item.item_code) {
                    setTimeout(() => {
                        calculate_universal_pricing_v15(frm, item.doctype, item.name, true);
                    }, delay);
                    delay += 300;
                }
            });
        }
    }
});

// Eventi per altri DocTypes principali
['Sales Order', 'Sales Invoice', 'Delivery Note'].forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        refresh: frappe.ui.form.get_event_handler('Quotation', 'refresh'),
        customer: frappe.ui.form.get_event_handler('Quotation', 'customer')
    });
});

// ================================
// FUNZIONI UTILITY
// ================================

function reset_measurement_fields(row) {
    // Reset tutti i campi di misurazione
    row.base = 0;
    row.altezza = 0;
    row.lunghezza = 0;
    row.larghezza_materiale = 0;
    row.mq_singolo = 0;
    row.mq_calcolati = 0;
    row.ml_calcolati = 0;
    row.pz_totali = 0;
    row.prezzo_mq = 0;
    row.prezzo_ml = 0;
    row.rate = 0;
    row.amount = 0;
    row.note_calcolo = "";
    row.price_locked = 0;
    row.manual_rate_override = 0;
    row.auto_calculated = 0;
}

function handle_measurement_change(frm, cdt, cdn, changed_field) {
    let row = locals[cdt][cdn];
    
    if (!row || !row.tipo_vendita) {
        return;
    }
    
    // Log del cambiamento
    console.log(`iderp: Campo ${changed_field} cambiato, tipo: ${row.tipo_vendita}`);
    
    // Aggiorna campi calcolati sempre
    let qty_info = calculate_base_quantities_v15(row, row.tipo_vendita);
    if (qty_info) {
        Object.assign(row, qty_info.fields);
        frm.refresh_field("items");
    }
    
    // Calcola prezzo solo se non bloccato e se abbiamo cliente
    if (!row.price_locked && frm.doc.customer && qty_info && qty_info.total_qty > 0) {
        calculate_universal_pricing_v15(frm, cdt, cdn);
    }
}

// Event listener per selezione righe
$(document).on('click', '[data-fieldname="items"] .grid-row', function() {
    setTimeout(() => {
        let grid_row = $(this).closest('.grid-row');
        let docname = grid_row.attr('data-name');
        
        if (docname && cur_frm && cur_frm.doc.items) {
            let item = cur_frm.doc.items.find(i => i.name === docname);
            if (item) {
                selected_item_row = item;
                update_toolbar_status_v15(cur_frm);
                console.log(`iderp: Riga selezionata: ${item.item_code} (${item.tipo_vendita})`);
            }
        }
    }, 100);
});

// Inizializzazione
$(document).ready(function() {
    console.log("✅ iderp v2.0: Universal Calculator caricato per ERPNext 15");
    console.log("🎯 Supporto: Metro Quadrato, Metro Lineare, Pezzo + Customer Groups");
});
