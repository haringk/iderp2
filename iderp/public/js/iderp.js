frappe.ui.form.on('Quotation Item', {
    base: function(frm, cdt, cdn) {
        calcola_prezzo(frm, cdt, cdn);
    },
    altezza: function(frm, cdt, cdn) {
        calcola_prezzo(frm, cdt, cdn);
    }
});
frappe.ui.form.on('Sales Order Item', {
    base: function(frm, cdt, cdn) {
        calcola_prezzo(frm, cdt, cdn);
    },
    altezza: function(frm, cdt, cdn) {
        calcola_prezzo(frm, cdt, cdn);
    }
});
function calcola_prezzo(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if(row.base && row.altezza && row.rate) {
        let mq = (row.base * row.altezza) / 10000; // misure in cm
        let amount = mq * row.rate;
        frappe.model.set_value(cdt, cdn, "amount", amount);
    }
}
