console.log("IDERP: Multi-Unit JS LOADED v3.1 - Base senza scaglioni");

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
        refresh: function(frm) {
            $.each(frm.doc.items || [], function(i, row) {
                calculate_price(frm, row.doctype, row.name);
            });
        }
    });
});

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
        base: row.base,
        altezza: row.altezza,
        qty: row.qty,
        lunghezza: row.lunghezza
    });
    
    switch(row.tipo_vendita) {
        case "Metro Quadrato":
            calculate_square_meters_basic(row);
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

function calculate_square_meters_basic(row) {
    console.log("Calcolo metri quadrati basic:", row.base, "x", row.altezza, "x", row.qty);
    
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
    
    // Calcolo prezzo con prezzo_mq fisso
    if (row.prezzo_mq && row.prezzo_mq > 0) {
        // Rate = prezzo per singolo pezzo
        row.rate = row.mq_singolo * row.prezzo_mq;
        
        // Note dettagliate
        row.note_calcolo = 
            `Dimensioni: ${row.base}×${row.altezza}cm\n` +
            `m² singolo: ${row.mq_singolo.toFixed(4)} m²\n` +
            `Prezzo unitario: ${row.mq_singolo.toFixed(4)} × €${row.prezzo_mq} = €${row.rate.toFixed(2)}\n` +
            `Quantità: ${qty} pz\n` +
            `m² totali: ${row.mq_calcolati.toFixed(3)} m²\n` +
            `Totale ordine: ${qty} × €${row.rate.toFixed(2)} = €${(row.rate * qty).toFixed(2)}`;
        
        console.log("Prezzo calcolato:", {
            mq_singolo: row.mq_singolo,
            mq_totali: row.mq_calcolati,
            rate: row.rate,
            total: row.rate * qty
        });
    } else {
        row.rate = 0;
        row.note_calcolo = 
            `Dimensioni: ${row.base}×${row.altezza}cm\n` +
            `m² singolo: ${row.mq_singolo.toFixed(4)} m²\n` +
            `m² totali: ${row.mq_calcolati.toFixed(3)} m² (${qty} pz)\n` +
            `Inserire prezzo al m²`;
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
    
    // Calcola metri lineari singolo
    var ml_singolo = row.lunghezza / 100;
    
    // Calcola metri lineari totali
    row.ml_calcolati = ml_singolo * qty;
    
    if (row.prezzo_ml && row.prezzo_ml > 0) {
        row.rate = ml_singolo * row.prezzo_ml;
        
        let note = `Lunghezza: ${row.lunghezza}cm = ${ml_singolo.toFixed(2)} ml\n`;
        if (row.larghezza_materiale) {
            note += `Larghezza materiale: ${row.larghezza_materiale}cm\n`;
        }
        note += `Prezzo unitario: ${ml_singolo.toFixed(2)} × €${row.prezzo_ml} = €${row.rate.toFixed(2)}\n`;
        note += `Quantità: ${qty} pz\n`;
        note += `ml totali: ${row.ml_calcolati.toFixed(2)} ml\n`;
        note += `Totale ordine: ${qty} × €${row.rate.toFixed(2)} = €${(row.rate * qty).toFixed(2)}`;
        
        row.note_calcolo = note;
        
        console.log("Prezzo ml calcolato:", row.rate);
    } else {
        row.note_calcolo = 
            `Lunghezza: ${row.lunghezza}cm = ${ml_singolo.toFixed(2)} ml\n` +
            `ml totali: ${row.ml_calcolati.toFixed(2)} ml (${qty} pz)\n` +
            `Inserire prezzo al ml`;
    }
}

function calculate_pieces(row) {
    console.log("Calcolo al pezzo");
    
    var qty = row.qty || 1;
    
    if (row.rate && qty) {
        row.note_calcolo = 
            `Vendita al pezzo\n` +
            `Prezzo unitario: €${row.rate}\n` +
            `Quantità: ${qty} pz\n` +
            `Totale: ${qty} × €${row.rate} = €${(qty * row.rate).toFixed(2)}`;
    } else {
        row.note_calcolo = "Vendita al pezzo - inserire prezzo unitario";
    }
}