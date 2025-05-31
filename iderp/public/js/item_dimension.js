console.log("IDERP: Multi-Unit JS LOADED v3.0 - Con scaglioni prezzo");

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
        // Quando cambia item, carica scaglioni prezzo
        load_pricing_tiers(frm, cdt, cdn);
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
        item_code: function(frm, cdt, cdn) { load_pricing_tiers(frm, cdt, cdn); },
        refresh: function(frm) {
            $.each(frm.doc.items || [], function(i, row) {
                calculate_price(frm, row.doctype, row.name);
            });
        }
    });
});

function load_pricing_tiers(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    if (!row.item_code || row.tipo_vendita !== 'Metro Quadrato') {
        return;
    }
    
    // Carica scaglioni prezzo per questo item
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Pricing Tier',
            filters: {
                item_code: row.item_code
            },
            fields: ['from_sqm', 'to_sqm', 'price_per_sqm', 'is_default'],
            order_by: 'from_sqm asc'
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                row.pricing_tiers = r.message;
                console.log("Scaglioni caricati per", row.item_code, ":", r.message);
                
                // Mostra info scaglioni all'utente
                show_pricing_info(frm, row, r.message);
                
                // Ricalcola con i nuovi scaglioni
                calculate_price(frm, cdt, cdn);
            }
        }
    });
}

function show_pricing_info(frm, row, tiers) {
    // Crea messaggio informativo sugli scaglioni
    let info = "Scaglioni prezzo:\n";
    tiers.forEach(function(tier) {
        if (tier.to_sqm) {
            info += `${tier.from_sqm} - ${tier.to_sqm} m²: €${tier.price_per_sqm}/m²\n`;
        } else {
            info += `Oltre ${tier.from_sqm} m²: €${tier.price_per_sqm}/m²\n`;
        }
    });
    
    // Aggiorna campo note_calcolo con info scaglioni
    if (!row.note_calcolo || !row.note_calcolo.includes("Scaglioni")) {
        row.note_calcolo = info + (row.note_calcolo || "");
    }
}

function reset_and_calculate(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    console.log("Reset e calcolo per tipo vendita:", row.tipo_vendita);
    
    // Reset campi quando cambia tipo vendita
    row.base = 0;
    row.altezza = 0;
    row.mq_calcolati = 0;
    row.mq_singolo = 0;
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
    
    // Se ci sono scaglioni prezzo, usali
    if (row.pricing_tiers && row.pricing_tiers.length > 0) {
        calculate_with_pricing_tiers(row, qty);
    } else if (row.prezzo_mq && row.prezzo_mq > 0) {
        // Fallback: usa prezzo fisso
        row.rate = row.mq_singolo * row.prezzo_mq;
        row.note_calcolo = `${row.mq_singolo.toFixed(4)} m² × €${row.prezzo_mq} = €${row.rate.toFixed(2)} cad\nTotale: ${qty} pz × €${row.rate.toFixed(2)} = €${(row.rate * qty).toFixed(2)}`;
    } else {
        // Carica scaglioni se non ci sono
        load_pricing_tiers(frm, cdt, cdn);
        row.note_calcolo = `${row.mq_calcolati.toFixed(3)} m² totali (${row.mq_singolo.toFixed(4)} m² × ${qty} pz)\nCaricamento scaglioni prezzo...`;
    }
}

function calculate_with_pricing_tiers(row, qty) {
    // Trova scaglione appropriato in base ai m² totali
    var total_sqm = row.mq_calcolati;
    var price_per_sqm = 0;
    var tier_info = "";
    
    // Cerca scaglione corretto
    for (let tier of row.pricing_tiers) {
        if (total_sqm >= tier.from_sqm && (!tier.to_sqm || total_sqm <= tier.to_sqm)) {
            price_per_sqm = tier.price_per_sqm;
            tier_info = tier.to_sqm ? 
                `${tier.from_sqm}-${tier.to_sqm} m²` : 
                `oltre ${tier.from_sqm} m²`;
            break;
        }
    }
    
    // Se non trova scaglione, usa l'ultimo (più alto)
    if (price_per_sqm === 0 && row.pricing_tiers.length > 0) {
        var last_tier = row.pricing_tiers[row.pricing_tiers.length - 1];
        price_per_sqm = last_tier.price_per_sqm;
        tier_info = `oltre ${last_tier.from_sqm} m²`;
    }
    
    if (price_per_sqm > 0) {
        // Calcola prezzo unitario (per singolo pezzo)
        row.rate = row.mq_singolo * price_per_sqm;
        
        // Aggiorna campo prezzo_mq per coerenza
        row.prezzo_mq = price_per_sqm;
        
        row.note_calcolo = 
            `Scaglione: ${tier_info} = €${price_per_sqm}/m²\n` +
            `Singolo: ${row.mq_singolo.toFixed(4)} m² × €${price_per_sqm} = €${row.rate.toFixed(2)}\n` +
            `Totale: ${qty} pz × €${row.rate.toFixed(2)} = €${(row.rate * qty).toFixed(2)} (${total_sqm.toFixed(3)} m² tot)`;
        
        console.log("Prezzo calcolato con scaglioni:", {
            tier_info: tier_info,
            price_per_sqm: price_per_sqm,
            rate: row.rate,
            total: row.rate * qty
        });
    } else {
        row.rate = 0;
        row.note_calcolo = `${total_sqm.toFixed(3)} m² totali - Nessuno scaglione configurato`;
    }
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
    row.ml_calcolati = (row.lunghezza / 100) * qty;
    
    if (row.prezzo_ml && row.prezzo_ml > 0) {
        row.rate = (row.lunghezza / 100) * row.prezzo_ml;
        
        let note = `${(row.lunghezza / 100).toFixed(2)} ml × €${row.prezzo_ml} = €${row.rate.toFixed(2)} cad`;
        if (row.larghezza_materiale) {
            note += ` (largh. ${row.larghezza_materiale}cm)`;
        }
        note += `\nTotale: ${qty} pz × €${row.rate.toFixed(2)} = €${(row.rate * qty).toFixed(2)}`;
        row.note_calcolo = note;
        
        console.log("Prezzo ml calcolato:", row.rate);
    } else {
        row.note_calcolo = `${row.ml_calcolati.toFixed(2)} ml totali (inserire prezzo al ml)`;
    }
}

function calculate_pieces(row) {
    console.log("Calcolo al pezzo");
    
    var qty = row.qty || 1;
    
    if (row.rate && qty) {
        row.note_calcolo = `${qty} pz × €${row.rate} = €${(qty * row.rate).toFixed(2)}`;
    } else {
        row.note_calcolo = "Vendita al pezzo - inserire prezzo unitario";
    }
}