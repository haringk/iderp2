// IDERP - ERPNext 15 Compatible JavaScript
console.log("IDERP: Loading ERPNext 15 compatible calculator");

frappe.ui.form.on('Quotation Item', {
    tipo_vendita: function(frm, cdt, cdn) {
        console.log('IDERP: Tipo vendita changed');
        
        let row = frappe.get_doc(cdt, cdn);
        
        // Reset campi quando cambia tipo
        if (row.tipo_vendita !== 'Metro Quadrato') {
            frappe.model.set_value(cdt, cdn, 'base', 0);
            frappe.model.set_value(cdt, cdn, 'altezza', 0);
            frappe.model.set_value(cdt, cdn, 'mq_singolo', 0);
            frappe.model.set_value(cdt, cdn, 'mq_calcolati', 0);
        }
        
        frm.refresh_field("items");
    },
    
    base: function(frm, cdt, cdn) {
        calculate_square_meters(frm, cdt, cdn);
    },
    
    altezza: function(frm, cdt, cdn) {
        calculate_square_meters(frm, cdt, cdn);
    },
    
    qty: function(frm, cdt, cdn) {
        calculate_square_meters(frm, cdt, cdn);
    }
});

function calculate_square_meters(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    
    if (row.tipo_vendita === 'Metro Quadrato' && row.base && row.altezza) {
        let base = parseFloat(row.base) || 0;
        let altezza = parseFloat(row.altezza) || 0;
        let qty = parseFloat(row.qty) || 1;
        
        // Calcola m² singolo (da cm a m²)
        let mq_singolo = (base * altezza) / 10000;
        
        // Calcola m² totali
        let mq_totali = mq_singolo * qty;
        
        // Aggiorna campi
        frappe.model.set_value(cdt, cdn, 'mq_singolo', mq_singolo.toFixed(4));
        frappe.model.set_value(cdt, cdn, 'mq_calcolati', mq_totali.toFixed(3));
        
        console.log(`IDERP: ${base}×${altezza}cm = ${mq_singolo.toFixed(4)} m² × ${qty} = ${mq_totali.toFixed(3)} m²`);
        
        // Refresh tabella
        frm.refresh_field("items");
    }
}

// Hook per altri DocTypes
frappe.ui.form.on('Sales Order Item', {
    tipo_vendita: frappe.ui.form.get_event_handler('Quotation Item', 'tipo_vendita'),
    base: frappe.ui.form.get_event_handler('Quotation Item', 'base'),
    altezza: frappe.ui.form.get_event_handler('Quotation Item', 'altezza'),
    qty: frappe.ui.form.get_event_handler('Quotation Item', 'qty')
});

console.log("✅ IDERP: ERPNext 15 calculator loaded");



// console.log("IDERP: Universal Calculator per tutti i tipi di vendita");
// 
// // Flag per prevenire loop infiniti
// var iderp_calculating = false;
// var selected_item_row = null;
// 
// // CALCOLO UNIVERSALE
// function calculate_universal_pricing(frm, cdt, cdn, force_recalc = false) {
//     if (iderp_calculating) return;
//     
//     let row = locals[cdt][cdn];
//     if (!row || !row.item_code) {
//         return;
//     }
//     
//     let tipo_vendita = row.tipo_vendita || "Pezzo";
//     
//     // Non ricalcolare se è bloccato
//     if (row.price_locked && !force_recalc) {
//         return;
//     }
//     
//     // Calcola quantità base per tipo
//     let qty_info = calculate_base_quantities_js(row, tipo_vendita);
//     if (!qty_info) {
//         return;
//     }
//     
//     // Aggiorna campi calcolati
//     Object.assign(row, qty_info);
//     
//     // Se non c'è cliente, mostra solo quantità
//     if (!frm.doc.customer) {
//         row.note_calcolo = `📊 ${qty_info.display_qty} - Seleziona cliente per prezzi`;
//         frm.refresh_field("items");
//         return;
//     }
//     
//     // FLAG: blocca altri eventi
//     iderp_calculating = true;
//     
//     // Chiamata API universale
//     frappe.call({
// 	    method: 'iderp.pricing_utils.calculate_universal_item_pricing_with_fallback',
//         args: {
//             item_code: row.item_code,
//             tipo_vendita: tipo_vendita,
//             base: row.base || 0,
//             altezza: row.altezza || 0,
//             lunghezza: row.lunghezza || 0,
//             qty: row.qty || 1,
//             customer: frm.doc.customer
//         },
//         freeze: false,
//         async: true,
//         callback: function(r) {
//             try {
//                 if (r.message && r.message.success && !r.message.error) {
//                     // Verifica che la riga sia ancora la stessa
//                     let current_row = locals[cdt][cdn];
//                     if (current_row && current_row.name === row.name && current_row.item_code === row.item_code) {
//                         
//                         current_row.rate = r.message.rate;
//                         current_row.note_calcolo = r.message.note_calcolo + "\n\n🤖 CALCOLO AUTOMATICO UNIVERSALE";
//                         current_row.auto_calculated = 1;
//                         current_row.manual_rate_override = 0;
//                         current_row.price_locked = 0;
//                         
//                         // Aggiorna prezzo specifico per tipo
//                         if (tipo_vendita === "Metro Quadrato") {
//                             current_row.prezzo_mq = r.message.price_per_unit;
//                         } else if (tipo_vendita === "Metro Lineare") {
//                             current_row.prezzo_ml = r.message.price_per_unit;
//                         }
//                         
//                         // Aggiorna amount
//                         current_row.amount = parseFloat((current_row.rate * (current_row.qty || 1)).toFixed(2));
//                         
//                         frm.refresh_field("items");
//                         update_toolbar_status(frm);
//                         
//                         frappe.show_alert({
//                             message: `✅ ${tipo_vendita}: €${current_row.rate}`,
//                             indicator: 'green'
//                         });
//                         
//                         // Ricalcola totali documento
//                         setTimeout(() => {
//                             if (frm && frm.script_manager) {
//                                 frm.script_manager.trigger("calculate_taxes_and_totals");
//                             }
//                         }, 300);
//                     }
//                 } else {
//                     // Errore API
//                     row.note_calcolo = `📊 ${qty_info.display_qty} - Errore calcolo: ${r.message?.error || "API non disponibile"}`;
//                     frm.refresh_field("items");
//                 }
//             } catch (err) {
//                 console.error("Errore callback API:", err);
//                 row.note_calcolo = `📊 ${qty_info.display_qty} - Errore interno`;
//                 frm.refresh_field("items");
//             } finally {
//                 setTimeout(() => {
//                     iderp_calculating = false;
//                 }, 500);
//             }
//         },
//         error: function(err) {
//             console.error("Errore API call:", err);
//             row.note_calcolo = `📊 ${qty_info.display_qty} - Errore connessione`;
//             frm.refresh_field("items");
//             setTimeout(() => {
//                 iderp_calculating = false;
//             }, 500);
//         }
//     });
// }
// 
// // CALCOLO QUANTITÀ JS PER TUTTI I TIPI
// function calculate_base_quantities_js(row, tipo_vendita) {
//     try {
//         let qty = parseFloat(row.qty) || 1;
//         
//         if (tipo_vendita === "Metro Quadrato") {
//             let base = parseFloat(row.base) || 0;
//             let altezza = parseFloat(row.altezza) || 0;
//             
//             if (!base || !altezza) {
//                 return {
//                     mq_singolo: 0,
//                     mq_calcolati: 0,
//                     display_qty: "Inserire base e altezza",
//                     total_qty: 0
//                 };
//             }
//             
//             let mq_singolo = (base * altezza) / 10000;
//             let mq_totali = mq_singolo * qty;
//             
//             return {
//                 mq_singolo: parseFloat(mq_singolo.toFixed(4)),
//                 mq_calcolati: parseFloat(mq_totali.toFixed(3)),
//                 display_qty: `${mq_totali.toFixed(3)} m²`,
//                 total_qty: mq_totali
//             };
//             
//         } else if (tipo_vendita === "Metro Lineare") {
//             let lunghezza = parseFloat(row.lunghezza) || 0;
//             
//             if (!lunghezza) {
//                 return {
//                     ml_singolo: 0,
//                     ml_calcolati: 0,
//                     display_qty: "Inserire lunghezza",
//                     total_qty: 0
//                 };
//             }
//             
//             let ml_singolo = lunghezza / 100; // da cm a metri
//             let ml_totali = ml_singolo * qty;
//             
//             return {
//                 ml_singolo: parseFloat(ml_singolo.toFixed(2)),
//                 ml_calcolati: parseFloat(ml_totali.toFixed(2)),
//                 display_qty: `${ml_totali.toFixed(2)} ml`,
//                 total_qty: ml_totali
//             };
//             
//         } else if (tipo_vendita === "Pezzo") {
//             return {
//                 pz_singolo: 1,
//                 pz_totali: qty,
//                 display_qty: `${qty} pezzi`,
//                 total_qty: qty
//             };
//         }
//         
//         return null;
//         
//     } catch (e) {
//         console.error("Errore calcolo quantità:", e);
//         return null;
//     }
// }
// 
// // AGGIORNA STATUS TOOLBAR
// function update_toolbar_status(frm) {
//     if (!selected_item_row) {
//         frm.page.set_indicator("🎛️ Seleziona una riga per controlli", "blue");
//         return;
//     }
//     
//     let row = selected_item_row;
//     let tipo_vendita = row.tipo_vendita || "Pezzo";
//     let status = "";
//     let color = "";
//     
//     if (row.price_locked) {
//         status = "🔒 PREZZO BLOCCATO";
//         color = "red";
//     } else if (row.manual_rate_override) {
//         status = "🖊️ PREZZO MANUALE";
//         color = "orange";
//     } else if (row.auto_calculated) {
//         status = "🤖 CALCOLO AUTOMATICO";
//         color = "green";
//     } else {
//         status = "⚪ NON CALCOLATO";
//         color = "gray";
//     }
//     
//     frm.page.set_indicator(`${status} | ${tipo_vendita} | Item: ${row.item_code || 'nessuno'}`, color);
// }
// 
// // PULSANTI TOOLBAR
// function add_toolbar_buttons(frm) {
//     // Rimuovi pulsanti esistenti
//     frm.page.remove_inner_button("🔄 Ricalcola");
//     frm.page.remove_inner_button("🔒 Blocca");
//     frm.page.remove_inner_button("🔓 Sblocca");
//     
//     // Pulsante Ricalcola
//     frm.page.add_inner_button("🔄 Ricalcola", function() {
//         if (!selected_item_row) {
//             frappe.msgprint("Seleziona prima una riga nella tabella items!");
//             return;
//         }
//         
//         if (!frm.doc.customer) {
//             frappe.msgprint("Seleziona prima un cliente per calcolare i prezzi!");
//             return;
//         }
//         
//         // Reset flag e forza ricalcolo
//         selected_item_row.manual_rate_override = 0;
//         selected_item_row.price_locked = 0;
//         selected_item_row.auto_calculated = 0;
//         
//         calculate_universal_pricing(frm, selected_item_row.doctype, selected_item_row.name, true);
//     });
//     
//     // Pulsante Blocca
//     frm.page.add_inner_button("🔒 Blocca", function() {
//         if (!selected_item_row) {
//             frappe.msgprint("Seleziona prima una riga nella tabella items!");
//             return;
//         }
//         
//         selected_item_row.price_locked = 1;
//         selected_item_row.manual_rate_override = 1;
//         selected_item_row.auto_calculated = 0;
//         
//         // SAFE split
//         let base_note = "";
//         if (selected_item_row.note_calcolo) {
//             base_note = selected_item_row.note_calcolo.split('\n🤖')[0];
//         }
//         selected_item_row.note_calcolo = base_note + "\n🔒 PREZZO BLOCCATO - Non verrà ricalcolato";
//         
//         frm.refresh_field("items");
//         update_toolbar_status(frm);
//         
//         frappe.show_alert({
//             message: `🔒 Prezzo bloccato: €${selected_item_row.rate}`,
//             indicator: 'orange'
//         });
//     });
//     
//     // Pulsante Sblocca
//     frm.page.add_inner_button("🔓 Sblocca", function() {
//         if (!selected_item_row) {
//             frappe.msgprint("Seleziona prima una riga nella tabella items!");
//             return;
//         }
//         
//         selected_item_row.price_locked = 0;
//         selected_item_row.manual_rate_override = 0;
//         
//         // SAFE split
//         let base_note = "";
//         if (selected_item_row.note_calcolo) {
//             base_note = selected_item_row.note_calcolo.split('\n🔒')[0];
//         }
//         selected_item_row.note_calcolo = base_note + "\n🔓 PREZZO SBLOCCATO";
//         
//         frm.refresh_field("items");
//         update_toolbar_status(frm);
//         
//         frappe.show_alert({
//             message: `🔓 Prezzo sbloccato per ${selected_item_row.item_code}`,
//             indicator: 'green'
//         });
//     });
// }
// 
// // EVENTI UNIVERSALI
// frappe.ui.form.on('Quotation Item', {
//     // Metro Quadrato
//     base: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         let qty_info = calculate_base_quantities_js(row, row.tipo_vendita || "Pezzo");
//         if (qty_info) {
//             Object.assign(row, qty_info);
//             frm.refresh_field("items");
//             
//             if (!row.price_locked && frm.doc.customer && qty_info.total_qty > 0) {
//                 setTimeout(() => {
//                     calculate_universal_pricing(frm, cdt, cdn);
//                 }, 300);
//             }
//         }
//     },
//     
//     altezza: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         let qty_info = calculate_base_quantities_js(row, row.tipo_vendita || "Pezzo");
//         if (qty_info) {
//             Object.assign(row, qty_info);
//             frm.refresh_field("items");
//             
//             if (!row.price_locked && frm.doc.customer && qty_info.total_qty > 0) {
//                 setTimeout(() => {
//                     calculate_universal_pricing(frm, cdt, cdn);
//                 }, 300);
//             }
//         }
//     },
//     
//     // Metro Lineare
//     lunghezza: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         let qty_info = calculate_base_quantities_js(row, row.tipo_vendita || "Pezzo");
//         if (qty_info) {
//             Object.assign(row, qty_info);
//             frm.refresh_field("items");
//             
//             if (!row.price_locked && frm.doc.customer && qty_info.total_qty > 0) {
//                 setTimeout(() => {
//                     calculate_universal_pricing(frm, cdt, cdn);
//                 }, 300);
//             }
//         }
//     },
//     
//     // Quantità (tutti i tipi)
//     qty: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         let qty_info = calculate_base_quantities_js(row, row.tipo_vendita || "Pezzo");
//         if (qty_info) {
//             Object.assign(row, qty_info);
//             frm.refresh_field("items");
//             
//             if (!row.price_locked && frm.doc.customer && qty_info.total_qty > 0) {
//                 setTimeout(() => {
//                     calculate_universal_pricing(frm, cdt, cdn);
//                 }, 300);
//             }
//         }
//     },
//     
//     // Tipo vendita
//     tipo_vendita: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         
//         // Reset campi quando cambia tipo
//         row.base = 0;
//         row.altezza = 0;
//         row.lunghezza = 0;
//         row.mq_singolo = 0;
//         row.mq_calcolati = 0;
//         row.ml_singolo = 0;
//         row.ml_calcolati = 0;
//         row.pz_singolo = 0;
//         row.pz_totali = 0;
//         row.rate = 0;
//         row.amount = 0;
//         row.note_calcolo = "";
//         row.price_locked = 0;
//         row.manual_rate_override = 0;
//         row.auto_calculated = 0;
//         
//         frm.refresh_field("items");
//     },
//     
//     // Item code
//     item_code: function(frm, cdt, cdn) {
//         let row = locals[cdt][cdn];
//         if (row.item_code && row.tipo_vendita && frm.doc.customer) {
//             let qty_info = calculate_base_quantities_js(row, row.tipo_vendita);
//             if (qty_info && qty_info.total_qty > 0 && !row.price_locked) {
//                 setTimeout(() => {
//                     calculate_universal_pricing(frm, cdt, cdn);
//                 }, 500);
//             }
//         }
//     },
//     
//     // Rate manuale
//     rate: function(frm, cdt, cdn) {
//         if (iderp_calculating) return;
//         
//         let row = locals[cdt][cdn];
//         if (row) {
//             row.manual_rate_override = 1;
//             row.auto_calculated = 0;
//             row.price_locked = 0;
//             
//             let qty = parseFloat(row.qty) || 1;
//             let rate = parseFloat(row.rate) || 0;
//             row.amount = parseFloat((rate * qty).toFixed(2));
//             
//             let base_note = "";
//             if (row.note_calcolo && typeof row.note_calcolo === 'string') {
//                 base_note = row.note_calcolo.split('\n🤖')[0].split('\n🔒')[0];
//             }
//             row.note_calcolo = base_note + "\n🖊️ PREZZO MODIFICATO MANUALMENTE";
//             
//             selected_item_row = row;
//             frm.refresh_field("items");
//             update_toolbar_status(frm);
//         }
//     }
// });
// 
// // EVENTI QUOTATION
// frappe.ui.form.on('Quotation', {
//     refresh: function(frm) {
//         if (frm.doc.docstatus === 0) {
//             add_toolbar_buttons(frm);
//             update_toolbar_status(frm);
//         }
//     },
//     
//     customer: function(frm) {
//         if (frm.doc.items && frm.doc.customer) {
//             frm.doc.items.forEach(function(item) {
//                 if (item.tipo_vendita && !item.price_locked) {
//                     let qty_info = calculate_base_quantities_js(item, item.tipo_vendita);
//                     if (qty_info && qty_info.total_qty > 0) {
//                         setTimeout(() => {
//                             calculate_universal_pricing(frm, item.doctype, item.name, true);
//                         }, 500);
//                     }
//                 }
//             });
//         }
//     }
// });
// 
// // Event listener per selezione righe
// $(document).on('click', '[data-fieldname="items"] .grid-row', function() {
//     setTimeout(() => {
//         let grid_row = $(this).closest('.grid-row');
//         let docname = grid_row.attr('data-name');
//         
//         if (docname && cur_frm && cur_frm.doc.items) {
//             let item = cur_frm.doc.items.find(i => i.name === docname);
//             if (item) {
//                 selected_item_row = item;
//                 update_toolbar_status(cur_frm);
//             }
//         }
//     }, 100);
// });
// 
// console.log("✅ IDERP Universal Calculator caricato per tutti i tipi di vendita");