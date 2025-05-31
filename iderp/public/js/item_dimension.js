console.log("IDERP: Multi-Unit JS v5.0 - Con scaglioni reali");

// Cache per scaglioni item
var item_pricing_cache = {};

// Funzione principale per tutti i DocType
frappe.ui.form.on('Quotation Item', {
    tipo_vendita: function(frm, cdt, cdn) {
        reset_and_calculate(frm, cdt, cdn);
    },
    base: function(frm, cdt, cdn) {
        calculate_price(frm, cdt, cdn);
    },
    altezza: function(frm, cdt, cdn) {
        calculate_price(frm, cdt, cdn);
    },
    qty: function(frm, cdt, cdn) {
        calculate_price(frm, cdt, cdn);
    },
    prezzo_mq: function(frm, cdt, cdn) {
        calculate_price(frm, cdt, cdn);
    },
    larghezza_materiale: function(frm, cdt, cdn) {
        calculate_price(frm, cdt, cdn);
    },
    lunghezza: function(frm, cdt, cdn) {
        calculate_price(frm, cdt, cdn);
    },
    prezzo_ml: function(frm, cdt, cdn) {
        calculate_price(frm, cdt, cdn);
    },
    item_code: function(frm, cdt, cdn) {
        // Carica scaglioni quando cambia item
        load_item_pricing_tiers(frm, cdt, cdn);
    },
    refresh: function(frm) {
        $.each(frm.doc.items || [], function(i, row) {
            calculate_price(frm, row.doctype, row.name);
        });
    }
});

// Copia eventi per altri DocType
['Sales Order Item', 'Sales Invoice Item', 'Delivery Note Item', 'Work Order Item'].forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        tipo_vendita: function(frm, cdt, cdn) { reset_and_calculate(frm, cdt, cdn); },
        base: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
        altezza: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
        qty: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
        prezzo_mq: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
        larghezza_materiale: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
        lunghezza: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
        prezzo_ml: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
        item_code: function(frm, cdt, cdn) { load_item_pricing_tiers(frm, cdt, cdn); },
        refresh: function(frm) {
            $.each(frm.doc.items || [], function(i, row) {
                calculate_price(frm, row.doctype, row.name);
            });
        }
    });
});

function load_item_pricing_tiers(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    if (!row.item_code || row.tipo_vendita !== 'Metro Quadrato') {
        return;
    }
    
    // Verifica cache
    if (item_pricing_cache[row.item_code]) {
        row.pricing_tiers = item_pricing_cache[row.item_code];
        console.log("Scaglioni da cache per", row.item_code, ":", row.pricing_tiers);
        calculate_price(frm, cdt, cdn);
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
                calculate_price(frm, cdt, cdn);
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
    
    if (row.tipo_vendita !== "Pezzo") {
        row.rate = 0;
    }
    
    frm.refresh_field("items");
    calculate_price(frm, cdt, cdn);
}

function calculate_price(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    if (!row.tipo_vendita) {
        console.log("Nessun tipo vendita impostato");
        return;
    }
    
    console.log("Calcolando prezzo per:", {
        tipo_vendita: row.tipo_vendita,
        item_code: row.item_code,
        base: row.base,
        altezza: row.altezza,
        qty: row.qty,
        lunghezza: row.lunghezza
    });
    
    switch(row.tipo_vendita) {
        case "Metro Quadrato":
            calculate_square_meters_with_tiers(row, frm, cdt, cdn);
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

function calculate_square_meters_with_tiers(row, frm, cdt, cdn) {
    console.log("Calcolo metri quadrati con scaglioni:", row.base, "x", row.altezza, "x", row.qty);
    
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
    
    // Usa scaglioni se disponibili
    if (row.pricing_tiers && row.pricing_tiers.length > 0) {
        calculate_with_pricing_tiers(row, qty);
    } else if (row.prezzo_mq && row.prezzo_mq > 0) {
        // Fallback: usa prezzo manuale
        calculate_with_manual_price(row, qty);
    } else {
        // Carica scaglioni se non ci sono
        if (row.item_code) {
            load_item_pricing_tiers(frm, cdt, cdn);
        }
        row.note_calcolo = `${row.mq_calcolati.toFixed(3)} m² totali (${row.mq_singolo.toFixed(4)} m² × ${qty} pz)\nNessun prezzo configurato`;
        row.rate = 0;
    }
}

function calculate_with_pricing_tiers(row, qty) {
    var total_sqm = row.mq_calcolati;
    var price_per_sqm = 0;
    var tier_info = "";
    var found_tier = null;
    
    console.log("Cercando scaglione per", total_sqm, "m² in:", row.pricing_tiers);
    
    // Cerca scaglione appropriato
    for (let tier of row.pricing_tiers) {
        if (total_sqm >= tier.from_sqm) {
            // Se to_sqm è null/undefined, significa "oltre X m²"
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
    
    // Se non trova scaglione esatto, usa l'ultimo (più alto)
    if (price_per_sqm === 0 && row.pricing_tiers.length > 0) {
        // Ordina per from_sqm e prendi l'ultimo applicabile
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
    
    // Se ancora non trova, usa il default
    if (price_per_sqm === 0) {
        for (let tier of row.pricing_tiers) {
            if (tier.is_default) {
                price_per_sqm = tier.price_per_sqm;
                tier_info = (tier.tier_name || "Default") + " (Fallback)";
                found_tier = tier;
                break;
            }
        }
    }
    
    if (price_per_sqm > 0) {
        // Calcola prezzo unitario (per singolo pezzo)
        row.rate = row.mq_singolo * price_per_sqm;
        
        // Aggiorna campo prezzo_mq per coerenza
        row.prezzo_mq = price_per_sqm;
        
        row.note_calcolo = 
            `🎯 Scaglione: ${tier_info}\n` +
            `💰 Prezzo: €${price_per_sqm}/m²\n` +
            `📐 Dimensioni: ${row.base}×${row.altezza}cm\n` +
            `🔢 m² singolo: ${row.mq_singolo.toFixed(4)} m²\n` +
            `💵 Prezzo unitario: €${row.rate.toFixed(2)}\n` +
            `📦 Quantità: ${qty} pz\n` +
            `📊 m² totali: ${total_sqm.toFixed(3)} m²\n` +
            `💸 Totale ordine: €${(row.rate * qty).toFixed(2)}`;
        
        console.log("Prezzo calcolato con scaglioni:", {
            tier_info: tier_info,
            price_per_sqm: price_per_sqm,
            rate: row.rate,
            total: row.rate * qty
        });
    } else {
        row.rate = 0;
        row.note_calcolo = `${total_sqm.toFixed(3)} m² totali - Nessuno scaglione applicabile`;
        console.log("Nessuno scaglione trovato per", total_sqm, "m²");
    }
}

function calculate_with_manual_price(row, qty) {
    // Calcolo con prezzo manuale
    row.rate = row.mq_singolo * row.prezzo_mq;
    
    row.note_calcolo = 
        `📐 Dimensioni: ${row.base}×${row.altezza}cm\n` +
        `🔢 m² singolo: ${row.mq_singolo.toFixed(4)} m²\n` +
        `💰 Prezzo manuale: €${row.prezzo_mq}/m²\n` +
        `💵 Prezzo unitario: €${row.rate.toFixed(2)}\n` +
        `📦 Quantità: ${qty} pz\n` +
        `📊 m² totali: ${row.mq_calcolati.toFixed(3)} m²\n` +
        `💸 Totale ordine: €${(row.rate * qty).toFixed(2)}`;
        
    console.log("Prezzo calcolato manuale:", row.rate);
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