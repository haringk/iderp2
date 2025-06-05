// Estensione form Ordine di Vendita per iDERP
// Eredita funzionalità dal Preventivo con aggiunte specifiche

frappe.ui.form.on("Sales Order", {
    setup: function(frm) {
        // Riusa setup del preventivo
        iderp.setup_item_grid(frm, "items");
        
        frm.set_query("item_code", "items", function(doc, cdt, cdn) {
            return {
                filters: {
                    "is_sales_item": 1,
                    "disabled": 0,
                    "has_variants": 0
                }
            };
        });
    },
    
    refresh: function(frm) {
        // Pulsanti personalizzati per stato bozza
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__("Importa da Preventivo"), function() {
                iderp.import_from_quotation(frm);
            }, __("Ottieni Articoli Da"));
            
            frm.add_custom_button(__("Calcola Metrature"), function() {
                iderp.recalculate_all_metrics(frm);
            }, __("Strumenti"));
        }
        
        // Per ordini confermati
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Stato Produzione"), function() {
                iderp.show_production_status(frm);
            }, __("Visualizza"));
        }
        
        // Mostra riepilogo
        if (frm.doc.items && frm.doc.items.length > 0) {
            iderp.show_metrics_summary(frm);
            
            // Mostra avvisi per articoli con dimensioni speciali
            iderp.check_special_dimensions(frm);
        }
    },
    
    customer: function(frm) {
        // Riapplica prezzi quando cambia cliente
        if (frm.doc.customer && frm.doc.items) {
            frm.doc.items.forEach(function(item) {
                if (item.item_code) {
                    iderp.apply_customer_group_pricing(frm, item.doctype, item.name);
                }
            });
        }
        
        // Controlla termini di pagamento predefiniti
        iderp.set_default_payment_terms(frm);
    },
    
    delivery_date: function(frm) {
        // Propaga data consegna a tutte le righe
        if (frm.doc.delivery_date && frm.doc.items) {
            frm.doc.items.forEach(function(item) {
                frappe.model.set_value(
                    item.doctype,
                    item.name,
                    "delivery_date",
                    frm.doc.delivery_date
                );
            });
        }
    },
    
    validate: function(frm) {
        // Validazioni aggiuntive per ordini
        return Promise.all([
            iderp.validate_minimum_qty(frm),
            iderp.validate_delivery_dates(frm),
            iderp.validate_warehouse_stock(frm)
        ]);
    }
});

// Estendi iDERP con funzioni specifiche per Sales Order
frappe.provide("iderp");

// Importa articoli da preventivo
iderp.import_from_quotation = function(frm) {
    frappe.prompt({
        label: __("Preventivo"),
        fieldname: "quotation",
        fieldtype: "Link",
        options: "Quotation",
        reqd: 1,
        get_query: function() {
            return {
                filters: {
                    "customer": frm.doc.customer,
                    "docstatus": 1,
                    "status": ["!=", "Lost"]
                }
            };
        }
    }, function(values) {
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Quotation",
                name: values.quotation
            },
            callback: function(r) {
                if (r.message) {
                    const quotation = r.message;
                    
                    // Svuota articoli esistenti
                    frm.clear_table("items");
                    
                    // Importa articoli con metrature
                    quotation.items.forEach(function(item) {
                        const new_item = frm.add_child("items");
                        
                        // Copia tutti i campi rilevanti
                        const fields_to_copy = [
                            "item_code", "item_name", "description",
                            "qty", "uom", "conversion_factor",
                            "rate", "amount", "base", "altezza",
                            "mq_totali", "warehouse"
                        ];
                        
                        fields_to_copy.forEach(field => {
                            if (item[field] !== undefined) {
                                new_item[field] = item[field];
                            }
                        });
                        
                        // Imposta data consegna
                        new_item.delivery_date = frm.doc.delivery_date;
                    });
                    
                    frm.refresh_field("items");
                    
                    // Copia anche eventuali opzionali
                    if (quotation.sales_item_optionals) {
                        frm.clear_table("sales_item_optionals");
                        
                        quotation.sales_item_optionals.forEach(function(opt) {
                            const new_opt = frm.add_child("sales_item_optionals");
                            Object.assign(new_opt, opt);
                        });
                        
                        frm.refresh_field("sales_item_optionals");
                    }
                    
                    frappe.show_alert({
                        message: __("Importati {0} articoli dal preventivo", [quotation.items.length]),
                        indicator: "green"
                    });
                }
            }
        });
    }, __("Seleziona Preventivo"));
};

// Controlla dimensioni speciali
iderp.check_special_dimensions = function(frm) {
    const warnings = [];
    
    frm.doc.items.forEach(function(item, idx) {
        if (item.uom === "Mq" && (item.base > 3000 || item.altezza > 3000)) {
            warnings.push(__("Riga {0}: {1} ha dimensioni superiori a 3 metri", [idx + 1, item.item_name]));
        }
    });
    
    if (warnings.length > 0) {
        frappe.msgprint({
            title: __("Attenzione: Dimensioni Speciali"),
            message: warnings.join("<br>"),
            indicator: "orange"
        });
    }
};

// Imposta termini pagamento predefiniti
iderp.set_default_payment_terms = function(frm) {
    if (!frm.doc.payment_terms_template && frm.doc.customer) {
        frappe.db.get_value(
            "Customer",
            frm.doc.customer,
            "payment_terms",
            function(r) {
                if (r && r.payment_terms) {
                    frm.set_value("payment_terms_template", r.payment_terms);
                }
            }
        );
    }
};

// Valida date consegna
iderp.validate_delivery_dates = function(frm) {
    const today = frappe.datetime.get_today();
    let has_errors = false;
    
    frm.doc.items.forEach(function(item) {
        if (item.delivery_date && item.delivery_date < today) {
            frappe.msgprint({
                title: __("Data Consegna Non Valida"),
                message: __("Riga {0}: La data di consegna non può essere nel passato", [item.idx]),
                indicator: "red"
            });
            has_errors = true;
        }
    });
    
    return !has_errors;
};

// Valida disponibilità magazzino
iderp.validate_warehouse_stock = function(frm) {
    // Controllo opzionale stock per articoli a magazzino
    const promises = [];
    
    frm.doc.items.forEach(function(item) {
        if (item.warehouse && item.item_code && !item.is_free_item) {
            promises.push(
                frappe.call({
                    method: "erpnext.stock.utils.get_latest_stock_qty",
                    args: {
                        item_code: item.item_code,
                        warehouse: item.warehouse
                    }
                })
            );
        }
    });
    
    return Promise.all(promises).then(results => {
        let warnings = [];
        
        results.forEach((result, idx) => {
            if (result.message !== undefined) {
                const item = frm.doc.items[idx];
                const available = result.message || 0;
                
                if (available < item.qty) {
                    warnings.push(
                        __("{0}: Disponibili solo {1} {2} in {3}", 
                        [item.item_name, available, item.uom, item.warehouse])
                    );
                }
            }
        });
        
        if (warnings.length > 0) {
            frappe.confirm(
                __("Attenzione disponibilità:<br>") + warnings.join("<br>") + 
                __("<br><br>Procedere comunque?"),
                () => true,
                () => false
            );
        }
        
        return true;
    });
};

// Mostra stato produzione
iderp.show_production_status = function(frm) {
    frappe.call({
        method: "iderp.api.production.get_order_production_status",
        args: {
            sales_order: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                const dialog = new frappe.ui.Dialog({
                    title: __("Stato Produzione Ordine"),
                    size: "large"
                });
                
                const html = iderp.render_production_status(r.message);
                dialog.$body.html(html);
                dialog.show();
            }
        }
    });
};