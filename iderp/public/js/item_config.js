// iderp/public/js/item_config.js
console.log("IDERP: Item Config JS Loaded");

frappe.ui.form.on('Item', {
    refresh: function(frm) {
        // Aggiungi sezione di configurazione per vendita personalizzata
        add_measurement_config_section(frm);
        
        // Pulsante per testare configurazione e-commerce
        if (!frm.is_new()) {
            frm.add_custom_button(__('Test E-commerce Config'), function() {
                test_ecommerce_config(frm);
            }, __('Actions'));
        }
    },
    
    onload: function(frm) {
        // Aggiungi campi custom se non esistenti
        setup_custom_fields(frm);
    }
});

function add_measurement_config_section(frm) {
    // Verifica se la sezione esiste già
    if (frm.get_field('measurement_config_section')) {
        return;
    }
    
    // Aggiungi campi per configurazione vendita personalizzata
    const fields = [
        {
            fieldname: 'measurement_config_section',
            fieldtype: 'Section Break',
            label: 'Configurazione Vendita Personalizzata',
            collapsible: 1
        },
        {
            fieldname: 'supports_custom_measurement',
            fieldtype: 'Check',
            label: 'Supporta Misure Personalizzate',
            description: 'Abilita calcoli per metro quadrato/lineare'
        },
        {
            fieldname: 'tipo_vendita_default',
            fieldtype: 'Select',
            label: 'Tipo Vendita Default',
            options: '\nPezzo\nMetro Quadrato\nMetro Lineare',
            depends_on: 'supports_custom_measurement'
        },
        {
            fieldname: 'config_column_break',
            fieldtype: 'Column Break'
        },
        {
            fieldname: 'larghezza_materiale_default',
            fieldtype: 'Float',
            label: 'Larghezza Materiale Default (cm)',
            precision: 2,
            depends_on: 'eval:doc.tipo_vendita_default=="Metro Lineare"'
        },
        {
            fieldname: 'measurement_limits_section',
            fieldtype: 'Section Break',
            label: 'Limiti Misurazione',
            depends_on: 'supports_custom_measurement',
            collapsible: 1
        },
        {
            fieldname: 'base_min',
            fieldtype: 'Float',
            label: 'Base Minima (cm)',
            default: 1,
            depends_on: 'eval:doc.tipo_vendita_default=="Metro Quadrato"'
        },
        {
            fieldname: 'base_max',
            fieldtype: 'Float',
            label: 'Base Massima (cm)',
            default: 1000,
            depends_on: 'eval:doc.tipo_vendita_default=="Metro Quadrato"'
        },
        {
            fieldname: 'limits_column_break',
            fieldtype: 'Column Break'
        },
        {
            fieldname: 'altezza_min',
            fieldtype: 'Float',
            label: 'Altezza Minima (cm)',
            default: 1,
            depends_on: 'eval:doc.tipo_vendita_default=="Metro Quadrato"'
        },
        {
            fieldname: 'altezza_max',
            fieldtype: 'Float',
            label: 'Altezza Massima (cm)',
            default: 1000,
            depends_on: 'eval:doc.tipo_vendita_default=="Metro Quadrato"'
        },
        {
            fieldname: 'lunghezza_limits_section',
            fieldtype: 'Section Break',
            label: 'Limiti Lunghezza',
            depends_on: 'eval:doc.tipo_vendita_default=="Metro Lineare"',
            collapsible: 1
        },
        {
            fieldname: 'lunghezza_min',
            fieldtype: 'Float',
            label: 'Lunghezza Minima (cm)',
            default: 1,
            depends_on: 'eval:doc.tipo_vendita_default=="Metro Lineare"'
        },
        {
            fieldname: 'lunghezza_max',
            fieldtype: 'Float',
            label: 'Lunghezza Massima (cm)',
            default: 10000,
            depends_on: 'eval:doc.tipo_vendita_default=="Metro Lineare"'
        },
        {
            fieldname: 'ecommerce_display_section',
            fieldtype: 'Section Break',
            label: 'Impostazioni Visualizzazione E-commerce',
            depends_on: 'supports_custom_measurement',
            collapsible: 1
        },
        {
            fieldname: 'show_measurement_helper',
            fieldtype: 'Check',
            label: 'Mostra Aiuto Misurazione',
            default: 1,
            description: 'Mostra tooltip e aiuti per le misure'
        },
        {
            fieldname: 'measurement_helper_text',
            fieldtype: 'Text',
            label: 'Testo Aiuto Personalizzato',
            depends_on: 'show_measurement_helper',
            description: 'Testo di aiuto specifico per questo prodotto'
        }
    ];
    
    // Aggiungi i campi dinamicamente
    fields.forEach(field => {
        if (!frm.get_field(field.fieldname)) {
            frm.add_custom_button('', () => {}, ''); // Hack per refresh
        }
    });
}

function setup_custom_fields(frm) {
    // Setup eventi per campi custom
    frm.fields_dict.supports_custom_measurement && 
    frm.fields_dict.supports_custom_measurement.$input.on('change', function() {
        frm.refresh_fields();
    });
    
    frm.fields_dict.tipo_vendita_default && 
    frm.fields_dict.tipo_vendita_default.$input.on('change', function() {
        frm.refresh_fields();
        update_default_values(frm);
    });
}

function update_default_values(frm) {
    const tipo_vendita = frm.doc.tipo_vendita_default;
    
    // Imposta valori di default in base al tipo vendita
    if (tipo_vendita === 'Metro Quadrato') {
        if (!frm.doc.base_min) frm.set_value('base_min', 10);
        if (!frm.doc.base_max) frm.set_value('base_max', 300);
        if (!frm.doc.altezza_min) frm.set_value('altezza_min', 10);
        if (!frm.doc.altezza_max) frm.set_value('altezza_max', 300);
    } else if (tipo_vendita === 'Metro Lineare') {
        if (!frm.doc.lunghezza_min) frm.set_value('lunghezza_min', 10);
        if (!frm.doc.lunghezza_max) frm.set_value('lunghezza_max', 1000);
        if (!frm.doc.larghezza_materiale_default) frm.set_value('larghezza_materiale_default', 100);
    }
}

function test_ecommerce_config(frm) {
    if (!frm.doc.supports_custom_measurement) {
        frappe.msgprint({
            title: __('Test Configurazione'),
            message: 'Questo item non supporta misure personalizzate.',
            indicator: 'orange'
        });
        return;
    }
    
    // Crea dialog per testare configurazione
    const dialog = new frappe.ui.Dialog({
        title: 'Test Configurazione E-commerce',
        fields: [
            {
                fieldname: 'item_code',
                fieldtype: 'Data',
                label: 'Item Code',
                read_only: 1,
                default: frm.doc.item_code
            },
            {
                fieldname: 'tipo_vendita_test',
                fieldtype: 'Select',
                label: 'Tipo Vendita',
                options: '\nPezzo\nMetro Quadrato\nMetro Lineare',
                default: frm.doc.tipo_vendita_default || 'Pezzo',
                reqd: 1
            },
            {
                fieldname: 'test_measurements_section',
                fieldtype: 'Section Break',
                label: 'Misure Test'
            },
            {
                fieldname: 'base_test',
                fieldtype: 'Float',
                label: 'Base (cm)',
                depends_on: 'eval:doc.tipo_vendita_test=="Metro Quadrato"'
            },
            {
                fieldname: 'altezza_test',
                fieldtype: 'Float',
                label: 'Altezza (cm)',
                depends_on: 'eval:doc.tipo_vendita_test=="Metro Quadrato"'
            },
            {
                fieldname: 'lunghezza_test',
                fieldtype: 'Float',
                label: 'Lunghezza (cm)',
                depends_on: 'eval:doc.tipo_vendita_test=="Metro Lineare"'
            },
            {
                fieldname: 'test_result_section',
                fieldtype: 'Section Break',
                label: 'Risultato Test'
            },
            {
                fieldname: 'test_result',
                fieldtype: 'Code',
                label: 'Risultato API',
                read_only: 1
            }
        ],
        primary_action_label: 'Testa Configurazione',
        primary_action: function(values) {
            test_api_call(values, dialog);
        }
    });
    
    dialog.show();
}

function test_api_call(values, dialog) {
    const measurements = {
        base: values.base_test || 0,
        altezza: values.altezza_test || 0,
        lunghezza: values.lunghezza_test || 0,
        larghezza_materiale: values.larghezza_materiale_default || 0
    };
    
    frappe.call({
        method: 'iderp.ecommerce.calculate_item_price',
        args: {
            item_code: values.item_code,
            tipo_vendita: values.tipo_vendita_test,
            ...measurements
        },
        callback: function(r) {
            if (r.message) {
                dialog.set_value('test_result', JSON.stringify(r.message, null, 2));
                
                if (r.message.error) {
                    frappe.show_alert({
                        message: 'Test fallito: ' + r.message.error,
                        indicator: 'red'
                    });
                } else {
                    frappe.show_alert({
                        message: `Test riuscito! Prezzo calcolato: €${r.message.calculated_price.toFixed(2)}`,
                        indicator: 'green'
                    });
                }
            }
        },
        error: function(r) {
            dialog.set_value('test_result', 'Errore API: ' + JSON.stringify(r, null, 2));
            frappe.show_alert({
                message: 'Errore nella chiamata API',
                indicator: 'red'
            });
        }
    });
}

// Utility per validare configurazione
function validate_measurement_config(frm) {
    const errors = [];
    
    if (frm.doc.supports_custom_measurement) {
        if (!frm.doc.tipo_vendita_default) {
            errors.push('Seleziona un tipo vendita default');
        }
        
        if (frm.doc.tipo_vendita_default === 'Metro Quadrato') {
            if (frm.doc.base_min >= frm.doc.base_max) {
                errors.push('Base minima deve essere minore di base massima');
            }
            if (frm.doc.altezza_min >= frm.doc.altezza_max) {
                errors.push('Altezza minima deve essere minore di altezza massima');
            }
        }
        
        if (frm.doc.tipo_vendita_default === 'Metro Lineare') {
            if (frm.doc.lunghezza_min >= frm.doc.lunghezza_max) {
                errors.push('Lunghezza minima deve essere minore di lunghezza massima');
            }
            if (!frm.doc.larghezza_materiale_default) {
                errors.push('Imposta una larghezza materiale default');
            }
        }
    }
    
    return errors;
}

// Hook per validazione prima del save
frappe.ui.form.on('Item', {
    validate: function(frm) {
        const errors = validate_measurement_config(frm);
        if (errors.length > 0) {
            frappe.throw(__('Errori configurazione misurazione:\n' + errors.join('\n')));
        }
    }
});