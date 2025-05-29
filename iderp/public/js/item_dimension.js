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
