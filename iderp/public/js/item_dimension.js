console.log("IDERP: Multi-Unit JS v6.0 - Con Customer Group Pricing Semplificato");

// Cache per scaglioni item e minimi customer group
var item_pricing_cache = {};
var customer_group_cache = {};

// Funzione principale per tutti i DocType
frappe.ui.form.on('Quotation Item', {
    tipo_vendita: function(frm, cdt, cdn) {
        reset_and_calculate(frm, cdt, cdn);
    },
    base: function(frm, cdt, cdn) {
        calculate_price_with_customer_group(frm, cdt, cdn);
    },
    altezza: function(frm, cdt, cdn) {
        calculate_price_with_customer_group(frm, cdt, cdn);
    },
    qty: function(frm, cdt, cdn) {
        calculate_price_with_customer_group(frm, cdt, cdn);
    },
    prezzo_mq: function(frm, cdt, cdn) {
        calculate_price_with_customer_group(frm, cdt, cdn);
    },
    larghezza_materiale: function(frm, cdt, cdn) {
        calculate_price_with_customer_group(frm, cdt, cdn);
    },
    lunghezza: function(frm, cdt, cdn) {
        calculate_price_with_customer_group(frm, cdt, cdn);
    },
    prezzo_ml: function(frm, cdt, cdn) {
        calculate_price_with_customer_group(frm, cdt, cdn);
    },
    item_code: function(frm, cdt, cdn) {
        // Carica scaglioni quando cambia item
        load_item_pricing_tiers(frm, cdt, cdn);
    },
    rate: function(frm, cdt, cdn) {
        // NON ricalcolare quando l'utente modifica manualmente il rate
        var row = locals[cdt][cdn];
        if (row.tipo_vendita === "Metro Quadrato" && row.base && row.altezza) {
            var qty = row.qty || 1;
            row.note_calcolo = 
                `⚠️ PREZZO MANUALE\n` +
                `📐 Dimensioni: ${row.base}×${row.altezza}cm\n` +
                `🔢 m² singolo: ${row.mq_singolo || 0} m²\n` +
                `💵 Prezzo manuale: €${row.rate}\n` +
                `📦 Quantità: ${qty} pz\n` +
                `💸 Totale ordine: €${(row.rate * qty).toFixed(2)}`;
        }
        frm.refresh_field("items");
    },
    refresh: function(frm) {
        $.each(frm.doc.items || [], function(i, row) {
            calculate_price_with_customer_group(frm, row.doctype, row.name);
        });
    }
});

// Hook per quando cambia il cliente nel documento principale
frappe.ui.form.on('Quotation', {
    customer: function(frm) {
        console.log("Cliente cambiato:", frm.doc.customer);
        // Pulisci cache customer group
        customer_group_cache = {};
        
        // Ricalcola tutti gli item con il nuovo cliente
        $.each(frm.doc.items || [], function(i, row) {
            calculate_price_with_customer_group(frm, row.doctype, row.name);
        });
    },
    refresh: function(frm) {
        // Mostra info customer group se presente
        if (frm.doc.customer) {
            show_customer_group_info(frm);
        }
    }
});

// Copia eventi per altri DocType
['Sales Order Item', 'Sales Invoice Item', 'Delivery Note Item', 'Work Order Item'].forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        tipo_vendita: function(frm, cdt, cdn) { reset_and_calculate(frm, cdt, cdn); },
        base: function(frm, cdt, cdn) { calculate_price_with_customer_group(frm, cdt, cdn); },
        altezza: function(frm, cdt, cdn) { calculate_price_with_customer_group(frm, cdt, cdn); },
        qty: function(frm, cdt, cdn) { calculate_price_with_customer_group(frm, cdt, cdn); },
        prezzo_mq: function(frm, cdt, cdn) { calculate_price_with_customer_group(frm, cdt, cdn); },
        larghezza_materiale: function(frm, cdt, cdn) { calculate_price_with_customer_group(frm, cdt, cdn); },
        lunghezza: function(frm, cdt, cdn) { calculate_price_with_customer_group(frm, cdt, cdn); },
        prezzo_ml: function(frm, cdt, cdn) { calculate_price_with_customer_group(frm, cdt, cdn); },
        item_code: function(frm, cdt, cdn) { load_item_pricing_tiers(frm, cdt, cdn); },
        rate: function(frm, cdt, cdn) {
            var row = locals[cdt][cdn];
            if (row.tipo_vendita === "Metro Quadrato" && row.base && row.altezza) {
                var qty = row.qty || 1;
                row.note_calcolo = 
                    `⚠️ PREZZO MANUALE\n` +
                    `📐 Dimensioni: ${row.base}×${row.altezza}cm\n` +
                    `🔢 m² singolo: ${row.mq_singolo || 0} m²\n` +
                    `💵 Prezzo manuale: €${row.rate}\n` +
                    `📦 Quantità: ${qty} pz\n` +
                    `💸 Totale ordine: €${(row.rate * qty).toFixed(2)}`;
            }
            frm.refresh_field("items");
        },
        refresh: function(frm) {
            $.each(frm.doc.items || [], function(i, row) {
                calculate_price_with_customer_group(frm, row.doctype, row.name);
            });
        }
    });
});

// Aggiungi hook anche per i documenti principali
['Sales Order', 'Sales Invoice', 'Delivery Note'].forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        customer: function(frm) {
            console.log("Cliente cambiato:", frm.doc.customer);
            customer_group_cache = {};
            $.each(frm.doc.items || [], function(i, row) {
                calculate_price_with_customer_group(frm, row.doctype, row.name);
            });
        },
        refresh: function(frm) {
            if (frm.doc.customer) {
                show_customer_group_info(frm);
            }
        }
    });
});

function show_customer_group_info(frm) {
    // Mostra informazioni gruppo cliente
    if (!frm.doc.customer) return;
    
    frappe.db.get_value("Customer", frm.doc.customer, "customer_group").then(r => {
        if (r.message && r.message.customer_group) {
            var group = r.message.customer_group;
            
            // Scegli colore badge in base al gruppo
            var badge_color = "blue";
            if (group === "Diamond") badge_color = "purple";
            else if (group === "Gold") badge_color = "orange";
            else if (group === "Bronze") badge_color = "green";
            else if (group === "Finale") badge_color = "gray";
            
            // Aggiungi badge o info visiva
            if (!frm.customer_group_indicator) {
                frm.customer_group_indicator = frm.page.add_label(
                    `👥 Gruppo: ${group}`, 
                    badge_color
                );
            } else {
                frm.customer_group_indicator.text(`👥 Gruppo: ${group}`);
                frm.customer_group_indicator.removeClass().addClass(`label label-${badge_color}`);
            }
        }
    });
}

function calculate_price_with_customer_group(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    if (!row.tipo_vendita) {
        console.log("Nessun tipo vendita impostato");
        return;
    }
    
    console.log("Calcolando prezzo con customer group per:", {
        customer: frm.doc.customer,
        tipo_vendita: row.tipo_vendita,
        item_code: row.item_code,
        base: row.base,
        altezza: row.altezza,
        qty: row.qty
    });
    
    switch(row.tipo_vendita) {
        case "Metro Quadrato":
            calculate_square_meters_with_customer_group(row, frm, cdt, cdn);
            break;
        case "Metro Lineare":
            calculate_linear_meters(row);
            break;
        case "Pezzo":
            calculate_pieces(row);
            break;
        default:
            console.log("Tipo vendita non riconosciuto:", row.tipo_vendita);
            return;
    }
    
    frm.refresh_field("items");
}

function calculate_square_meters_with_customer_group(row, frm, cdt, cdn) {
    console.log("Calcolo metri quadrati con customer group:", row.base, "x", row.altezza, "x", row.qty);
    
    if (!row.base || !row.altezza || row.base <= 0 || row.altezza <= 0) {
        row.mq_singolo = 0;
        row.mq_calcolati = 0;
        row.rate = 0;
        row.note_calcolo = "Inserire base e altezza";
        return;
    }
    
    // Calcola m² per singolo pezzo
    row.mq_singolo = (row.base * row.altezza) / 10000;
    
    // Calcola m² totali (singolo × quantità)
    var qty = row.qty || 1;
    row.mq_calcolati = row.mq_singolo * qty;
    
    console.log("MQ singolo:", row.mq_singolo, "MQ totali:", row.mq_calcolati);
    
    // Prima carica minimi customer group se disponibili
    if (frm.doc.customer && row.item_code) {
        load_customer_group_min_sqm(frm.doc.customer, row.item_code, function(min_info) {
            // Poi calcola con scaglioni + minimi customer group
            if (row.pricing_tiers && row.pricing_tiers.length > 0) {
                calculate_with_pricing_tiers_and_min_sqm(row, qty, min_info);
            } else if (row.prezzo_mq && row.prezzo_mq > 0) {
                calculate_with_manual_price_and_min_sqm(row, qty, min_info);
            } else {
                // Carica scaglioni se non ci sono
                if (row.item_code) {
                    load_item_pricing_tiers(frm, cdt, cdn);
                }
                apply_customer_group_minimum(row, qty, min_info);
            }
        });
    } else {
        // Fallback senza customer group
        if (row.pricing_tiers && row.pricing_tiers.length > 0) {
            calculate_with_pricing_tiers(row, qty);
        } else if (row.prezzo_mq && row.prezzo_mq > 0) {
            calculate_with_manual_price(row, qty);
        } else {
            row.note_calcolo = `${row.mq_calcolati.toFixed(3)} m² totali - Nessun prezzo configurato`;
            row.rate = 0;
        }
    }
}

function load_customer_group_min_sqm(customer, item_code, callback) {
    var cache_key = `${customer}-${item_code}`;
    
    // Verifica cache
    if (customer_group_cache[cache_key]) {
        console.log("Customer group min da cache per", cache_key);
        callback(customer_group_cache[cache_key]);
        return;
    }
    
    // Carica minimi dall'API
    frappe.call({
        method: 'iderp.pricing_utils.get_customer_group_min_sqm',
        args: {
            customer: customer,
            item_code: item_code
        },
        callback: function(r) {
            var min_info = r.message || {min_sqm: 0};
            customer_group_cache[cache_key] = min_info;
            
            console.log("Customer group min caricato per", cache_key, ":", min_info);
            callback(min_info);
        },
        error: function(r) {
            console.log("Errore caricamento customer group min:", r);
            callback({min_sqm: 0});
        }
    });
}

function calculate_with_pricing_tiers_and_min_sqm(row, qty, min_info) {
    var total_sqm = row.mq_calcolati;
    var original_sqm = total_sqm;
    var min_applied = false;
    
    // Applica minimo se necessario
    if (min_info.min_sqm && total_sqm < min_info.min_sqm) {
        total_sqm = min_info.min_sqm;
        min_applied = true;
        console.log("Applicato minimo:", min_info.min_sqm, "m² invece di", original_sqm);
    }
    
    var price_per_sqm = 0;
    var tier_info = "";
    var found_tier = null;
    
    console.log("Cercando scaglione per", total_sqm, "m² (originali:", original_sqm, ") in:", row.pricing_tiers);
    
    // Cerca scaglione appropriato basato sui m² effettivi (con minimo applicato)
    for (let tier of row.pricing_tiers) {
        if (total_sqm >= tier.from_sqm) {
            if (!tier.to_sqm || total_sqm <= tier.to_sqm) {
                price_per_sqm = tier.price_per_sqm;
                tier_info = tier.tier_name || 
                    (tier.to_sqm ? 
                        `${tier.from_sqm}-${tier.to_sqm} m²` : 
                        `oltre ${tier.from_sqm} m²`);
                found_tier = tier;
                break;
            }
        }
    }
    
    // Fallback se non trova scaglione
    if (price_per_sqm === 0 && row.pricing_tiers.length > 0) {
        var sorted_tiers = row.pricing_tiers.sort((a, b) => a.from_sqm - b.from_sqm);
        for (let tier of sorted_tiers.reverse()) {
            if (total_sqm >= tier.from_sqm) {
                price_per_sqm = tier.price_per_sqm;
                tier_info = tier.tier_name || `oltre ${tier.from_sqm} m²`;
                found_tier = tier;
                break;
            }
        }
    }
    
    if (price_per_sqm > 0) {
        // Calcola prezzo unitario basato sui m² effettivi
        var calculated_rate = (total_sqm / qty) * price_per_sqm;
        
        // Imposta il prezzo
        row.rate = Number(calculated_rate.toFixed(2));
        row.prezzo_mq = price_per_sqm;
        
        // Segna che sono state applicate regole
        row.customer_group_rules_applied = min_applied ? 1 : 0;
        
        // Crea note dettagliate
        var note_parts = [
            `🎯 Scaglione: ${tier_info}`,
            `💰 Prezzo: €${price_per_sqm.toFixed(2)}/m²`,
            `📐 Dimensioni: ${row.base}×${row.altezza}cm`,
            `🔢 m² singolo: ${row.mq_singolo.toFixed(4)} m²`,
            `📦 Quantità: ${qty} pz`,
            `📊 m² originali: ${original_sqm.toFixed(3)} m²`
        ];
        
        if (min_applied) {
            note_parts.push(`⚠️ MINIMO GRUPPO ${min_info.customer_group}: ${min_info.min_sqm} m²`);
            note_parts.push(`📈 Fatturato su: ${total_sqm.toFixed(3)} m²`);
        } else {
            note_parts.push(`📈 m² fatturati: ${total_sqm.toFixed(3)} m²`);
        }
        
        note_parts.push(`💵 Prezzo unitario: €${calculated_rate.toFixed(2)}`);
        note_parts.push(`💸 Totale ordine: €${(calculated_rate * qty).toFixed(2)}`);
        
        row.note_calcolo = note_parts.join('\n');
        
        console.log("Prezzo calcolato con customer group:", {
            tier_info: tier_info,
            price_per_sqm: price_per_sqm,
            original_sqm: original_sqm,
            effective_sqm: total_sqm,
            min_applied: min_applied,
            rate: calculated_rate
        });
        
    } else {
        row.rate = 0;
        row.note_calcolo = `${total_sqm.toFixed(3)} m² totali - Nessuno scaglione applicabile`;
        console.log("Nessuno scaglione trovato per", total_sqm, "m²");
    }
}

function calculate_with_manual_price_and_min_sqm(row, qty, min_info) {
    var total_sqm = row.mq_calcolati;
    var original_sqm = total_sqm;
    var min_applied = false;
    
    // Applica minimo se necessario
    if (min_info.min_sqm && total_sqm < min_info.min_sqm) {
        total_sqm = min_info.min_sqm;
        min_applied = true;
    }
    
    // Calcola prezzo basato sui m² effettivi
    var calculated_rate = (total_sqm / qty) * row.prezzo_mq;
    row.rate = Number(calculated_rate.toFixed(2));
    row.customer_group_rules_applied = min_applied ? 1 : 0;
    
    var note_parts = [
        `📐 Dimensioni: ${row.base}×${row.altezza}cm`,
        `🔢 m² singolo: ${row.mq_singolo.toFixed(4)} m²`,
        `💰 Prezzo manuale: €${row.prezzo_mq}/m²`,
        `📦 Quantità: ${qty} pz`,
        `📊 m² originali: ${original_sqm.toFixed(3)} m²`
    ];
    
    if (min_applied) {
        note_parts.push(`⚠️ MINIMO GRUPPO ${min_info.customer_group}: ${min_info.min_sqm} m²`);
        note_parts.push(`📈 Fatturato su: ${total_sqm.toFixed(3)} m²`);
    } else {
        note_parts.push(`📈 m² fatturati: ${total_sqm.toFixed(3)} m²`);
    }
    
    note_parts.push(`💵 Prezzo unitario: €${calculated_rate.toFixed(2)}`);
    note_parts.push(`💸 Totale ordine: €${(calculated_rate * qty).toFixed(2)}`);
    
    row.note_calcolo = note_parts.join('\n');
    
    console.log("Prezzo manuale con customer group:", calculated_rate);
}

function apply_customer_group_minimum(row, qty, min_info) {
    if (min_info.min_sqm && row.mq_calcolati < min_info.min_sqm) {
        row.note_calcolo = `${row.mq_calcolati.toFixed(3)} m² totali\n⚠️ MINIMO GRUPPO ${min_info.customer_group}: ${min_info.min_sqm} m²\nNessun prezzo configurato`;
    } else {
        row.note_calcolo = `${row.mq_calcolati.toFixed(3)} m² totali (${row.mq_singolo.toFixed(4)} m² × ${qty} pz)\nNessun prezzo configurato`;
    }
    row.rate = 0;
}

// Mantieni tutte le altre funzioni esistenti...
function load_item_pricing_tiers(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    if (!row.item_code || row.tipo_vendita !== 'Metro Quadrato') {
        return;
    }
    
    // Verifica cache
    if (item_pricing_cache[row.item_code]) {
        row.pricing_tiers = item_pricing_cache[row.item_code];
        console.log("Scaglioni da cache per", row.item_code, ":", row.pricing_tiers);
        calculate_price_with_customer_group(frm, cdt, cdn);
        return;
    }
    
    // Carica scaglioni dall'API
    frappe.call({
        method: 'iderp.pricing_utils.get_item_pricing_tiers',
        args: {
            item_code: row.item_code
        },
        callback: function(r) {
            if (r.message && r.message.tiers) {
                row.pricing_tiers = r.message.tiers;
                item_pricing_cache[row.item_code] = r.message.tiers;
                
                console.log("Scaglioni caricati per", row.item_code, ":", r.message.tiers);
                
                // Ricalcola con i nuovi scaglioni
                calculate_price_with_customer_group(frm, cdt, cdn);
            } else if (r.message && r.message.error) {
                console.log("Errore caricamento scaglioni:", r.message.error);
                row.pricing_tiers = [];
            } else {
                console.log("Nessuno scaglione configurato per", row.item_code);
                row.pricing_tiers = [];
            }
        },
        error: function(r) {
            console.log("Errore API scaglioni:", r);
            row.pricing_tiers = [];
        }
    });
}

function reset_and_calculate(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    console.log("Reset e calcolo per tipo vendita:", row.tipo_vendita);
    
    // Reset campi quando cambia tipo vendita
    row.base = 0;
    row.altezza = 0;
    row.mq_singolo = 0;
    row.mq_calcolati = 0;
    row.larghezza_materiale = 0;
    row.lunghezza = 0;
    row.ml_calcolati = 0;
    row.prezzo_mq = 0;
    row.prezzo_ml = 0;
    row.note_calcolo = "";
    row.customer_group_rules_applied = 0;
    
    if (row.tipo_vendita !== "Pezzo") {
        row.rate = 0;
    }
    
    frm.refresh_field("items");
    calculate_price_with_customer_group(frm, cdt, cdn);
}

// Mantieni le funzioni esistenti per compatibilità
function calculate_with_pricing_tiers(row, qty) {
    // Versione senza customer group (fallback)
    calculate_with_pricing_tiers_and_min_sqm(row, qty, {min_sqm: 0});
}

function calculate_with_manual_price(row, qty) {
    // Versione senza customer group (fallback)  
    calculate_with_manual_price_and_min_sqm(row, qty, {min_sqm: 0});
}

function calculate_linear_meters(row) {
    console.log("Calcolo metri lineari:", row.lunghezza);
    
    if (!row.lunghezza || row.lunghezza <= 0) {
        row.ml_calcolati = 0;
        row.rate = 0;
        row.note_calcolo = "Inserire lunghezza";
        return;
    }
    
    var qty = row.qty || 1;
    var ml_singolo = row.lunghezza / 100;
    row.ml_calcolati = ml_singolo * qty;
    
    if (row.prezzo_ml && row.prezzo_ml > 0) {
        row.rate = ml_singolo * row.prezzo_ml;
        
        let note = `📏 Lunghezza: ${row.lunghezza}cm = ${ml_singolo.toFixed(2)} ml\n`;
        if (row.larghezza_materiale) {
            note += `📐 Larghezza materiale: ${row.larghezza_materiale}cm\n`;
        }
        note += `💰 Prezzo: €${row.prezzo_ml}/ml\n`;
        note += `💵 Prezzo unitario: €${row.rate.toFixed(2)}\n`;
        note += `📦 Quantità: ${qty} pz\n`;
        note += `📊 ml totali: ${row.ml_calcolati.toFixed(2)} ml\n`;
        note += `💸 Totale ordine: €${(row.rate * qty).toFixed(2)}`;
        
        row.note_calcolo = note;
        console.log("Prezzo ml calcolato:", row.rate);
    } else {
        row.note_calcolo = `📏 ml totali: ${row.ml_calcolati.toFixed(2)} ml (${qty} pz)\nInserire prezzo al ml`;
    }
}

function calculate_pieces(row) {
    console.log("Calcolo al pezzo");
    
    var qty = row.qty || 1;
    
    if (row.rate && qty) {
        row.note_calcolo = 
            `📦 Vendita al pezzo\n` +
            `💵 Prezzo unitario: €${row.rate}\n` +
            `📦 Quantità: ${qty} pz\n` +
            `💸 Totale: €${(qty * row.rate).toFixed(2)}`;
    } else {
        row.note_calcolo = "Vendita al pezzo - inserire prezzo unitario";
    }
}