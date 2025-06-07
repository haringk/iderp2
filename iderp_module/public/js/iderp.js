// iDERP - Gestione articoli a metratura
// Compatibile con ERPNext 15

frappe.provide("iderp");

iderp = {
    // Costanti per unità di misura
    UNITS: {
        SQUARE_METER: "Mq",
        EACH: "Nos", 
        LINEAR_METER: "Metro"
    },

    // Inizializzazione modulo
    init: function() {
        console.log("iDERP: Inizializzazione modulo metratura");
        
        // Registra eventi per i DocType di vendita
        this.register_events();
    },

    // Registra eventi per tutti i DocType supportati
    register_events: function() {
        const doctypes = [
            "Quotation Item",
            "Sales Order Item", 
            "Delivery Note Item",
            "Sales Invoice Item",
            "Purchase Order Item",
            "Purchase Receipt Item",
            "Purchase Invoice Item"
        ];

        doctypes.forEach(doctype => {
            frappe.ui.form.on(doctype, {
                item_code: function(frm, cdt, cdn) {
                    iderp.fetch_item_details(frm, cdt, cdn);
                },
                base: function(frm, cdt, cdn) {
                    iderp.calculate_metrics(frm, cdt, cdn);
                },
                altezza: function(frm, cdt, cdn) {
                    iderp.calculate_metrics(frm, cdt, cdn);
                },
                qty: function(frm, cdt, cdn) {
                    iderp.calculate_metrics(frm, cdt, cdn);
                },
                uom: function(frm, cdt, cdn) {
                    iderp.handle_uom_change(frm, cdt, cdn);
                },
                rate: function(frm, cdt, cdn) {
                    iderp.calculate_amount(frm, cdt, cdn);
                }
            });
        });
    },

    // Recupera dettagli articolo
    fetch_item_details: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_code) return;

        frappe.call({
            method: "iderp.api.item.get_item_details",
            args: {
                item_code: row.item_code,
                customer: frm.doc.customer || frm.doc.party_name,
                company: frm.doc.company
            },
            callback: function(r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, {
                        item_name: r.message.item_name,
                        description: r.message.description,
                        uom: r.message.uom || r.message.stock_uom,
                        conversion_factor: r.message.conversion_factor || 1,
                        base: r.message.base || 0,
                        altezza: r.message.altezza || 0,
                        rate: r.message.rate || 0
                    });
                    
                    // Calcola metriche se necessario
                    if (r.message.uom === iderp.UNITS.SQUARE_METER) {
                        iderp.calculate_metrics(frm, cdt, cdn);
                    }
                }
            }
        });
    },

    // Gestisce cambio unità di misura
    handle_uom_change: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        
        if (row.uom === iderp.UNITS.SQUARE_METER) {
            // Mostra campi base e altezza
            this.toggle_dimension_fields(frm, cdt, cdn, true);
            this.calculate_metrics(frm, cdt, cdn);
        } else {
            // Nascondi campi base e altezza
            this.toggle_dimension_fields(frm, cdt, cdn, false);
            frappe.model.set_value(cdt, cdn, {
                base: 0,
                altezza: 0,
                mq_totali: 0
            });
        }
    },

    // Mostra/nasconde campi dimensioni
    toggle_dimension_fields: function(frm, cdt, cdn, show) {
        const grid = frm.fields_dict[cdt.toLowerCase().replace(" ", "_")].grid;
        
        if (grid) {
            grid.toggle_display("base", show);
            grid.toggle_display("altezza", show);
            grid.toggle_display("mq_totali", show);
        }
    },

    // Calcola metriche (mq totali)
    calculate_metrics: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        
        if (row.uom === iderp.UNITS.SQUARE_METER && row.base && row.altezza) {
            // Converti da mm a metri e calcola mq
            const base_m = row.base / 1000;
            const altezza_m = row.altezza / 1000;
            const mq_unitari = base_m * altezza_m;
            const mq_totali = mq_unitari * (row.qty || 1);
            
            frappe.model.set_value(cdt, cdn, {
                mq_totali: flt(mq_totali, precision("mq_totali", row)),
                qty: flt(mq_totali, precision("qty", row)) // Qty = mq totali per articoli a mq
            });
            
            // Ricalcola importo
            this.calculate_amount(frm, cdt, cdn);
        }
    },

    // Calcola importo riga
    calculate_amount: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        let amount = 0;
        
        if (row.rate && row.qty) {
            amount = flt(row.rate) * flt(row.qty);
            
            // Applica sconto se presente
            if (row.discount_percentage) {
                amount = amount * (1 - row.discount_percentage / 100);
            }
            
            frappe.model.set_value(cdt, cdn, "amount", amount);
        }
        
        // Aggiorna totali documento
        this.update_totals(frm);
    },

    // Aggiorna totali documento
    update_totals: function(frm) {
        let total = 0;
        let total_qty = 0;
        let total_mq = 0;
        
        const items_field = frm.doc.items || frm.doc.quotation_items || frm.doc.sales_order_items;
        
        if (items_field) {
            items_field.forEach(item => {
                total += flt(item.amount);
                total_qty += flt(item.qty);
                if (item.uom === iderp.UNITS.SQUARE_METER) {
                    total_mq += flt(item.mq_totali);
                }
            });
        }
        
        frm.set_value({
            total: total,
            total_qty: total_qty,
            total_mq: total_mq
        });
    },

    // Applica regole prezzo per gruppo cliente
    apply_customer_group_pricing: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.item_code || !frm.doc.customer) return;
        
        frappe.call({
            method: "iderp.pricing.get_customer_group_price",
            args: {
                item_code: row.item_code,
                customer: frm.doc.customer,
                qty: row.qty || 1,
                transaction_date: frm.doc.transaction_date || frappe.datetime.nowdate()
            },
            callback: function(r) {
                if (r.message && r.message.price) {
                    frappe.model.set_value(cdt, cdn, "rate", r.message.price);
                    
                    // Mostra info sconto applicato
                    if (r.message.rule_name) {
                        frappe.show_alert({
                            message: __("Applicata regola prezzo: {0}", [r.message.rule_name]),
                            indicator: "green"
                        });
                    }
                }
            }
        });
    },

    // Valida quantità minime per gruppo cliente
    validate_minimum_qty: function(frm) {
        if (!frm.doc.customer) return;
        
        return frappe.call({
            method: "iderp.global_minimums.validate_order_minimums",
            args: {
                customer: frm.doc.customer,
                items: frm.doc.items || frm.doc.quotation_items || frm.doc.sales_order_items,
                total: frm.doc.total || frm.doc.grand_total
            },
            callback: function(r) {
                if (r.message && !r.message.valid) {
                    frappe.msgprint({
                        title: __("Ordine minimo non raggiunto"),
                        message: r.message.message,
                        indicator: "red"
                    });
                    return false;
                }
                return true;
            }
        });
    },

    // Helper per formattazione numeri
    format_currency: function(value, currency) {
        return format_currency(value, currency || frappe.defaults.get_default("currency"));
    },

    // Helper per formattazione metri quadri
    format_square_meters: function(value) {
        return flt(value, 2) + " m²";
    }
};

// Inizializza quando DOM è pronto
$(document).ready(function() {
    if (frappe.ui.form) {
        iderp.init();
    }
});

// Esporta per uso globale
window.iderp = iderp;
