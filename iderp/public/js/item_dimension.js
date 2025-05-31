console.log("IDERP: Multi-Unit JS LOADED v2.0");

// Lista di tutti i DocType supportati
const SUPPORTED_DOCTYPES = [
    'Quotation Item',
    'Sales Order Item', 
    'Sales Invoice Item',
    'Delivery Note Item',
    'Work Order Item'
];

// Applica gli eventi a tutti i DocType
SUPPORTED_DOCTYPES.forEach(function(doctype) {
    frappe.ui.form.on(doctype, {
        // Cambio tipo vendita
        tipo_vendita: function(frm, cdt, cdn) {
            reset_and_calculate(frm, cdt, cdn);
        },
        
        // Eventi per metri quadrati
        base: function(frm, cdt, cdn) {
            calculate_price(frm, cdt, cdn);
        },
        altezza: function(frm, cdt, cdn) {
            calculate_price(frm, cdt, cdn);
        },
        prezzo_mq: function(frm, cdt, cdn) {
            calculate_price(frm, cdt, cdn);
        },
        
        // Eventi per metri lineari
        larghezza_materiale: function(frm, cdt, cdn) {
            calculate_price(frm, cdt, cdn);
        },
        lunghezza: function(frm, cdt, cdn) {
            calculate_price(frm, cdt, cdn);
        },
        prezzo_ml: function(frm, cdt, cdn) {
            calculate_price(frm, cdt, cdn);
        },
        
        // Refresh generale
        refresh: function(frm) {
            $.each(frm.doc.items || [], function(i, row) {
                calculate_price(frm, row.doctype, row.name);
            });
        }
    });
});

function reset_and_calculate(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    // Reset tutti i campi quando cambia tipo vendita
    row.base = 0;
    row.altezza = 0;
    row.mq_calcolati = 0;
    row.larghezza_materiale = 0;
    row.lunghezza = 0;
    row.ml_calcolati = 0;
    row.prezzo_mq = 0;
    row.prezzo_ml = 0;
    row.rate = 0;
    row.note_calcolo = "";
    
    frm.refresh_field("items");
    
    console.log("Reset campi per tipo vendita:", row.tipo_vendita);
}

function calculate_price(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    if (!row.tipo_vendita) {
        row.tipo_vendita = "Pezzo";
    }
    
    console.log("Calcolando prezzo per:", row.tipo_vendita, row);
    
    switch(row.tipo_vendita) {
        case "Metro Quadrato":
            calculate_square_meters(row);
            break;
        case "Metro Lineare":
            calculate_linear_meters(row);
            break;
        case "Pezzo":
            calculate_pieces(row);
            break;
        default:
            calculate_pieces(row);
    }
    
    frm.refresh_field("items");
}

function calculate_square_meters(row) {
    // Reset campi non utilizzati
    row.larghezza_materiale = 0;
    row.lunghezza = 0;
    row.ml_calcolati = 0;
    row.prezzo_ml = 0;
    
    if (row.base && row.altezza) {
        // Calcola metri quadrati (da cm a m²)
        row.mq_calcolati = (row.base * row.altezza) / 10000;
        
        if (row.prezzo_mq && row.prezzo_mq > 0) {
            row.rate = row.mq_calcolati * row.prezzo_mq;
            row.note_calcolo = `${row.mq_calcolati.toFixed(3)} m² × €${row.prezzo_mq} = €${row.rate.toFixed(2)}`;
        } else {
            row.rate = 0;
            row.note_calcolo = `${row.mq_calcolati.toFixed(3)} m² (manca prezzo al m²)`;
        }
    } else {
        row.mq_calcolati = 0;
        row.rate = 0;
        row.note_calcolo = "Inserire base e altezza";
    }
}

function calculate_linear_meters(row) {
    // Reset campi non utilizzati
    row.base = 0;
    row.altezza = 0;
    row.mq_calcolati = 0;
    row.prezzo_mq = 0;
    
    if (row.lunghezza) {
        // Calcola metri lineari (da cm a m)
        row.ml_calcolati = row.lunghezza / 100;
        
        if (row.prezzo_ml && row.prezzo_ml > 0) {
            row.rate = row.ml_calcolati * row.prezzo_ml;
            
            let note = `${row.ml_calcolati.toFixed(2)} ml × €${row.prezzo_ml}`;
            if (row.larghezza_materiale) {
                note += ` (largh. ${row.larghezza_materiale}cm)`;
            }
            note += ` = €${row.rate.toFixed(2)}`;
            row.note_calcolo = note;
        } else {
            row.rate = 0;
            row.note_calcolo = `${row.ml_calcolati.toFixed(2)} ml (manca prezzo al ml)`;
        }
    } else {
        row.ml_calcolati = 0;
        row.rate = 0;
        row.note_calcolo = "Inserire lunghezza";
    }
}

function calculate_pieces(row) {
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

// Funzione di utilità per debug
function debug_row(row) {
    console.log("=== DEBUG ROW ===");
    console.log("Tipo vendita:", row.tipo_vendita);
    console.log("Base:", row.base, "Altezza:", row.altezza, "MQ:", row.mq_calcolati);
    console.log("Lunghezza:", row.lunghezza, "Largh. materiale:", row.larghezza_materiale, "ML:", row.ml_calcolati);
    console.log("Prezzi - MQ:", row.prezzo_mq, "ML:", row.prezzo_ml, "Rate:", row.rate);
    console.log("Note:", row.note_calcolo);
    console.log("================");
}