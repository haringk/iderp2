// Estensione form Fattura di Vendita per iDERP
// Gestisce fatturazione articoli a metratura

frappe.ui.form.on("Sales Invoice", {
    setup: function(frm) {
        // Setup griglia articoli
        iderp.setup_item_grid(frm, "items");
        
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
        if (frm.doc.docstatus === 0) {
            // Pulsanti importazione
            frm.add_custom_button(__("Ordine di Vendita"), function() {
                iderp.get_items_from_sales_order(frm);
            }, __("Ottieni Articoli Da"));
            
            frm.add_custom_button(__("Documento di Trasporto"), function() {
                iderp.get_items_from_delivery_note(frm);
            }, __("Ottieni Articoli Da"));
            
            // Strumenti
            frm.add_custom_button(__("Calcola Metrature"), function() {
                iderp.recalculate_all_metrics(frm);
            }, __("Strumenti"));
            
            frm.add_custom_button(__("Applica Ritenuta"), function() {
                iderp.apply_withholding_tax(frm);
            }, __("Strumenti"));
        }
        
        // Mostra riepilogo per fatture confermate
        if (frm.doc.docstatus === 1) {
            iderp.show_invoice_summary(frm);
        }
        
        // Riepilogo metrature
        if (frm.doc.items && frm.doc.items.length > 0) {
            iderp.show_metrics_summary(frm);
        }
    },
    
    customer: function(frm) {
        // Imposta dati fiscali cliente
        if (frm.doc.customer) {
            iderp.set_customer_tax_info(frm);
            
            // Riapplica prezzi
            frm.doc.items.forEach(function(item) {
                if (item.item_code) {
                    iderp.apply_customer_group_pricing(frm, item.doctype, item.name);
                }
            });
        }
    },
    
    is_return: function(frm) {
        // Gestione note credito
        if (frm.doc.is_return) {
            frm.set_value("naming_series", frappe.meta.get_docfield("Sales Invoice", "naming_series").default.replace("SINV-", "CN-"));
        }
    },
    
    validate: function(frm) {
        // Validazioni fattura
        return Promise.all([
            iderp.validate_tax_info(frm),
            iderp.validate_invoice_items(frm)
        ]);
    }
});

// Estendi iDERP per fatturazione
frappe.provide("iderp");

// Importa da Ordine di Vendita
iderp.get_items_from_sales_order = function(frm) {
    erpnext.utils.map_current_doc({
        method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
        source_doctype: "Sales Order",
        target: frm,
        setters: {
            customer: frm.doc.customer || undefined,
            delivery_status: ["!=", "Fully Delivered"]
        },
        get_query_filters: {
            docstatus: 1,
            status: ["not in", ["Closed", "On Hold"]],
            billing_status: ["!=", "Fully Billed"],
            company: frm.doc.company
        }
    });
};

// Importa da Documento di Trasporto
iderp.get_items_from_delivery_note = function(frm) {
    erpnext.utils.map_current_doc({
        method: "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice",
        source_doctype: "Delivery Note",
        target: frm,
        date_field: "posting_date",
        setters: {
            customer: frm.doc.customer || undefined,
            posting_date: undefined
        },
        get_query_filters: {
            docstatus: 1,
            status: ["not in", ["Closed", "Return"]],
            billing_status: ["!=", "Fully Billed"],
            company: frm.doc.company,
            is_return: 0
        }
    });
};

// Imposta dati fiscali cliente
iderp.set_customer_tax_info = function(frm) {
    if (!frm.doc.customer) return;
    
    frappe.call({
        method: "frappe.client.get",
        args: {
            doctype: "Customer",
            name: frm.doc.customer
        },
        callback: function(r) {
            if (r.message) {
                const customer = r.message;
                
                // Imposta dati fiscali
                if (customer.tax_id && !frm.doc.tax_id) {
                    frm.set_value("tax_id", customer.tax_id);
                }
                
                if (customer.customer_type === "Individual") {
                    // Codice fiscale per persone fisiche
                    if (customer.fiscal_code && !frm.doc.fiscal_code) {
                        frm.set_value("fiscal_code", customer.fiscal_code);
                    }
                }
                
                // Template tasse predefinito
                if (customer.default_sales_taxes_template && !frm.doc.taxes_and_charges) {
                    frm.set_value("taxes_and_charges", customer.default_sales_taxes_template);
                }
            }
        }
    });
};

// Applica ritenuta d'acconto
iderp.apply_withholding_tax = function(frm) {
    frappe.prompt([
        {
            label: __("Tipo Ritenuta"),
            fieldname: "withholding_type",
            fieldtype: "Select",
            options: [
                "Ritenuta 20% Professionisti",
                "Ritenuta 23% Agenti",
                "Ritenuta 4% Condomini",
                "Altra Ritenuta"
            ],
            reqd: 1
        },
        {
            label: __("Percentuale"),
            fieldname: "percentage",
            fieldtype: "Percent",
            default: 20,
            depends_on: "eval:doc.withholding_type=='Altra Ritenuta'"
        }
    ], function(values) {
        let percentage = values.percentage;
        
        // Determina percentuale in base al tipo
        switch(values.withholding_type) {
            case "Ritenuta 20% Professionisti":
                percentage = 20;
                break;
            case "Ritenuta 23% Agenti":
                percentage = 23;
                break;
            case "Ritenuta 4% Condomini":
                percentage = 4;
                break;
        }
        
        // Calcola ritenuta su imponibile
        const taxable_amount = frm.doc.net_total || 0;
        const withholding_amount = (taxable_amount * percentage) / 100;
        
        // Aggiungi riga tasse negativa
        const tax_row = frm.add_child("taxes");
        tax_row.charge_type = "Actual";
        tax_row.description = values.withholding_type;
        tax_row.tax_amount = -withholding_amount;
        tax_row.rate = 0;
        
        frm.refresh_field("taxes");
        frm.trigger("calculate_taxes_and_totals");
        
        frappe.show_alert({
            message: __("Applicata ritenuta del {0}%", [percentage]),
            indicator: "green"
        });
        
    }, __("Applica Ritenuta d'Acconto"));
};

// Valida dati fiscali
iderp.validate_tax_info = function(frm) {
    // Validazione partita IVA italiana
    if (frm.doc.tax_id && frm.doc.territory === "Italy") {
        const vat_regex = /^IT\d{11}$/;
        if (!vat_regex.test(frm.doc.tax_id)) {
            frappe.msgprint({
                title: __("Partita IVA Non Valida"),
                message: __("La partita IVA italiana deve essere nel formato IT seguito da 11 cifre"),
                indicator: "red"
            });
            return false;
        }
    }
    
    // Validazione codice fiscale
    if (frm.doc.fiscal_code) {
        const cf_regex = /^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$/i;
        if (!cf_regex.test(frm.doc.fiscal_code)) {
            frappe.msgprint({
                title: __("Codice Fiscale Non Valido"),
                message: __("Il codice fiscale non è nel formato corretto"),
                indicator: "orange"
            });
        }
    }
    
    return true;
};

// Valida articoli fattura
iderp.validate_invoice_items = function(frm) {
    let has_errors = false;
    
    // Controlla che ci siano articoli
    if (!frm.doc.items || frm.doc.items.length === 0) {
        frappe.msgprint(__("Aggiungere almeno un articolo alla fattura"));
        return false;
    }
    
    // Valida ogni riga
    frm.doc.items.forEach(function(item) {
        // Controllo prezzi zero
        if (item.rate === 0 && !item.is_free_item) {
            frappe.msgprint({
                title: __("Prezzo Zero"),
                message: __("Riga {0}: {1} ha prezzo zero. Contrassegnare come omaggio se intenzionale", 
                    [item.idx, item.item_name]),
                indicator: "orange"
            });
        }
        
        // Controllo account ricavi
        if (!item.income_account) {
            frappe.msgprint({
                title: __("Conto Ricavi Mancante"),
                message: __("Riga {0}: Specificare il conto ricavi", [item.idx]),
                indicator: "red"
            });
            has_errors = true;
        }
    });
    
    return !has_errors;
};

// Mostra riepilogo fattura
iderp.show_invoice_summary = function(frm) {
    const summary = {
        total_items: frm.doc.items.length,
        total_mq: 0,
        total_weight: 0,
        payment_status: frm.doc.outstanding_amount > 0 ? __("Non Pagata") : __("Pagata")
    };
    
    // Calcola totali
    frm.doc.items.forEach(function(item) {
        if (item.uom === "Mq" && item.mq_totali) {
            summary.total_mq += item.mq_totali;
        }
        if (item.total_weight) {
            summary.total_weight += item.total_weight;
        }
    });
    
    // Crea HTML riepilogo
    let html = `
        <div class="invoice-summary" style="margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 5px;">
            <h5>${__("Riepilogo Fattura")}</h5>
            <div class="row">
                <div class="col-sm-3">
                    <strong>${__("Articoli")}:</strong> ${summary.total_items}
                </div>
                <div class="col-sm-3">
                    <strong>${__("Totale Mq")}:</strong> ${summary.total_mq.toFixed(2)} m²
                </div>
                <div class="col-sm-3">
                    <strong>${__("Stato Pagamento")}:</strong> ${summary.payment_status}
                </div>
                <div class="col-sm-3">
                    <strong>${__("Scadenza")}:</strong> ${frm.doc.due_date || "-"}
                </div>
            </div>
        </div>
    `;
    
    $(frm.fields_dict.items.wrapper).before(html);
};