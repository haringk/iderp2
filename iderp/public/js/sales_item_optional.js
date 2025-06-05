// iderp/public/js/sales_item_optional.js

frappe.provide("iderp.optional");

iderp.optional = {
    /**
     * Setup optional handlers per documenti vendita
     */
    setup_optional_handlers: function(frm, cdt, cdn) {
        // Aggiungi pulsante per selezionare optional
        frm.fields_dict.items.grid.add_custom_button(__('Aggiungi Optional'), function() {
            let row = frm.fields_dict.items.grid.get_selected_children()[0];
            if (row) {
                iderp.optional.show_optional_selector(frm, row);
            } else {
                frappe.msgprint(__('Seleziona prima una riga articolo'));
            }
        });
        
        // Handler per cambio quantità
        frm.cscript.item_optionals_on_form_rendered = function(doc, grid_row) {
            // Aggiungi handler per ricalcolo automatico
            grid_row.fields_dict.quantity.df.onchange = function() {
                iderp.optional.recalculate_optional_price(frm, grid_row);
            };
        };
    },
    
    /**
     * Mostra dialog per selezione optional
     */
    show_optional_selector: function(frm, item_row) {
        if (!item_row.item_code) {
            frappe.msgprint(__('Seleziona prima un articolo'));
            return;
        }
        
        // Ottieni optional applicabili
        frappe.call({
            method: 'iderp.doctype.item_optional.item_optional.get_applicable_optionals',
            args: {
                item_code: item_row.item_code
            },
            callback: function(r) {
                if (r.message && r.message.length > 0) {
                    iderp.optional.show_optional_dialog(frm, item_row, r.message);
                } else {
                    frappe.msgprint(__('Nessun optional disponibile per questo articolo'));
                }
            }
        });
    },
    
    /**
     * Dialog per selezione optional
     */
    show_optional_dialog: function(frm, item_row, optionals) {
        // Prepara opzioni per MultiCheck
        let options = optionals.map(opt => ({
            label: `${opt.optional_name} (${iderp.optional.format_price(opt)})`,
            value: opt.optional,
            checked: iderp.optional.is_optional_selected(item_row, opt.optional)
        }));
        
        let d = new frappe.ui.Dialog({
            title: __('Seleziona Optional per {0}', [item_row.item_name || item_row.item_code]),
            fields: [
                {
                    fieldname: 'optionals',
                    fieldtype: 'MultiCheck',
                    label: __('Optional Disponibili'),
                    options: options,
                    columns: 1
                },
                {
                    fieldname: 'apply_template',
                    fieldtype: 'Check',
                    label: __('Applica Template Predefinito'),
                    default: 0,
                    onchange: function() {
                        if (this.get_value()) {
                            iderp.optional.load_template_optionals(d, item_row.item_code);
                        }
                    }
                }
            ],
            primary_action_label: __('Applica'),
            primary_action: function(values) {
                iderp.optional.apply_selected_optionals(frm, item_row, values.optionals);
                d.hide();
            }
        });
        
        d.show();
    },
    
    /**
     * Formatta prezzo optional per visualizzazione
     */
    format_price: function(opt) {
        if (opt.pricing_type === 'Fisso') {
            return format_currency(opt.price);
        } else if (opt.pricing_type === 'Percentuale') {
            return `${opt.price}%`;
        } else if (opt.pricing_type === 'Per Metro Quadrato') {
            return `${format_currency(opt.price)}/m²`;
        } else if (opt.pricing_type === 'Per Metro Lineare') {
            return `${format_currency(opt.price)}/ml`;
        }
        return format_currency(opt.price);
    },
    
    /**
     * Verifica se optional è già selezionato
     */
    is_optional_selected: function(item_row, optional_name) {
        if (item_row.item_optionals) {
            return item_row.item_optionals.some(opt => opt.optional === optional_name);
        }
        return false;
    },
    
    /**
     * Applica optional selezionati alla riga
     */
    apply_selected_optionals: function(frm, item_row, selected_optionals) {
        // Rimuovi optional non più selezionati
        if (item_row.item_optionals) {
            item_row.item_optionals = item_row.item_optionals.filter(opt => 
                selected_optionals.includes(opt.optional)
            );
        } else {
            item_row.item_optionals = [];
        }
        
        // Aggiungi nuovi optional
        selected_optionals.forEach(optional_name => {
            if (!iderp.optional.is_optional_selected(item_row, optional_name)) {
                // Ottieni dettagli optional
                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: 'Item Optional',
                        name: optional_name
                    },
                    callback: function(r) {
                        if (r.message) {
                            let opt = r.message;
                            let new_row = frm.add_child('items', {
                                optional: opt.name,
                                description: opt.description,
                                pricing_type: opt.pricing_type,
                                unit_price: opt.price,
                                quantity: 1
                            }, item_row.idx);
                            
                            // Ricalcola prezzo
                            iderp.optional.recalculate_optional_price(frm, new_row);
                        }
                    }
                });
            }
        });
        
        frm.refresh_field('items');
    },
    
    /**
     * Ricalcola prezzo optional
     */
    recalculate_optional_price: function(frm, optional_row) {
        let parent_item = frm.doc.items[optional_row.idx - 1];
        
        if (optional_row.pricing_type === 'Fisso') {
            optional_row.total_price = optional_row.unit_price * optional_row.quantity;
            
        } else if (optional_row.pricing_type === 'Percentuale') {
            let base_amount = parent_item.rate * parent_item.qty;
            optional_row.total_price = base_amount * optional_row.unit_price / 100;
            
        } else if (optional_row.pricing_type === 'Per Metro Quadrato') {
            if (parent_item.mq_calcolati) {
                optional_row.total_price = optional_row.unit_price * parent_item.mq_calcolati;
            } else {
                optional_row.total_price = optional_row.unit_price * optional_row.quantity;
            }
            
        } else if (optional_row.pricing_type === 'Per Metro Lineare') {
            if (parent_item.ml_calcolati) {
                optional_row.total_price = optional_row.unit_price * parent_item.ml_calcolati;
            } else {
                optional_row.total_price = optional_row.unit_price * optional_row.quantity;
            }
        }
        
        // Aggiorna totale optional sulla riga item
        iderp.optional.update_item_optional_total(frm, parent_item);
        
        frm.refresh_field('items');
    },
    
    /**
     * Aggiorna totale optional per riga item
     */
    update_item_optional_total: function(frm, item_row) {
        let total = 0;
        
        if (item_row.item_optionals) {
            item_row.item_optionals.forEach(opt => {
                total += opt.total_price || 0;
            });
        }
        
        item_row.optional_total = total;
        
        // Trigger evento per aggiornamento totali documento
        frm.trigger('calculate_totals');
    },
    
    /**
     * Carica optional da template
     */
    load_template_optionals: function(dialog, item_code) {
        frappe.call({
            method: 'iderp.doctype.optional_template.optional_template.get_template_for_item',
            args: {
                item_code: item_code
            },
            callback: function(r) {
                if (r.message && r.message.optionals) {
                    // Seleziona automaticamente gli optional del template
                    let field = dialog.get_field('optionals');
                    let selected = r.message.optionals
                        .filter(opt => opt.default_selected || opt.is_mandatory)
                        .map(opt => opt.optional);
                    
                    field.set_value(selected);
                    
                    frappe.show_alert({
                        message: __('Template "{0}" applicato', [r.message.template_name]),
                        indicator: 'green'
                    });
                }
            }
        });
    },
    
    /**
     * Mostra riepilogo optional documento
     */
    show_optional_summary: function(frm) {
        frappe.call({
            method: 'iderp.doctype.sales_item_optional.sales_item_optional.get_optional_summary',
            args: {
                parent_doctype: frm.doctype,
                parent_name: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    let summary_html = iderp.optional.render_summary(r.message);
                    frappe.msgprint({
                        title: __('Riepilogo Optional'),
                        message: summary_html,
                        wide: true
                    });
                }
            }
        });
    },
    
    /**
     * Renderizza HTML riepilogo
     */
    render_summary: function(summary) {
        let html = '<table class="table table-bordered">';
        html += '<thead><tr>';
        html += '<th>' + __('Optional') + '</th>';
        html += '<th>' + __('Quantità') + '</th>';
        html += '<th class="text-right">' + __('Importo') + '</th>';
        html += '</tr></thead><tbody>';
        
        summary.optionals.forEach(opt => {
            html += '<tr>';
            html += '<td>' + opt.description + '</td>';
            html += '<td>' + opt.total_qty + '</td>';
            html += '<td class="text-right">' + format_currency(opt.total_amount) + '</td>';
            html += '</tr>';
        });
        
        html += '</tbody><tfoot><tr>';
        html += '<th colspan="2">' + __('Totale Optional') + '</th>';
        html += '<th class="text-right">' + format_currency(summary.total_amount) + '</th>';
        html += '</tr></tfoot></table>';
        
        return html;
    }
};