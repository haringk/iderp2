/*
		'Quotation Item',
		'Sales Order Item', 
		'Sales Invoice Item', 
		'Delivery Note Item', 
		'Work Order Item', 
		'Web Order Item'], 
*/


frappe.ui.form.on('Quotation Item', {
	
    base: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    altezza: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    prezzo_mq: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },

    // Esegui anche al refresh (quando carica)
    refresh: function(frm) {
        $.each(frm.doc.items || frm.doc.quotation_items || [], function(i, row) {
            calculate_mq(frm, row.doctype, row.name);
        });
    }
});

frappe.ui.form.on('Sales Order Item', {
	
    base: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    altezza: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    prezzo_mq: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },

    // Esegui anche al refresh (quando carica)
    refresh: function(frm) {
        $.each(frm.doc.items || frm.doc.quotation_items || [], function(i, row) {
            calculate_mq(frm, row.doctype, row.name);
        });
    }
});

frappe.ui.form.on('Sales Invoice Item', {
	
    base: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    altezza: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    prezzo_mq: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },

    // Esegui anche al refresh (quando carica)
    refresh: function(frm) {
        $.each(frm.doc.items || frm.doc.quotation_items || [], function(i, row) {
            calculate_mq(frm, row.doctype, row.name);
        });
    }
});

frappe.ui.form.on('Delivery Note Item', {
	
    base: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    altezza: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    prezzo_mq: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },

    // Esegui anche al refresh (quando carica)
    refresh: function(frm) {
        $.each(frm.doc.items || frm.doc.quotation_items || [], function(i, row) {
            calculate_mq(frm, row.doctype, row.name);
        });
    }
});

frappe.ui.form.on('Work Order Item', {
	
    base: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    altezza: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    prezzo_mq: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },

    // Esegui anche al refresh (quando carica)
    refresh: function(frm) {
        $.each(frm.doc.items || frm.doc.quotation_items || [], function(i, row) {
            calculate_mq(frm, row.doctype, row.name);
        });
    }
});

frappe.ui.form.on('Web Order Item', {
	
    base: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    altezza: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },
    prezzo_mq: function(frm, cdt, cdn) { calculate_mq(frm, cdt, cdn); },

    // Esegui anche al refresh (quando carica)
    refresh: function(frm) {
        $.each(frm.doc.items || frm.doc.quotation_items || [], function(i, row) {
            calculate_mq(frm, row.doctype, row.name);
        });
    }
});

function calculate_mq(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    // Attiva i log
	console.log("Valori della riga:", row);
	console.log("MQ Calcolati:", row.mq_calcolati);
	console.log("Prezzo riga:", row.rate);
    
    // Esegui il calcolo solo se i campi esistono
    if (row.base && row.altezza) {
        row.mq_calcolati = (row.base * row.altezza) / 10000;
        if (row.prezzo_mq) {
            row.rate = row.mq_calcolati * row.prezzo_mq;
        }
    } else {
        row.mq_calcolati = 0;
        if (row.prezzo_mq) {
            row.rate = 0;
        }
    }
    frm.refresh_field("items");
	frm.refresh_field("importo_mq", cdn);
	frm.refresh_field("totale_mq", cdn);
}



/* 

[
    'Quotation Item',
    'Sales Order Item',
    'Sales Invoice Item',
    'Delivery Note Item',
    'Work Order Item',
    'Web Order Item'
].forEach(function(dt) {
    frappe.ui.form.on(dt, {
        base: function(frm, cdt, cdn) {
            calculate_importo(frm, cdt, cdn);
        },
        altezza: function(frm, cdt, cdn) {
            calculate_importo(frm, cdt, cdn);
        },
        prezzo_mq: function(frm, cdt, cdn) {
            calculate_importo(frm, cdt, cdn);
        }
    });
});

function calculate_importo(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    if(row.base && row.altezza && row.prezzo_mq) {
        row.totale_mq = (row.base * row.altezza / 10000).toFixed(3); // se misuri in cm
        row.importo_mq = (row.totale_mq * row.prezzo_mq).toFixed(2);
    } else {
        row.totale_mq = 0;
        row.importo_mq = 0;
    }
    frm.refresh_field("totale_mq", cdn);
    frm.refresh_field("importo_mq", cdn);
}

*/