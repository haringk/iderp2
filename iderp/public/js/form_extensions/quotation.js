// Estensione form Preventivo per iDERP
// Aggiunge funzionalità specifiche per articoli a metratura

frappe.ui.form.on("Quotation", {
    setup: function(frm) {
        // Aggiungi campi personalizzati alla griglia se non esistono
        iderp.setup_item_grid(frm, "items");
        
        // Imposta query filtrate
        frm.set_query("item_code", "items", function(doc, cdt, cdn) {
            return {
                filters: {
                    "is_sales_item": 1,
                    "disabled": 0
                }
            };
        });
    },
    
    refresh: function(frm) {
        // Aggiungi pulsanti personalizzati
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__("Calcola Metrature"), function() {
                iderp.recalculate_all_metrics(frm);
            }, __("Strumenti"));
            
            frm.add_custom_button(__("Applica Sconti Gruppo"), function() {
                iderp.apply_group_discounts(frm);
            }, __("Strumenti"));
        }
        
        // Mostra riepilogo metrature
        if (frm.doc.items && frm.doc.items.length > 0) {
            iderp.show_metrics_summary(frm);
        }
    },
    
    customer: function(frm) {
        // Quando cambia il cliente, riapplica prezzi gruppo
        if (frm.doc.customer && frm.doc.items) {
            frm.doc.items.forEach(function(item) {
                if (item.item_code) {
                    iderp.apply_customer_group_pricing(frm, item.doctype, item.name);
                }
            });
        }
    },
    
    validate: function(frm) {
        // Valida quantità minime
        return iderp.validate_minimum_qty(frm);
    },
    
    before_submit: function(frm) {
        // Validazione finale prima dell'invio
        return new Promise((resolve, reject) => {
            // Controlla dimensioni articoli
            let has_errors = false;
            let promises = [];
            
            frm.doc.items.forEach(function(item) {
                if (item.uom === "Mq" && (item.base || item.altezza)) {
                    promises.push(
                        frappe.call({
                            method: "iderp.api.item.validate_item_dimensions",
                            args: {
                                item_code: item.item_code,
                                base_mm: item.base,
                                altezza_mm: item.altezza
                            }
                        })
                    );
                }
            });
            
            Promise.all(promises).then(results => {
                results.forEach(r => {
                    if (r.message && !r.message.valid) {
                        frappe.msgprint({
                            title: __("Errore Validazione"),
                            message: r.message.message,
                            indicator: "red"
                        });
                        has_errors = true;
                    }
                });
                
                if (has_errors) {
                    reject("Correggere gli errori prima di procedere");
                } else {
                    resolve();
                }
            });
        });
    }
});

// Estendi funzionalità iDERP
frappe.provide("iderp");

// Configura griglia articoli con campi personalizzati
iderp.setup_item_grid = function(frm, items_field) {
    const grid = frm.fields_dict[items_field].grid;
    
    // Aggiungi campi se non esistono già
    if (!grid.fields_map.base) {
        grid.add_field({
            fieldtype: "Float",
            fieldname: "base",
            label: __("Base (mm)"),
            insert_after: "qty",
            print_hide: 0,
            hidden: 0
        });
    }
    
    if (!grid.fields_map.altezza) {
        grid.add_field({
            fieldtype: "Float", 
            fieldname: "altezza",
            label: __("Altezza (mm)"),
            insert_after: "base",
            print_hide: 0,
            hidden: 0
        });
    }
    
    if (!grid.fields_map.mq_totali) {
        grid.add_field({
            fieldtype: "Float",
            fieldname: "mq_totali",
            label: __("Mq Totali"),
            insert_after: "altezza",
            print_hide: 0,
            read_only: 1,
            hidden: 0
        });
    }
};

// Ricalcola tutte le metrature
iderp.recalculate_all_metrics = function(frm) {
    let recalculated = 0;
    
    frm.doc.items.forEach(function(item) {
        if (item.uom === "Mq" && item.base && item.altezza) {
            iderp.calculate_metrics(frm, item.doctype, item.name);
            recalculated++;
        }
    });
    
    if (recalculated > 0) {
        frappe.show_alert({
            message: __("Ricalcolate metrature per {0} righe", [recalculated]),
            indicator: "green"
        });
    }
};

// Applica sconti gruppo cliente
iderp.apply_group_discounts = function(frm) {
    if (!frm.doc.customer) {
        frappe.msgprint(__("Selezionare prima un cliente"));
        return;
    }
    
    frappe.call({
        method: "iderp.pricing.apply_customer_group_discounts",
        args: {
            customer: frm.doc.customer,
            items: frm.doc.items,
            posting_date: frm.doc.transaction_date
        },
        callback: function(r) {
            if (r.message) {
                // Aggiorna prezzi
                r.message.forEach(function(updated_item) {
                    const item = frm.doc.items.find(i => i.name === updated_item.name);
                    if (item) {
                        frappe.model.set_value(
                            item.doctype,
                            item.name,
                            "rate",
                            updated_item.rate
                        );
                        
                        if (updated_item.discount_percentage) {
                            frappe.model.set_value(
                                item.doctype,
                                item.name,
                                "discount_percentage",
                                updated_item.discount_percentage
                            );
                        }
                    }
                });
                
                frappe.show_alert({
                    message: __("Applicati sconti gruppo cliente"),
                    indicator: "green"
                });
            }
        }
    });
};

// Mostra riepilogo metrature
iderp.show_metrics_summary = function(frm) {
    let total_mq = 0;
    let total_metri = 0;
    let items_mq = 0;
    let items_metri = 0;
    
    frm.doc.items.forEach(function(item) {
        if (item.uom === "Mq" && item.mq_totali) {
            total_mq += item.mq_totali;
            items_mq++;
        } else if (item.uom === "Metro" && item.qty) {
            total_metri += item.qty;
            items_metri++;
        }
    });
    
    let summary_html = `
        <div class="iderp-metrics-summary" style="margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px;">
            <h5>${__("Riepilogo Metrature")}</h5>
    `;
    
    if (items_mq > 0) {
        summary_html += `<p><strong>${__("Totale Mq")}:</strong> ${iderp.format_square_meters(total_mq)} (${items_mq} ${__("articoli")})</p>`;
    }
    
    if (items_metri > 0) {
        summary_html += `<p><strong>${__("Totale Metri")}:</strong> ${total_metri.toFixed(2)} m (${items_metri} ${__("articoli")})</p>`;
    }
    
    summary_html += "</div>";
    
    // Aggiungi riepilogo sopra la tabella articoli
    $(frm.fields_dict.items.wrapper).prepend(summary_html);
};