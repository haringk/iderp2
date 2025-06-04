# iderp/hooks.py

app_name = "iderp"
app_title = "IDERP - Sistema Stampa Digitale"
app_publisher = "idstudio AI"
app_description = "Plugin ERPNext per stampa digitale con calcoli universali"
app_email = "ai@idstudio.org"
app_license = "MIT"
app_version = "2.0.0"

# JavaScript e CSS - ERPNext 15 Compatible
doctype_js = {
    "Item": "public/js/item_config.js",
    "Quotation": "public/js/item_dimension.js",
    "Sales Order": "public/js/item_dimension.js",
    "Sales Invoice": "public/js/item_dimension.js",
    "Delivery Note": "public/js/item_dimension.js"
}

app_include_css = [
    "/assets/iderp/css/iderp.css"
]

# Website Assets per E-commerce
website_context = {
    "favicon": "/assets/iderp/images/favicon.ico"
}

# Server-side Events - ATTIVATI per ERPNext 15
doc_events = {
    "Quotation": {
        "before_save": [
            "iderp.universal_pricing.apply_universal_pricing_server_side",
            "iderp.global_minimums.apply_global_minimums_server_side"
        ],
        "validate": "iderp.copy_fields.copy_custom_fields"
    },
    "Sales Order": {
        "before_save": [
            "iderp.universal_pricing.apply_universal_pricing_server_side",
            "iderp.global_minimums.apply_global_minimums_server_side"
        ],
        "validate": "iderp.copy_fields.copy_custom_fields"
    },
    "Sales Invoice": {
        "before_save": [
            "iderp.universal_pricing.apply_universal_pricing_server_side",
            "iderp.global_minimums.apply_global_minimums_server_side"
        ],
        "validate": "iderp.copy_fields.copy_custom_fields"
    },
    "Delivery Note": {
        "before_save": [
            "iderp.universal_pricing.apply_universal_pricing_server_side",
            "iderp.global_minimums.apply_global_minimums_server_side"
        ],
        "validate": "iderp.copy_fields.copy_custom_fields"
    },
    "Item": {
        "validate": "iderp.pricing_utils.validate_pricing_tiers"
    }
}

# API Whitelist - ERPNext 15 Compatible
whitelisted_methods = [
    # Pricing APIs
    "iderp.pricing_utils.get_item_pricing_tiers",
    "iderp.pricing_utils.calculate_item_pricing", 
    "iderp.pricing_utils.calculate_universal_item_pricing",
    "iderp.pricing_utils.calculate_universal_item_pricing_with_fallback",
    "iderp.pricing_utils.get_customer_group_min_sqm",
    
    # Customer Group APIs  
    "iderp.customer_group_pricing.get_customer_group_pricing",
    
    # E-commerce APIs (placeholder per future implementazioni)
    "iderp.ecommerce.calculate_item_price",
    "iderp.ecommerce.add_to_cart_calculated",
    "iderp.ecommerce.get_item_selling_config"
]

# Fixtures - Dati base da installare
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            ["dt", "in", ["Item", "Quotation Item", "Sales Order Item", "Sales Invoice Item", "Delivery Note Item"]]
        ]
    }
]

# Installation Hook
after_install = "iderp.install.after_install"
after_migrate = "iderp.install.after_install"

# Scheduler Events per manutenzione sistema
scheduler_events = {
    "daily": [
        "iderp.maintenance.cleanup_old_calculations"
    ],
    "weekly": [
        "iderp.reports.generate_pricing_reports"
    ]
}

# Boot Session - Configurazione client-side
boot_session = "iderp.boot.boot_session"

# Website Routes per E-commerce
website_route_rules = [
    {"from_route": "/calculator/<item_code>", "to_route": "iderp_calculator"},
]

# Standard include 
standard_portal_menu_items = [
    {
        "title": "Configuratore Prodotti",
        "route": "/iderp-calculator", 
        "reference_doctype": "Item",
        "role": "Customer"
    }
]

# Jinja Filters per template
jinja = {
    "methods": [
        "iderp.ecommerce.get_measurement_options",
        "iderp.ecommerce.format_price_with_measurement"
    ]
}

# Override DocType Classes per customizzazioni avanzate
override_doctype_class = {
    "Item": "iderp.overrides.CustomItem",
    "Quotation": "iderp.overrides.CustomQuotation"  
}

# Translation
default_mail_footer = """
<div style="text-align: center; margin-top: 20px; color: #888;">
    <small>Powered by IDERP - Sistema Stampa Digitale</small>
</div>
"""

# Regional Settings Italia
country = "Italy"
currency = "EUR"
timezone = "Europe/Rome"

# ERPNext 15 Specific Configuration
web_include_js = [
    "/assets/iderp/js/iderp_web.js"
]

web_include_css = [
    "/assets/iderp/css/ecommerce_styles.css"
]

# Permission Queries per sicurezza avanzata
permission_query_conditions = {
    "Item": "iderp.permissions.get_item_permission_query_conditions"
}

has_permission = {
    "Item": "iderp.permissions.has_item_permission"
}

# Document onload events
doc_events.update({
    "Customer": {
        "after_insert": "iderp.setup.setup_default_customer_group"
    },
    "Price List": {
        "validate": "iderp.pricing.validate_price_list_compatibility"
    }
})

# Navbar customization
app_logo_url = "/assets/iderp/images/logo.png"

# Error logging
log_events = {
    "Item": {
        "on_error": "iderp.error_handler.log_item_error"
    }
}

# Performance monitoring  
benchmarks = {
    "pricing_calculation": {
        "method": "iderp.pricing_utils.calculate_universal_item_pricing",
        "threshold": 1.0  # 1 secondo max
    }
}

# Data Import Templates
data_import_tool = [
    {
        "module": "IDERP",
        "doctype": "Item",
        "template": "iderp_item_template.xlsx"
    }
]

# Development mode settings
if frappe.conf.get("developer_mode"):
    doctype_js.update({
        "Item": [
            "public/js/item_config.js",
            "public/js/item_debug.js"
        ]
    })