// Estensione form Documento di Trasporto per iDERP
// Gestisce DDT con articoli a metratura

frappe.ui.form.on("Delivery Note", {
    setup: function(frm) {
        // Setup griglia articoli
        iderp.setup_item_grid(frm, "items");
        
        frm.set_query("item_code", "items", function(doc, cdt, cdn) {
            return {
                filters: {
                    "is_stock_item": 1,
                    "disabled": 0,
                    "has_variants": 0
                }
            };
        });
        
        // Query per trasportatore
        frm.set_query("transporter", function() {
            return {
                filters: {
                    "is_transporter": 1
                }
            };
        });
    },
    
    refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            // Importa da ordine
            frm.add_custom_button(__("Ordine di Vendita"), function() {
                iderp.get_items_from_sales_order_for_dn(frm);
            }, __("Ottieni Articoli Da"));
            
            // Strumenti
            frm.add_custom_button(__("Calcola Metrature"), function() {
                iderp.recalculate_all_metrics(frm);
            }, __("Strumenti"));
            
            frm.add_custom_button(__("Calcola Pesi/Volumi"), function() {
                iderp.calculate_shipping_metrics(frm);
            }, __("Strumenti"));
        }
        
        if (frm.doc.docstatus === 1) {
            // Stato consegna
            frm.add_custom_button(__("Tracking Spedizione"), function() {
                iderp.show_shipping_tracking(frm);
            }, __("Visualizza"));
        }
        
        // Mostra info spedizione
        iderp.show_shipping_info(frm);
        
        // Riepilogo metrature
        if (frm.doc.items && frm.doc.items.length > 0) {
            iderp.show_metrics_summary(frm);
        }
    },
    
    customer: function(frm) {
        // Imposta indirizzo spedizione predefinito
        if (frm.doc.customer) {
            iderp.set_default_shipping_address(frm);
        }
    },
    
    transporter: function(frm) {
        // Info trasportatore
        if (frm.doc.transporter) {
            frappe.db.get_value(
                "Supplier",
                frm.doc.transporter,
                ["supplier_name", "mobile_no"],
                function(r) {
                    if (r) {
                        frm.set_value("transporter_name", r.supplier_name);
                        if (r.mobile_no && !frm.doc.driver_mobile) {
                            frm.set_value("driver_mobile", r.mobile_no);
                        }
                    }
                }
            );
        }
    },
    
    validate: function(frm) {
        // Validazioni DDT
        return Promise.all([
            iderp.validate_delivery_items(frm),
            iderp.validate_transport_info(frm)
        ]);
    },
    
    before_submit: function(frm) {
        // Controllo finale pesi e volumi
        return iderp.check_shipping_limits(frm);
    }
});

// Estendi iDERP per DDT
frappe.provide("iderp");

// Importa da ordine per DDT
iderp.get_items_from_sales_order_for_dn = function(frm) {
    erpnext.utils.map_current_doc({
        method: "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
        source_doctype: "Sales Order",
        target: frm,
        setters: {
            customer: frm.doc.customer || undefined
        },
        get_query_filters: {
            docstatus: 1,
            status: ["not in", ["Closed", "On Hold"]],
            delivery_status: ["not in", ["Fully Delivered", "Not Applicable"]],
            company: frm.doc.company
        }
    });
};

// Imposta indirizzo spedizione
iderp.set_default_shipping_address = function(frm) {
    if (!frm.doc.shipping_address_name) {
        frappe.call({
            method: "erpnext.selling.doctype.customer.customer.get_customer_address",
            args: {
                customer: frm.doc.customer,
                address_type: "Shipping Address"
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_value("shipping_address_name", r.message.name);
                    frm.set_value("shipping_address", r.message.display);
                }
            }
        });
    }
};

// Calcola metriche spedizione
iderp.calculate_shipping_metrics = function(frm) {
    let total_weight = 0;
    let total_volume = 0;
    let total_packages = 0;
    
    const promises = frm.doc.items.map(item => {
        if (item.item_code) {
            return frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Item",
                    name: item.item_code,
                    fieldname: ["weight_per_unit", "weight_uom", "volume_per_unit", "volume_uom"]
                }
            });
        }
        return Promise.resolve(null);
    });
    
    Promise.all(promises).then(results => {
        results.forEach((r, idx) => {
            if (r && r.message) {
                const item = frm.doc.items[idx];
                const data = r.message;
                
                // Calcola peso
                if (data.weight_per_unit) {
                    const item_weight = data.weight_per_unit * item.qty;
                    frappe.model.set_value(item.doctype, item.name, "total_weight", item_weight);
                    total_weight += item_weight;
                }
                
                // Calcola volume per articoli a metratura
                if (item.uom === "Mq" && item.base && item.altezza) {
                    // Volume = area * spessore (assumendo spessore standard)
                    const thickness = 0.01; // 10mm di spessore standard
                    const volume = (item.base / 1000) * (item.altezza / 1000) * thickness * item.qty;
                    frappe.model.set_value(item.doctype, item.name, "volume", volume);
                    total_volume += volume;
                } else if (data.volume_per_unit) {
                    const item_volume = data.volume_per_unit * item.qty;
                    frappe.model.set_value(item.doctype, item.name, "volume", item_volume);
                    total_volume += item_volume;
                }
                
                // Stima colli
                if (item.qty > 0) {
                    const packages = Math.ceil(item.qty / (item.qty > 10 ? 10 : 1));
                    frappe.model.set_value(item.doctype, item.name, "no_of_packages", packages);
                    total_packages += packages;
                }
            }
        });
        
        // Aggiorna totali
        frm.set_value("total_net_weight", total_weight);
        frm.set_value("total_volume", total_volume.toFixed(3));
        frm.set_value("total_packages", total_packages);
        
        frappe.show_alert({
            message: __("Calcolati pesi e volumi: {0} kg, {1} m³, {2} colli", 
                [total_weight.toFixed(2), total_volume.toFixed(3), total_packages]),
            indicator: "green"
        });
    });
};

// Mostra info spedizione
iderp.show_shipping_info = function(frm) {
    if (!frm.doc.items || frm.doc.items.length === 0) return;
    
    let info_html = `
        <div class="shipping-info" style="margin: 10px 0; padding: 10px; background: #e7f3ff; border-radius: 5px;">
            <h5>${__("Informazioni Spedizione")}</h5>
            <div class="row">
    `;
    
    if (frm.doc.transporter) {
        info_html += `
            <div class="col-sm-4">
                <strong>${__("Trasportatore")}:</strong> ${frm.doc.transporter_name || frm.doc.transporter}
            </div>
        `;
    }
    
    if (frm.doc.total_net_weight) {
        info_html += `
            <div class="col-sm-4">
                <strong>${__("Peso Totale")}:</strong> ${frm.doc.total_net_weight} kg
            </div>
        `;
    }
    
    if (frm.doc.total_packages) {
        info_html += `
            <div class="col-sm-4">
                <strong>${__("Numero Colli")}:</strong> ${frm.doc.total_packages}
            </div>
        `;
    }
    
    info_html += `
            </div>
        </div>
    `;
    
    $(frm.fields_dict.items.wrapper).before(info_html);
};

// Valida articoli consegna
iderp.validate_delivery_items = function(frm) {
    let has_errors = false;
    const warehouse_items = {};
    
    // Raggruppa per magazzino
    frm.doc.items.forEach(item => {
        if (!item.warehouse) {
            frappe.msgprint({
                title: __("Magazzino Mancante"),
                message: __("Riga {0}: Specificare il magazzino", [item.idx]),
                indicator: "red"
            });
            has_errors = true;
        } else {
            if (!warehouse_items[item.warehouse]) {
                warehouse_items[item.warehouse] = [];
            }
            warehouse_items[item.warehouse].push(item);
        }
    });
    
    // Controlla disponibilità per magazzino
    // (implementazione semplificata)
    
    return !has_errors;
};

// Valida info trasporto
iderp.validate_transport_info = function(frm) {
    // Per spedizioni con trasportatore esterno
    if (frm.doc.transporter && !frm.doc.lr_no) {
        frappe.confirm(
            __("Numero documento di trasporto non specificato. Continuare?"),
            () => true,
            () => false
        );
    }
    
    // Controllo causale trasporto
    if (!frm.doc.transport_reason) {
        frm.set_value("transport_reason", "Vendita");
    }
    
    return true;
};

// Controllo limiti spedizione
iderp.check_shipping_limits = function(frm) {
    // Limiti peso per tipo spedizione
    const weight_limits = {
        "Corriere": 30,
        "Corriere Espresso": 20,
        "Trasporto Dedicato": 1000
    };
    
    if (frm.doc.shipping_type && frm.doc.total_net_weight) {
        const limit = weight_limits[frm.doc.shipping_type];
        
        if (limit && frm.doc.total_net_weight > limit) {
            return new Promise((resolve, reject) => {
                frappe.confirm(
                    __("Il peso totale ({0} kg) supera il limite per {1} ({2} kg). Continuare?",
                        [frm.doc.total_net_weight, frm.doc.shipping_type, limit]),
                    () => resolve(),
                    () => reject("Limite peso superato")
                );
            });
        }
    }
    
    return Promise.resolve();
};

// Mostra tracking spedizione
iderp.show_shipping_tracking = function(frm) {
    if (frm.doc.tracking_number) {
        // URL tracking in base al corriere
        const tracking_urls = {
            "DHL": `https://www.dhl.com/it-it/home/tracking.html?tracking-id=${frm.doc.tracking_number}`,
            "UPS": `https://www.ups.com/track?tracknum=${frm.doc.tracking_number}`,
            "TNT": `https://www.tnt.it/tracking/Tracking.aspx?Number=${frm.doc.tracking_number}`,
            "SDA": `https://www.sda.it/wps/portal/Servizi_online/dettaglio-spedizione?locale=it&tracing.letteraVettura=${frm.doc.tracking_number}`
        };
        
        const url = tracking_urls[frm.doc.transporter_name] || "#";
        
        if (url !== "#") {
            window.open(url, "_blank");
        } else {
            frappe.msgprint(__("URL tracking non disponibile per {0}", [frm.doc.transporter_name]));
        }
    } else {
        frappe.msgprint(__("Numero tracking non disponibile"));
    }
};
