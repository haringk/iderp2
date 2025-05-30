console.log("IDERP: JS LOADED");

frappe.ui.form.on('Quotation Item', {
    base: function(frm, cdt, cdn) { 
        calculate_mq(frm, cdt, cdn); 
    },
    altezza: function(frm, cdt, cdn) { 
        calculate_mq(frm, cdt, cdn); 
    },
    prezzo_mq: function(frm, cdt, cdn) { 
        calculate_mq(frm, cdt, cdn); 
    },
    refresh: function(frm) {
        $.each(frm.doc.items || [], function(i, row) {
            calculate_mq(frm, row.doctype, row.name);
        });
    }
});

function calculate_mq(frm, cdt, cdn) {
    var row = locals[cdt][cdn];
    
    console.log("Valori della riga:", row);
    
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
}
