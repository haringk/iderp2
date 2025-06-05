// iderp/public/js/item_config.js
// iderp Item Configuration for ERPNext 15
// Enhanced version with proper validation and UX

console.log("iderp: Item Config JS Loading - ERPNext 15 Compatible");

frappe.ui.form.on('Item', {
    refresh: function(frm) {
        console.log("iderp: Item form refreshed");
        
        // Add custom buttons for iderp configuration
        if (frm.doc.supports_custom_measurement) {
            add_iderp_buttons(frm);
        }
        
        // Show iderp status indicator
        update_iderp_status_indicator(frm);
        
        // Add help messages
        add_iderp_help_messages(frm);
    },
    
    supports_custom_measurement: function(frm) {
        console.log("iderp: Custom measurement toggled:", frm.doc.supports_custom_measurement);
        
        if (frm.doc.supports_custom_measurement) {
            // Enable iderp features
            enable_iderp_features(frm);
            
            // Set default selling type if not set
            if (!frm.doc.tipo_vendita_default) {
                frm.set_value('tipo_vendita_default', 'Metro Quadrato');
            }
            
            // Show configuration guide
            show_iderp_setup_guide(frm);
        } else {
            // Disable iderp features
            disable_iderp_features(frm);
        }
        
        // Update UI
        frm.refresh_fields();
        update_iderp_status_indicator(frm);
    },
    
    tipo_vendita_default: function(frm) {
        if (frm.doc.supports_custom_measurement && frm.doc.tipo_vendita_default) {
            console.log("iderp: Default selling type changed to:", frm.doc.tipo_vendita_default);
            
            // Update help text based on selling type
            update_selling_type_help(frm);
            
            // Validate configuration
            validate_iderp_configuration(frm);
        }
    },
    
    before_save: function(frm) {
        if (frm.doc.supports_custom_measurement) {
            return validate_iderp_before_save(frm);
        }
    }
});

function add_iderp_buttons(frm) {
    // Remove existing buttons first
    frm.page.remove_inner_button('Configure Pricing Tiers');
    frm.page.remove_inner_button('Test iderp Calculation');
    frm.page.remove_inner_button('iderp Summary');
    
    // Add configuration button
    frm.page.add_inner_button(__('Configure Pricing Tiers'), function() {
        open_pricing_tiers_dialog(frm);
    });
    
    // Add test calculation button
    frm.page.add_inner_button(__('Test iderp Calculation'), function() {
        open_test_calculation_dialog(frm);
    });
    
    // Add summary button
    frm.page.add_inner_button(__('iderp Summary'), function() {
        show_iderp_summary(frm);
    });
}

function update_iderp_status_indicator(frm) {
    let status = get_iderp_configuration_status(frm);
    
    let color = 'red';
    let message = 'iderp Not Configured';
    
    if (status.configured) {
        if (status.complete) {
            color = 'green';
            message = `iderp Configured: ${status.summary}`;
        } else {
            color = 'orange';
            message = `iderp Partial: ${status.summary}`;
        }
    }
    
    frm.page.set_indicator(message, color);
}

function get_iderp_configuration_status(frm) {
    if (!frm.doc.supports_custom_measurement) {
        return { configured: false, complete: false, summary: 'Disabled' };
    }
    
    let status = {
        configured: true,
        complete: false,
        has_pricing_tiers: false,
        has_customer_minimums: false,
        summary: ''
    };
    
    // Check pricing tiers
    if (frm.doc.pricing_tiers && frm.doc.pricing_tiers.length > 0) {
        status.has_pricing_tiers = true;
    }
    
    // Check customer group minimums
    if (frm.doc.customer_group_minimums && frm.doc.customer_group_minimums.length > 0) {
        status.has_customer_minimums = true;
    }
    
    // Build summary
    let parts = [];
    if (status.has_pricing_tiers) parts.push(`${frm.doc.pricing_tiers.length} tiers`);
    if (status.has_customer_minimums) parts.push(`${frm.doc.customer_group_minimums.length} minimums`);
    
    status.summary = parts.length > 0 ? parts.join(', ') : 'Basic setup';
    status.complete = status.has_pricing_tiers;
    
    return status;
}

function enable_iderp_features(frm) {
    // Show iderp sections
    frm.toggle_display(['pricing_section', 'customer_group_minimums_section'], true);
    
    // Enable fields
    frm.set_df_property('tipo_vendita_default', 'reqd', 1);
    
    // Add custom styling
    add_iderp_styling(frm);
}

function disable_iderp_features(frm) {
    // Hide iderp sections
    frm.toggle_display(['pricing_section', 'customer_group_minimums_section'], false);
    
    // Clear required flags
    frm.set_df_property('tipo_vendita_default', 'reqd', 0);
    
    // Clear values
    frm.set_value('tipo_vendita_default', '');
}

function add_iderp_styling(frm) {
    // Add visual indicators for iderp sections
    setTimeout(function() {
        let sections = frm.fields_dict.pricing_section?.$wrapper;
        if (sections) {
            sections.addClass('iderp-enabled-section');
        }
    }, 500);
}

function show_iderp_setup_guide(frm) {
    frappe.msgprint({
        title: __('iderp Configuration Guide'),
        indicator: 'blue',
        message: `
            <div class="iderp-setup-guide">
                <h4>Setup Steps:</h4>
                <ol>
                    <li><strong>Select Default Selling Type</strong><br>Choose Metro Quadrato, Metro Lineare, or Pezzo</li>
                    <li><strong>Configure Pricing Tiers</strong><br>Set up quantity-based pricing for different selling types</li>
                    <li><strong>Set Customer Group Minimums</strong><br>Define minimum quantities for different customer groups</li>
                    <li><strong>Test Configuration</strong><br>Use the test calculation to verify setup</li>
                </ol>
                <p><em>Selling Type Selected: <strong>${frm.doc.tipo_vendita_default || 'None'}</strong></em></p>
            </div>
        `
    });
}

function update_selling_type_help(frm) {
    let help_text = '';
    
    switch(frm.doc.tipo_vendita_default) {
        case 'Metro Quadrato':
            help_text = 'Customers will enter Base × Height in cm. Price calculated per m².';
            break;
        case 'Metro Lineare':
            help_text = 'Customers will enter Length in cm. Price calculated per linear meter.';
            break;
        case 'Pezzo':
            help_text = 'Traditional per-piece pricing. No custom measurements required.';
            break;
    }
    
    if (help_text) {
        frm.set_df_property('tipo_vendita_default', 'description', help_text);
    }
}

function validate_iderp_configuration(frm) {
    // Validate that configuration makes sense
    if (!frm.doc.tipo_vendita_default) {
        frappe.msgprint(__('Please select a Default Selling Type for iderp configuration'));
        return false;
    }
    
    return true;
}

function validate_iderp_before_save(frm) {
    return new Promise((resolve) => {
        if (!validate_iderp_configuration(frm)) {
            resolve(false);
            return;
        }
        
        // Additional async validations can go here
        resolve(true);
    });
}

function open_pricing_tiers_dialog(frm) {
    frappe.msgprint({
        title: __('Pricing Tiers Configuration'),
        message: __('Use the Pricing Tiers table below to configure quantity-based pricing for different selling types.'),
        primary_action: {
            label: __('Open Item'),
            action: function() {
                // Scroll to pricing section
                setTimeout(function() {
                    let section = frm.fields_dict.pricing_section?.$wrapper;
                    if (section) {
                        section[0].scrollIntoView({ behavior: 'smooth' });
                    }
                }, 100);
            }
        }
    });
}

function open_test_calculation_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Test iderp Calculation'),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'test_selling_type',
                label: __('Selling Type'),
                options: 'Metro Quadrato\nMetro Lineare\nPezzo',
                default: frm.doc.tipo_vendita_default,
                reqd: 1
            },
            {
                fieldtype: 'Section Break'
            },
            {
                fieldtype: 'Float',
                fieldname: 'test_base',
                label: __('Base (cm)'),
                depends_on: 'eval:doc.test_selling_type=="Metro Quadrato"'
            },
            {
                fieldtype: 'Float',
                fieldname: 'test_altezza',
                label: __('Height (cm)'),
                depends_on: 'eval:doc.test_selling_type=="Metro Quadrato"'
            },
            {
                fieldtype: 'Float',
                fieldname: 'test_lunghezza',
                label: __('Length (cm)'),
                depends_on: 'eval:doc.test_selling_type=="Metro Lineare"'
            },
            {
                fieldtype: 'Int',
                fieldname: 'test_qty',
                label: __('Quantity'),
                default: 1,
                reqd: 1
            },
            {
                fieldtype: 'Section Break'
            },
            {
                fieldtype: 'HTML',
                fieldname: 'test_result',
                label: __('Calculation Result')
            }
        ],
        primary_action_label: __('Calculate'),
        primary_action: function(values) {
            test_iderp_calculation(frm, values, dialog);
        }
    });
    
    dialog.show();
}

function test_iderp_calculation(frm, values, dialog) {
    frappe.call({
        method: 'iderp.pricing_utils.calculate_universal_item_pricing',
        args: {
            item_code: frm.doc.item_code,
            tipo_vendita: values.test_selling_type,
            base: values.test_base || 0,
            altezza: values.test_altezza || 0,
            lunghezza: values.test_lunghezza || 0,
            qty: values.test_qty || 1
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                let result = r.message;
                let html = `
                    <div class="alert alert-success">
                        <h4>✅ Calculation Successful</h4>
                        <p><strong>Rate:</strong> €${result.rate}</p>
                        <p><strong>Total Quantity:</strong> ${result.total_qty} ${result.qty_label}</p>
                        <p><strong>Price per Unit:</strong> €${result.price_per_unit}</p>
                        <p><strong>Tier:</strong> ${result.tier_info?.tier_name || 'N/A'}</p>
                    </div>
                `;
                dialog.set_value('test_result', html);
            } else {
                let html = `
                    <div class="alert alert-danger">
                        <h4>❌ Calculation Failed</h4>
                        <p>${r.message?.error || 'Unknown error'}</p>
                    </div>
                `;
                dialog.set_value('test_result', html);
            }
        }
    });
}

function show_iderp_summary(frm) {
    let status = get_iderp_configuration_status(frm);
    
    frappe.call({
        method: 'iderp.dashboard.get_configured_items_count',
        callback: function(r) {
            let summary_html = `
                <div class="iderp-summary">
                    <h4>iderp Configuration Summary</h4>
                    <table class="table table-bordered">
                        <tr><td><strong>Item Code:</strong></td><td>${frm.doc.item_code}</td></tr>
                        <tr><td><strong>Supports Custom Measurement:</strong></td><td>${frm.doc.supports_custom_measurement ? '✅ Yes' : '❌ No'}</td></tr>
                        <tr><td><strong>Default Selling Type:</strong></td><td>${frm.doc.tipo_vendita_default || 'Not Set'}</td></tr>
                        <tr><td><strong>Pricing Tiers:</strong></td><td>${frm.doc.pricing_tiers?.length || 0} configured</td></tr>
                        <tr><td><strong>Customer Minimums:</strong></td><td>${frm.doc.customer_group_minimums?.length || 0} configured</td></tr>
                        <tr><td><strong>Status:</strong></td><td>${status.complete ? '✅ Complete' : '⚠️ Incomplete'}</td></tr>
                    </table>
                </div>
            `;
            
            frappe.msgprint({
                title: __('iderp Summary'),
                message: summary_html
            });
        }
    });
}

function add_iderp_help_messages(frm) {
    if (!frm.doc.supports_custom_measurement) {
        return;
    }
    
    // Add contextual help based on configuration state
    let status = get_iderp_configuration_status(frm);
    
    if (!status.has_pricing_tiers) {
        frappe.show_alert({
            message: __('Add pricing tiers to enable automatic price calculation'),
            indicator: 'orange'
        });
    }
}

// Utility function for iderp styling
function add_iderp_css() {
    if ($('.iderp-style').length === 0) {
        $('head').append(`
            <style class="iderp-style">
                .iderp-enabled-section {
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                    background-color: #f8f9fa;
                }
                .iderp-summary table {
                    margin-top: 10px;
                }
                .iderp-setup-guide ol {
                    margin: 15px 0;
                    padding-left: 20px;
                }
                .iderp-setup-guide li {
                    margin-bottom: 8px;
                }
            </style>
        `);
    }
}

// Initialize iderp styling
$(document).ready(function() {
    add_iderp_css();
    console.log("✅ iderp Item Config loaded for ERPNext 15");
});
