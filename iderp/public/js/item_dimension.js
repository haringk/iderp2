console.log("IDERP: Multi-Unit JS v7.0 - Con Minimi nell'Item");

// Cache per item e relativi minimi
var item_config_cache = {};

// Funzione principale per tutti i DocType
frappe.ui.form.on('Quotation Item', {
    tipo_vendita: function(frm, cdt, cdn) {
        reset_and_calculate(frm, cdt, cdn);
    },
    base: function(frm, cdt, cdn) {
        calculate_price_with_item_minimums(frm, cdt, cdn);
    },
    altezza: function(frm, cdt, cdn) {
        calculate_price_with_item_minimums(frm, cdt, cdn);
    },
    qty: function(frm, cdt, cdn) {
        calculate_price_with_item_minimums(frm, cdt, cdn);
    },
    prezzo_mq: function(frm, cdt, cdn) {
        calculate_price_with_item_minimums(frm, cdt, cdn);
    },
    larghezza_materiale: function(frm, cdt, cdn) {
        calculate_price_with_item_minimums(frm, cdt, cdn);
    },
    lunghezza: function(frm, cdt, cdn) {
        calculate_price_with_item_minimums(frm, cdt, cdn);
    },
    prezzo_ml: function(frm, cdt, cdn) {
        calculate_price_with_item_minimums(frm, cdt, cdn);
    },
    item_code: function(frm, cdt, cdn) {
        // Carica configurazione item quando cambia
        load_item_configuration(frm, cdt, cdn);
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
    }
});

// Hook per quando cambia il cliente nel documento principale
frappe.ui.form.on('Quotation', {
    customer: function(frm) {
        console.log("Cliente cambiato:", frm.doc.customer);
        // Pulisci cache
        item_config_cache = {};
        
        // Ricalcola tutti gli item con il nuovo cliente
        $.each(frm.doc.items || [], function(i, row) {
            calculate_price_with_item_minimums(frm, row.doctype, row.name);
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
        base: function(frm, cdt, cdn) { calculate_price_with_item_minimums(frm, cdt, cdn); },
        altezza: function(frm, cdt, cdn) { calculate_price_with_item_minimums(frm, cdt, cdn); },
        qty: function(frm, cdt, cdn) { calculate_price_with_item_minimums(frm, cdt, cdn); },
        prezzo_mq: function(frm, cdt, cdn) { calculate_price_with_item_minimums(frm, cdt, cdn); },
        larghezza_materiale: function(frm, cdt, cdn) { calculate_price_with_item_minimums(frm, cdt, cdn); },
        lunghezza: function(frm, cdt, cdn) { calculate_price_with_item_minimums(frm, cdt, cdn); },
        prezzo_ml: function(frm, cdt, cdn) { calculate_price_with_item_minimums(frm, cdt, cdn); },
        item_code: function(frm, cdt, cdn) { load_item_configuration(frm, cdt, cdn); },
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
        }
    });
});

// Aggiungi hook anche per i documenti principali
['Sales Order', 'Sales Invoice', 'Delivery Note'].forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        customer: function(frm) {
            console.log("Cliente cambiato:", frm.doc.customer);
            item_config_cache = {};
            $.each(frm.doc.items || [], function(i, row) {
                calculate_price_with_item_minimums(frm, row.doctype, row.name);
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

function load_item_configuration(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    if (!row.item_code) {
        return;
    }
    
    console.log("Caricando configurazione per item:", row.item_code);
    
    // Verifica cache
    if (item_config_cache[row.item_code]) {
        row.item_config = item_config_cache[row.item_code];
        console.log("Configurazione da cache per", row.item_code);
        calculate_price_with_item_minimums(frm, cdt, cdn);
        return;
    }
    
    // Carica configurazione item completa
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Item',
            name: row.item_code
        },
        callback: function(r) {
            if (r.message) {
                var item_doc = r.message;
                
                // Estrai configurazione rilevante
                var config = {
                    supports_custom_measurement: item_doc.supports_custom_measurement || 0,
                    tipo_vendita_default: item_doc.tipo_vendita_default || 'Pezzo',
                    pricing_tiers: item_doc.pricing_tiers || [],
                    customer_group_minimums: item_doc.customer_group_minimums || []
                };
                
                // Salva in cache
                item_config_cache[row.item_code] = config;
                row.item_config = config;
                
                console.log("Configurazione caricata per", row.item_code, ":", config);
                
                // Imposta tipo vendita default se non impostato
                if (!row.tipo_vendita && config.tipo_vendita_default) {
                    row.tipo_vendita = config.tipo_vendita_default;
                }
                
                // Ricalcola con la nuova configurazione
                calculate_price_with_item_minimums(frm, cdt, cdn);
                frm.refresh_field("items");
            }
        },
        error: function(r) {
            console.log("Errore caricamento item config:", r);
            row.item_config = null;
        }
    });
}

function calculate_price_with_item_minimums(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    if (!row.tipo_vendita) {
        console.log("Nessun tipo vendita impostato");
        return;
    }
    
    console.log("Calcolando prezzo con minimi item per:", {
        customer: frm.doc.customer,
        tipo_vendita: row.tipo_vendita,
        item_code: row.item_code,
        base: row.base,
        altezza: row.altezza,
        qty: row.qty
    });
    
    switch(row.tipo_vendita) {
        case "Metro Quadrato":
            calculate_square_meters_with_item_minimums(row, frm, cdt, cdn);
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

function calculate_square_meters_with_item_minimums(row, frm, cdt, cdn) {
    console.log("Calcolo metri quadrati con minimi item:", row.base, "x", row.altezza, "x", row.qty);
    
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
    
    // Ottieni minimo per gruppo cliente dalla configurazione item (asincrono)
    get_customer_group_minimum_from_item(row, frm.doc.customer, function(customer_group_minimum) {
        // Calcola con minimi applicati (ora nel callback)
        if (row.item_config && row.item_config.pricing_tiers && row.item_config.pricing_tiers.length > 0) {
            calculate_with_pricing_tiers_and_item_minimums(row, qty, customer_group_minimum);
        } else if (row.prezzo_mq && row.prezzo_mq > 0) {
            calculate_with_manual_price_and_item_minimums(row, qty, customer_group_minimum);
        } else {
            apply_item_minimum_only(row, qty, customer_group_minimum);
        }
        
        // Refresh dopo il calcolo
        frm.refresh_field("items");
    });
}

function get_customer_group_minimum_from_item(row, customer, callback) {
    // Ottieni minimo dal customer group minimums dell'item
    if (!row.item_config || !row.item_config.customer_group_minimums || !customer) {
        callback({min_sqm: 0, customer_group: null, source: "Nessun minimo configurato"});
        return;
    }
    
    // Ottieni gruppo del cliente
    frappe.db.get_value("Customer", customer, "customer_group").then(r => {
        if (!r.message || !r.message.customer_group) {
            callback({min_sqm: 0, customer_group: null, source: "Cliente senza gruppo"});
            return;
        }
        
        var customer_group = r.message.customer_group;
        
        // Cerca minimo per questo gruppo nei customer_group_minimums dell'item
        var matching_minimum = null;
        for (var i = 0; i < row.item_config.customer_group_minimums.length; i++) {
            var minimum = row.item_config.customer_group_minimums[i];
            if (minimum.customer_group === customer_group && minimum.enabled) {
                matching_minimum = minimum;
                break;
            }
        }
        
        if (matching_minimum) {
            callback({
                min_sqm: matching_minimum.min_sqm,
                customer_group: customer_group,
                description: matching_minimum.description,
                source: "Item configuration"
            });
        } else {
            callback({
                min_sqm: 0,
                customer_group: customer_group,
                source: "Nessun minimo per questo gruppo"
            });
        }
    }).catch(err => {
        console.log("Errore ottenimento customer group:", err);
        callback({min_sqm: 0, customer_group: null, source: "Errore"});
    });
}

function calculate_with_pricing_tiers_and_item_minimums(row, qty, minimum_info) {
    var total_sqm = row.mq_calcolati;
    var original_sqm = total_sqm;
    var min_applied = false;
    
    // Applica minimo se necessario
    if (minimum_info.min_sqm && total_sqm < minimum_info.min_sqm) {
        total_sqm = minimum_info.min_sqm;
        min_applied = true;
        console.log("Applicato minimo item:", minimum_info.min_sqm, "m² invece di", original_sqm);
    }
    
    var price_per_sqm = 0;
    var tier_info = "";
    var found_tier = null;
    
    console.log("Cercando scaglione per", total_sqm, "m² (originali:", original_sqm, ") in:", row.item_config.pricing_tiers);
    
    // Cerca scaglione appropriato basato sui m² effettivi (con minimo applicato)
    for (let tier of row.item_config.pricing_tiers) {
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
    if (price_per_sqm === 0 && row.item_config.pricing_tiers.length > 0) {
        var sorted_tiers = row.item_config.pricing_tiers.sort((a, b) => a.from_sqm - b.from_sqm);
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
        
        // Crea note dettagliate
        var note_parts = [
            `🎯 Scaglione: ${tier_info}`,
            `💰 Prezzo: €${price_per_sqm.toFixed(2)}/m²`,
            `📐 Dimensioni: ${row.base}×${row.altezza}cm`,
            `🔢 m² singolo: ${row.mq_singolo.toFixed(4)} m²`,
            `📦 Quantità: ${qty} pz`,
            `📊 m² originali: ${original_sqm.toFixed(3)} m²`
        ];
        
        if (min_applied && minimum_info.customer_group) {
            note_parts.push(`⚠️ MINIMO GRUPPO ${minimum_info.customer_group.toUpperCase()}: ${minimum_info.min_sqm} m²`);
            if (minimum_info.description) {
                note_parts.push(`💡 ${minimum_info.description}`);
            }
            note_parts.push(`📈 Fatturato su: ${total_sqm.toFixed(3)} m²`);
        } else {
            note_parts.push(`📈 m² fatturati: ${total_sqm.toFixed(3)} m²`);
        }
        
        note_parts.push(`💵 Prezzo unitario: €${calculated_rate.toFixed(2)}`);
        note_parts.push(`💸 Totale ordine: €${(calculated_rate * qty).toFixed(2)}`);
        
        row.note_calcolo = note_parts.join('\n');
        
        console.log("Prezzo calcolato con minimi item:", {
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

function calculate_with_manual_price_and_item_minimums(row, qty, minimum_info) {
    var total_sqm = row.mq_calcolati;
    var original_sqm = total_sqm;
    var min_applied = false;
    
    // Applica minimo se necessario
    if (minimum_info.min_sqm && total_sqm < minimum_info.min_sqm) {
        total_sqm = minimum_info.min_sqm;
        min_applied = true;
    }
    
    // Calcola prezzo basato sui m² effettivi
    var calculated_rate = (total_sqm / qty) * row.prezzo_mq;
    row.rate = Number(calculated_rate.toFixed(2));
    
    var note_parts = [
        `📐 Dimensioni: ${row.base}×${row.altezza}cm`,
        `🔢 m² singolo: ${row.mq_singolo.toFixed(4)} m²`,
        `💰 Prezzo manuale: €${row.prezzo_mq}/m²`,
        `📦 Quantità: ${qty} pz`,
        `📊 m² originali: ${original_sqm.toFixed(3)} m²`
    ];
    
    if (min_applied && minimum_info.customer_group) {
        note_parts.push(`⚠️ MINIMO GRUPPO ${minimum_info.customer_group.toUpperCase()}: ${minimum_info.min_sqm} m²`);
        if (minimum_info.description) {
            note_parts.push(`💡 ${minimum_info.description}`);
        }
        note_parts.push(`📈 Fatturato su: ${total_sqm.toFixed(3)} m²`);
    } else {
        note_parts.push(`📈 m² fatturati: ${total_sqm.toFixed(3)} m²`);
    }
    
    note_parts.push(`💵 Prezzo unitario: €${calculated_rate.toFixed(2)}`);
    note_parts.push(`💸 Totale ordine: €${(calculated_rate * qty).toFixed(2)}`);
    
    row.note_calcolo = note_parts.join('\n');
    
    console.log("Prezzo manuale con minimi item:", calculated_rate);
}

function apply_item_minimum_only(row, qty, minimum_info) {
    if (minimum_info.min_sqm && row.mq_calcolati < minimum_info.min_sqm && minimum_info.customer_group) {
        var note_parts = [
            `${row.mq_calcolati.toFixed(3)} m² totali`,
            `⚠️ MINIMO GRUPPO ${minimum_info.customer_group.toUpperCase()}: ${minimum_info.min_sqm} m²`
        ];
        if (minimum_info.description) {
            note_parts.push(`💡 ${minimum_info.description}`);
        }
        note_parts.push("Nessun prezzo configurato");
        row.note_calcolo = note_parts.join('\n');
    } else {
        row.note_calcolo = `${row.mq_calcolati.toFixed(3)} m² totali (${row.mq_singolo.toFixed(4)} m² × ${qty} pz)\nNessun prezzo configurato`;
    }
    row.rate = 0;
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
    
    if (row.tipo_vendita !== "Pezzo") {
        row.rate = 0;
    }
    
    frm.refresh_field("items");
    calculate_price_with_item_minimums(frm, cdt, cdn);
}

// Mantieni le funzioni esistenti per compatibilità
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