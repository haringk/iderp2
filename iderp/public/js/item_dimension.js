console.log("IDERP: Smart Calculator - Tempo reale + Override manuale");

// Flag per prevenire loop infiniti
var iderp_calculating = false;

// CALCOLO INTELLIGENTE
function smart_calculate_pricing(frm, cdt, cdn) {
    if (iderp_calculating) return; // Previeni loop
    
    let row = locals[cdt][cdn];
    if (!row || !row.item_code || row.tipo_vendita !== "Metro Quadrato") {
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
    
    // Chiamata API per calcolo prezzo con customer group
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
                    iderp_calculating = true; // Blocca eventi durante update
                    
                    // SOLO se NON è stato modificato manualmente
                    if (!row.manual_rate_override) {
                        row.rate = r.message.rate;
                        row.prezzo_mq = r.message.tier_info.price_per_sqm;
                    }
                    
                    row.note_calcolo = r.message.note_calcolo;
                    row.auto_calculated = 1; // Flag calcolo automatico
                    
                    frm.refresh_field("items");
                    
                    setTimeout(() => {
                        iderp_calculating = false; // Riabilita eventi
                    }, 100);
                }
            }
        });
    }
    
    frm.refresh_field("items");
}

// EVENTI QUOTATION ITEM
frappe.ui.form.on('Quotation Item', {
    // Calcolo automatico su campi misure
    base: function(frm, cdt, cdn) {
        setTimeout(() => smart_calculate_pricing(frm, cdt, cdn), 200);
    },
    
    altezza: function(frm, cdt, cdn) {
        setTimeout(() => smart_calculate_pricing(frm, cdt, cdn), 200);
    },
    
    qty: function(frm, cdt, cdn) {
        setTimeout(() => smart_calculate_pricing(frm, cdt, cdn), 200);
    },
    
    item_code: function(frm, cdt, cdn) {
        setTimeout(() => smart_calculate_pricing(frm, cdt, cdn), 300);
    },
    
    // OVERRIDE MANUALE - Importante!
    rate: function(frm, cdt, cdn) {
        if (iderp_calculating) return; // Ignora durante calcoli automatici
        
        let row = locals[cdt][cdn];
        
        // Marca come modificato manualmente
        row.manual_rate_override = 1;
        row.auto_calculated = 0;
        
        // Solo ricalcola amount
        let qty = parseFloat(row.qty) || 1;
        let rate = parseFloat(row.rate) || 0;
        row.amount = parseFloat((rate * qty).toFixed(2));
        
        // Aggiorna note
        row.note_calcolo = (row.note_calcolo || "").split('\n')[0] + 
                          "\n🖊️ PREZZO MODIFICATO MANUALMENTE";
        
        frm.refresh_field("items");
        frm.script_manager.trigger("calculate_taxes_and_totals");
    },
    
    // Reset override quando cambia tipo vendita
    tipo_vendita: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.manual_rate_override = 0;
        row.auto_calculated = 0;
        row.base = 0;
        row.altezza = 0;
        row.mq_singolo = 0;
        row.mq_calcolati = 0;
        row.rate = 0;
        row.note_calcolo = "";
        frm.refresh_field("items");
    }
});

// Evento cambio cliente
frappe.ui.form.on('Quotation', {
    customer: function(frm) {
        if (frm.doc.items) {
            frm.doc.items.forEach(function(item) {
                if (item.tipo_vendita === "Metro Quadrato" && 
                    item.base && item.altezza && 
                    !item.manual_rate_override) {
                    
                    setTimeout(() => smart_calculate_pricing(frm, item.doctype, item.name), 500);
                }
            });
        }
    },
    
    refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            frm.page.set_indicator("🧮 Calcolo automatico + override manuale", "green");
        }
    }
});

// Copia eventi per altri DocType
['Sales Order Item', 'Sales Invoice Item', 'Delivery Note Item'].forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        base: function(frm, cdt, cdn) {
            setTimeout(() => smart_calculate_pricing(frm, cdt, cdn), 200);
        },
        altezza: function(frm, cdt, cdn) {
            setTimeout(() => smart_calculate_pricing(frm, cdt, cdn), 200);
        },
        qty: function(frm, cdt, cdn) {
            setTimeout(() => smart_calculate_pricing(frm, cdt, cdn), 200);
        },
        rate: function(frm, cdt, cdn) {
            if (iderp_calculating) return;
            
            let row = locals[cdt][cdn];
            row.manual_rate_override = 1;
            row.auto_calculated = 0;
            
            let qty = parseFloat(row.qty) || 1;
            let rate = parseFloat(row.rate) || 0;
            row.amount = parseFloat((rate * qty).toFixed(2));
            
            row.note_calcolo = (row.note_calcolo || "").split('\n')[0] + 
                              "\n🖊️ PREZZO MODIFICATO MANUALMENTE";
            
            frm.refresh_field("items");
            frm.script_manager.trigger("calculate_taxes_and_totals");
        }
    });
});

console.log("✅ IDERP Smart Calculator: Tempo reale + Override abilitato");


/*


// IDERP: JavaScript Disabilitato - Solo Server-Side  
console.log("IDERP: Calcoli solo server-side - no loop infiniti");

// Solo eventi minimal per UX
frappe.ui.form.on('Quotation Item', {
    tipo_vendita: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.tipo_vendita !== "Metro Quadrato") {
            row.base = 0;
            row.altezza = 0;
            row.mq_singolo = 0; 
            row.mq_calcolati = 0;
        }
        frm.refresh_field("items");
    }
});

// Messaggio per utente
frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            frm.page.set_indicator("Calcoli al salvataggio", "orange");
        }
    }
});

console.log("✅ IDERP: Modalità server-side attiva");
*/

/*


console.log("IDERP: Multi-Unit JS v9.0 - DEFINITIVO CON MINIMI AUTOMATICI");

// Cache per item e relativi minimi
var item_config_cache = {};

// FLAG per prevenire loop infiniti - CRITICO
var iderp_calculation_locked = false;

// FUNZIONE PRINCIPALE: APPLICA MINIMO AUTOMATICO
function apply_minimum_automatic(frm, cdt, cdn) {
    // Previeni loop infiniti
    if (iderp_calculation_locked) {
        console.log("🛑 Calcolo bloccato per prevenire loop");
        return;
    }
    
    var row = locals[cdt][cdn];
    if (!row || !row.item_code || row.tipo_vendita !== "Metro Quadrato") {
        return;
    }
    
    var customer = frm.doc.customer || frm.doc.party_name;
    if (!customer) {
        console.log("⚠️ Nessun cliente - calcolo standard");
        calculate_standard_pricing(row);
        return;
    }
    
    // Blocca calcoli durante l'operazione
    iderp_calculation_locked = true;
    
    console.log("🧮 Applicando calcolo automatico con minimi per:", row.item_code);
    
    // Carica configurazione item
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Item',
            name: row.item_code
        },
        callback: function(r) {
            try {
                if (!r.message || !r.message.customer_group_minimums) {
                    console.log("⚠️ Nessun minimo configurato - calcolo standard");
                    calculate_standard_pricing(row);
                    return;
                }
                
                var item_doc = r.message;
                
                // Ottieni gruppo cliente
                frappe.db.get_value("Customer", customer, "customer_group").then(customer_r => {
                    try {
                        var customer_group = customer_r.message.customer_group;
                        
                        // Cerca minimo per questo gruppo
                        var minimum = item_doc.customer_group_minimums.find(
                            m => m.customer_group === customer_group && m.enabled
                        );
                        
                        if (!minimum) {
                            console.log("⚠️ Nessun minimo per gruppo", customer_group, "- calcolo standard");
                            calculate_standard_pricing(row);
                            return;
                        }
                        
                        // Calcola con minimi
                        calculate_pricing_with_minimums(row, item_doc, minimum, frm);
                        
                    } catch (err) {
                        console.log("❌ Errore gruppo cliente:", err);
                        calculate_standard_pricing(row);
                    } finally {
                        iderp_calculation_locked = false;
                    }
                }).catch(err => {
                    console.log("❌ Errore gruppo cliente:", err);
                    calculate_standard_pricing(row);
                    iderp_calculation_locked = false;
                });
                
            } catch (err) {
                console.log("❌ Errore item config:", err);
                calculate_standard_pricing(row);
                iderp_calculation_locked = false;
            }
        },
        error: function(err) {
            console.log("❌ Errore caricamento item:", err);
            calculate_standard_pricing(row);
            iderp_calculation_locked = false;
        }
    });
}

function calculate_pricing_with_minimums(row, item_doc, minimum, frm) {
    var base = parseFloat(row.base) || 0;
    var altezza = parseFloat(row.altezza) || 0;
    var qty = parseFloat(row.qty) || 1;
    
    if (!base || !altezza) {
        row.note_calcolo = "Inserire base e altezza";
        row.rate = 0;
        row.amount = 0;
        finalize_calculation(row, frm);
        return;
    }
    
    // Calcola m²
    var mq_singolo = (base * altezza) / 10000;
    var mq_totali = mq_singolo * qty;
    var mq_effettivi = Math.max(mq_totali, minimum.min_sqm);
    var minimo_applicato = mq_effettivi > mq_totali;
    
    row.mq_singolo = mq_singolo;
    row.mq_calcolati = mq_totali;
    
    // Trova scaglione prezzo
    var tier = null;
    if (item_doc.pricing_tiers && item_doc.pricing_tiers.length > 0) {
        tier = item_doc.pricing_tiers.find(t => 
            mq_effettivi >= t.from_sqm && 
            (!t.to_sqm || mq_effettivi <= t.to_sqm)
        );
    }
    
    if (!tier) {
        console.log("❌ Nessuno scaglione trovato per", mq_effettivi, "m²");
        if (row.prezzo_mq && row.prezzo_mq > 0) {
            // Usa prezzo manuale
            var calculated_rate = (mq_effettivi / qty) * row.prezzo_mq;
            row.rate = parseFloat(calculated_rate.toFixed(2));
        } else {
            row.rate = 0;
        }
    } else {
        // Calcola prezzo con scaglione
        var calculated_rate = (mq_effettivi / qty) * tier.price_per_sqm;
        row.rate = parseFloat(calculated_rate.toFixed(2));
        row.prezzo_mq = tier.price_per_sqm;
    }
    
    // Calcola amount
    row.amount = parseFloat((row.rate * qty).toFixed(2));
    
    // Crea note dettagliate
    var note = [];
    note.push(`🎯 Gruppo: ${minimum.customer_group}`);
    note.push(`📐 Dimensioni: ${base}×${altezza}cm`);
    note.push(`🔢 m² singolo: ${mq_singolo.toFixed(4)} m²`);
    note.push(`📦 Quantità: ${qty} pz`);
    note.push(`📊 m² originali: ${mq_totali.toFixed(3)} m²`);
    
    if (minimo_applicato) {
        note.push(`⚠️ MINIMO APPLICATO: ${minimum.min_sqm} m²`);
        note.push(`📈 m² fatturati: ${mq_effettivi.toFixed(3)} m²`);
    } else {
        note.push(`📈 m² fatturati: ${mq_effettivi.toFixed(3)} m²`);
    }
    
    if (tier) {
        note.push(`💰 Scaglione: ${tier.tier_name || (tier.from_sqm + '-' + (tier.to_sqm || '∞'))} (€${tier.price_per_sqm}/m²)`);
    } else if (row.prezzo_mq) {
        note.push(`💰 Prezzo manuale: €${row.prezzo_mq}/m²`);
    }
    
    note.push(`💵 Prezzo unitario: €${row.rate}`);
    note.push(`💸 Totale riga: €${row.amount}`);
    
    row.note_calcolo = note.join('\n');
    
    console.log("✅ Calcolo con minimi completato:", {
        mq_totali: mq_totali,
        mq_effettivi: mq_effettivi,
        minimo_applicato: minimo_applicato,
        rate: row.rate,
        amount: row.amount
    });
    
    finalize_calculation(row, frm);
}

function calculate_standard_pricing(row) {
    var base = parseFloat(row.base) || 0;
    var altezza = parseFloat(row.altezza) || 0;
    var qty = parseFloat(row.qty) || 1;
    
    if (!base || !altezza) {
        row.mq_singolo = 0;
        row.mq_calcolati = 0;
        row.rate = 0;
        row.amount = 0;
        row.note_calcolo = "Inserire base e altezza";
        return;
    }
    
    var mq_singolo = (base * altezza) / 10000;
    var mq_totali = mq_singolo * qty;
    
    row.mq_singolo = mq_singolo;
    row.mq_calcolati = mq_totali;
    
    if (row.prezzo_mq && row.prezzo_mq > 0) {
        var calculated_rate = mq_singolo * row.prezzo_mq;
        row.rate = parseFloat(calculated_rate.toFixed(2));
        row.amount = parseFloat((row.rate * qty).toFixed(2));
        
        row.note_calcolo = 
            `📐 Dimensioni: ${base}×${altezza}cm\n` +
            `🔢 m² singolo: ${mq_singolo.toFixed(4)} m²\n` +
            `💰 Prezzo: €${row.prezzo_mq}/m²\n` +
            `💵 Prezzo unitario: €${row.rate}\n` +
            `📦 Quantità: ${qty} pz\n` +
            `📊 m² totali: ${mq_totali.toFixed(3)} m²\n` +
            `💸 Totale riga: €${row.amount}`;
    } else {
        row.rate = 0;
        row.amount = 0;
        row.note_calcolo = `${mq_totali.toFixed(3)} m² totali - Inserire prezzo al m²`;
    }
    
    console.log("✅ Calcolo standard completato");
}

function finalize_calculation(row, frm) {
    // Aggiorna anche locals se esiste
    if (window.locals && window.locals[row.doctype] && window.locals[row.doctype][row.name]) {
        var locals_item = window.locals[row.doctype][row.name];
        locals_item.rate = row.rate;
        locals_item.amount = row.amount;
        locals_item.prezzo_mq = row.prezzo_mq;
        locals_item.note_calcolo = row.note_calcolo;
        locals_item.mq_singolo = row.mq_singolo;
        locals_item.mq_calcolati = row.mq_calcolati;
    }
    
    // Refresh campi
    frm.refresh_field("items");
    
    // Ricalcola totali documento con delay per evitare conflitti
    setTimeout(() => {
        if (frm && frm.script_manager) {
            frm.script_manager.trigger("calculate_taxes_and_totals");
        }
    }, 100);
}

// EVENTI FRAPPE - VERSIONE SAFE
frappe.ui.form.on('Quotation Item', {
    // Trigger automatico quando cambiano i dati rilevanti
    item_code: function(frm, cdt, cdn) {
        setTimeout(() => apply_minimum_automatic(frm, cdt, cdn), 200);
    },
    
    base: function(frm, cdt, cdn) {
        setTimeout(() => apply_minimum_automatic(frm, cdt, cdn), 200);
    },
    
    altezza: function(frm, cdt, cdn) {
        setTimeout(() => apply_minimum_automatic(frm, cdt, cdn), 200);
    },
    
    qty: function(frm, cdt, cdn) {
        setTimeout(() => apply_minimum_automatic(frm, cdt, cdn), 200);
    },
    
    tipo_vendita: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        // Reset campi quando cambia tipo vendita
        row.base = 0;
        row.altezza = 0;
        row.mq_singolo = 0;
        row.mq_calcolati = 0;
        row.rate = 0;
        row.amount = 0;
        row.note_calcolo = "";
        frm.refresh_field("items");
    },
    
    // Evento rate LIMITATO per evitare loop
    rate: function(frm, cdt, cdn) {
        if (iderp_calculation_locked) {
            return; // Blocca durante calcoli automatici
        }
        
        var row = locals[cdt][cdn];
        var qty = parseFloat(row.qty) || 1;
        var rate = parseFloat(row.rate) || 0;
        
        // Solo ricalcola amount, non triggerare altri eventi
        row.amount = parseFloat((rate * qty).toFixed(2));
        
        // Aggiorna locals
        if (window.locals && window.locals[row.doctype] && window.locals[row.doctype][row.name]) {
            window.locals[row.doctype][row.name].amount = row.amount;
        }
        
        // Non refreshare items per evitare loop, solo ricalcola totali
        if (frm && frm.script_manager) {
            frm.script_manager.trigger("calculate_taxes_and_totals");
        }
    }
});

// Evento quando cambia il cliente
frappe.ui.form.on('Quotation', {
    customer: function(frm) {
        console.log("Cliente cambiato:", frm.doc.customer);
        // Ricalcola tutti gli item con il nuovo cliente
        if (frm.doc.items) {
            frm.doc.items.forEach(function(item) {
                if (item.tipo_vendita === "Metro Quadrato" && item.base && item.altezza) {
                    setTimeout(() => apply_minimum_automatic(frm, item.doctype, item.name), 300);
                }
            });
        }
    }
});

// Copia eventi per altri DocType
['Sales Order Item', 'Sales Invoice Item', 'Delivery Note Item'].forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        item_code: function(frm, cdt, cdn) {
            setTimeout(() => apply_minimum_automatic(frm, cdt, cdn), 200);
        },
        base: function(frm, cdt, cdn) {
            setTimeout(() => apply_minimum_automatic(frm, cdt, cdn), 200);
        },
        altezza: function(frm, cdt, cdn) {
            setTimeout(() => apply_minimum_automatic(frm, cdt, cdn), 200);
        },
        qty: function(frm, cdt, cdn) {
            setTimeout(() => apply_minimum_automatic(frm, cdt, cdn), 200);
        },
        rate: function(frm, cdt, cdn) {
            if (iderp_calculation_locked) return;
            
            var row = locals[cdt][cdn];
            var qty = parseFloat(row.qty) || 1;
            var rate = parseFloat(row.rate) || 0;
            row.amount = parseFloat((rate * qty).toFixed(2));
            
            if (window.locals && window.locals[row.doctype] && window.locals[row.doctype][row.name]) {
                window.locals[row.doctype][row.name].amount = row.amount;
            }
            
            if (frm && frm.script_manager) {
                frm.script_manager.trigger("calculate_taxes_and_totals");
            }
        }
    });
});

// Copia eventi customer per altri DocType
['Sales Order', 'Sales Invoice', 'Delivery Note'].forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        customer: function(frm) {
            console.log("Cliente cambiato in", doctype, ":", frm.doc.customer);
            if (frm.doc.items) {
                frm.doc.items.forEach(function(item) {
                    if (item.tipo_vendita === "Metro Quadrato" && item.base && item.altezza) {
                        setTimeout(() => apply_minimum_automatic(frm, item.doctype, item.name), 300);
                    }
                });
            }
        }
    });
});

console.log("✅ IDERP Multi-Unit System con minimi automatici caricato");

*/