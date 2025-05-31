console.log("IDERP: Multi-Unit JS LOADED v2.1");

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

// Copia gli stessi eventi per altri DocType
frappe.ui.form.on('Sales Order Item', {
    tipo_vendita: function(frm, cdt, cdn) { reset_and_calculate(frm, cdt, cdn); },
    base: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
    altezza: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
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

frappe.ui.form.on('Sales Invoice Item', {
    tipo_vendita: function(frm, cdt, cdn) { reset_and_calculate(frm, cdt, cdn); },
    base: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
    altezza: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
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

frappe.ui.form.on('Delivery Note Item', {
    tipo_vendita: function(frm, cdt, cdn) { reset_and_calculate(frm, cdt, cdn); },
    base: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
    altezza: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
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

frappe.ui.form.on('Work Order Item', {
    tipo_vendita: function(frm, cdt, cdn) { reset_and_calculate(frm, cdt, cdn); },
    base: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
    altezza: function(frm, cdt, cdn) { calculate_price(frm, cdt, cdn); },
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

function reset_and_calculate(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    console.log("Reset e calcolo per tipo vendita:", row.tipo_vendita);
    
    // Reset tutti i campi quando cambia tipo vendita
    row.base = 0;
    row.altezza = 0;
    row.mq_calcolati = 0;
    row.larghezza_materiale = 0;
    row.lunghezza = 0;
    row.ml_calcolati = 0;
    row.prezzo_mq = 0;
    row.prezzo_ml = 0;
    row.note_calcolo = "";
    
    // Non resettare il rate se è vendita al pezzo
    if (row.tipo_vendita !== "Pezzo") {
        row.rate = 0;
    }
    
    frm.refresh_field("items");
    
    // Calcola subito dopo il reset
    calculate_price(frm, cdt, cdn);
}

function calculate_price(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    // Imposta default se non c'è tipo vendita
    if (!row.tipo_vendita) {
        row.tipo_vendita = "Pezzo";
    }
    
    console.log("Calcolando prezzo per:", {
        tipo_vendita: row.tipo_vendita,
        base: row.base,
        altezza: row.altezza,
        lunghezza: row.lunghezza,
        prezzo_mq: row.prezzo_mq,
        prezzo_ml: row.prezzo_ml
    });
    
    switch(row.tipo_vendita) {
        case "Metro Quadrato":
            calculate_square_meters(row);
            break;
        case "Metro Lineare":
            calculate_linear_meters(row);
            break;
        case "Pezzo":
        default:
            calculate_pieces(row);
            break;
    }
    
    frm.refresh_field("items");
}

function calculate_square_meters(row) {
    console.log("Calcolo metri quadrati:", row.base, "x", row.altezza);
    
    // Reset campi non utilizzati
    row.larghezza_materiale = 0;
    row.lunghezza = 0;
    row.ml_calcolati = 0;
    row.prezzo_ml = 0;
    
    if (row.base && row.altezza && row.base > 0 && row.altezza > 0) {
        // Calcola metri quadrati (da cm a m²)
        row.mq_calcolati = (row.base * row.altezza) / 10000;
        
        console.log("MQ calcolati:", row.mq_calcolati);
        
        if (row.prezzo_mq && row.prezzo_mq > 0) {
            row.rate = row.mq_calcolati * row.prezzo_mq;
            row.note_calcolo = `${row.mq_calcolati.toFixed(3)} m² × €${row.prezzo_mq} = €${row.rate.toFixed(2)}`;
            console.log("Prezzo calcolato:", row.rate);
        } else {
            row.rate = 0;
            row.note_calcolo = `${row.mq_calcolati.toFixed(3)} m² (inserire prezzo al m²)`;
        }
    } else {
        row.mq_calcolati = 0;
        row.rate = 0;
        row.note_calcolo = "Inserire base e altezza";
    }
}

function calculate_linear_meters(row) {
    console.log("Calcolo metri lineari:", row.lunghezza);
    
    // Reset campi non utilizzati
    row.base = 0;
    row.altezza = 0;
    row.mq_calcolati = 0;
    row.prezzo_mq = 0;
    
    if (row.lunghezza && row.lunghezza > 0) {
        // Calcola metri lineari (da cm a m)
        row.ml_calcolati = row.lunghezza / 100;
        
        console.log("ML calcolati:", row.ml_calcolati);
        
        if (row.prezzo_ml && row.prezzo_ml > 0) {
            row.rate = row.ml_calcolati * row.prezzo_ml;
            
            let note = `${row.ml_calcolati.toFixed(2)} ml × €${row.prezzo_ml}`;
            if (row.larghezza_materiale) {
                note += ` (largh. ${row.larghezza_materiale}cm)`;
            }
            note += ` = €${row.rate.toFixed(2)}`;
            row.note_calcolo = note;
            
            console.log("Prezzo calcolato:", row.rate);
        } else {
            row.rate = 0;
            row.note_calcolo = `${row.ml_calcolati.toFixed(2)} ml (inserire prezzo al ml)`;
        }
    } else {
        row.ml_calcolati = 0;
        row.rate = 0;
        row.note_calcolo = "Inserire lunghezza";
    }
}

function calculate_pieces(row) {
    console.log("Calcolo al pezzo");
    
    // Reset tutti i campi di misurazione
    row.base = 0;
    row.altezza = 0;
    row.mq_calcolati = 0;
    row.larghezza_materiale = 0;
    row.lunghezza = 0;
    row.ml_calcolati = 0;
    row.prezzo_mq = 0;
    row.prezzo_ml = 0;
    
    // Per vendita al pezzo, rate rimane come impostato manualmente
    if (row.rate && row.qty) {
        row.note_calcolo = `${row.qty} pz × €${row.rate} = €${(row.qty * row.rate).toFixed(2)}`;
    } else {
        row.note_calcolo = "Vendita al pezzo - inserire prezzo unitario";
    }
}