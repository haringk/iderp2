# hooks.py (ROOT)

app_name = "iderp"
app_title = "iderp - Sistema Stampa Digitale"
app_publisher = "idstudio"
app_description = "Plugin ERPNext per stampa digitale con calcoli universali Metro Quadrato/Lineare/Pezzo"
app_email = "dev@idstudio.org"
app_license = "MIT"
app_version = "2.0.0"

# ERPNext 15 compatibility flags
required_apps = ["frappe", "erpnext"]
is_frappe_app = True

# JavaScript e CSS - ERPNext 15 Compatible
app_include_js = [
    "/assets/iderp/js/iderp.js"
]

app_include_css = [
    "/assets/iderp/css/iderp.css"
]

doctype_js = {
    "Item": "public/js/item_config.js",
    "Quotation": ["public/js/item_dimension.js", "public/js/sales_item_optional.js"],
    "Sales Order": ["public/js/item_dimension.js", "public/js/sales_item_optional.js"],
    "Sales Invoice": ["public/js/item_dimension.js", "public/js/sales_item_optional.js"],
    "Delivery Note": ["public/js/item_dimension.js", "public/js/sales_item_optional.js"]
}

# Server-side Events - ATTIVATI per ERPNext 15
doc_events = {
    "Quotation": {
        "before_save": [
            "iderp.universal_pricing.apply_universal_pricing_server_side",
            "iderp.global_minimums.apply_global_minimums_server_side",
            "iderp.optional_pricing.calculate_optional_totals"  # AGGIUNGI QUESTA
        ],
        "validate": "iderp.copy_fields.copy_custom_fields"
    },
    "Sales Order": {
        "before_save": [
            "iderp.universal_pricing.apply_universal_pricing_server_side", 
            "iderp.global_minimums.apply_global_minimums_server_side",
            "iderp.optional_pricing.calculate_optional_totals"  # AGGIUNGI QUESTA
        ],
        "validate": "iderp.copy_fields.copy_custom_fields"
    },
    "Sales Invoice": {
        "before_save": [
            "iderp.universal_pricing.apply_universal_pricing_server_side",
            "iderp.global_minimums.apply_global_minimums_server_side",
            "iderp.optional_pricing.calculate_optional_totals"  # AGGIUNGI QUESTA
        ],
        "validate": "iderp.copy_fields.copy_custom_fields"
    },
    "Delivery Note": {
        "before_save": [
            "iderp.universal_pricing.apply_universal_pricing_server_side",
            "iderp.global_minimums.apply_global_minimums_server_side",
            "iderp.optional_pricing.calculate_optional_totals"  # AGGIUNGI QUESTA
        ],
        "validate": "iderp.copy_fields.copy_custom_fields"
    },
    "Item": {
        "validate": "iderp.pricing_utils.validate_pricing_tiers"
    },
    "Customer": {
        "after_insert": "iderp.customer_group_pricing.setup_default_customer_group"
    },
    # AGGIUNGI QUESTO:
    "Item Optional": {
        "validate": "iderp.optional_pricing.validate_optional"
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
    "iderp.customer_group_pricing.apply_customer_group_rules",
    
    # Dashboard APIs
    "iderp.dashboard.get_quotations_this_month",
    "iderp.dashboard.get_top_customer_groups", 
    "iderp.dashboard.get_configured_items_count",
    "iderp.dashboard.get_average_order_value",
    "iderp.dashboard.get_iderp_system_health",
    
    # Optional APIs (AGGIUNGI QUESTE)
    "iderp.api.optional.get_item_optionals",
    "iderp.api.optional.apply_template",
    "iderp.api.optional.calculate_optional_price",
    "iderp.api.optional.get_optional_summary",
    "iderp.api.optional.toggle_optional",
    "iderp.api.optional.get_templates_for_item",
    "iderp.optional_pricing.get_optional_price",
    "iderp.optional_pricing.format_optional_price",

    # E-commerce APIs (placeholder per future implementazioni)
    "iderp.ecommerce.calculate_item_price",
    "iderp.ecommerce.add_to_cart_calculated",
    "iderp.ecommerce.get_item_selling_config"
]

# Installation Hook
after_install = "iderp.install.after_install"
after_migrate = "iderp.install.after_install"

# Boot Session - Configurazione client-side  
boot_session = "iderp.boot_session"

# Scheduler Events per manutenzione sistema
scheduler_events = {
    "daily": [
        "iderp.maintenance.cleanup_old_calculations",
        "iderp.optional_pricing.cleanup_optional_orphans"  # AGGIUNGI
    ],
    "weekly": [
        "iderp.maintenance.cleanup_cache",
        "iderp.reports.generate_weekly_reports"
    ]
}

# Website Routes per E-commerce (future)
website_route_rules = [
    {"from_route": "/calculator/<item_code>", "to_route": "iderp_calculator"},
]

# Fixtures - Dati base da installare
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["dt", "in", ["Item", "Quotation Item", "Sales Order Item", 
                         "Sales Invoice Item", "Delivery Note Item",
                         "Quotation", "Work Order", "Portal Settings"]]  # AGGIUNTI NUOVI
        ]
    },
    {
        "dt": "Property Setter", 
        "filters": [
            ["doc_type", "in", ["Item", "Quotation Item", "Sales Order Item"]]
        ]
    },
    # AGGIUNGI QUESTO BLOCCO:
    {
        "dt": "Item Optional",
        "filters": [["name", "in", ["Plastificazione Lucida", "Plastificazione Opaca", 
                                    "Fustella Sagomata", "Occhielli Metallici", 
                                    "Verniciatura UV Spot"]]]
    }
]

# ERPNext 15 Specific Configuration
web_include_js = [
    "/assets/iderp/js/iderp_web.js"
]

web_include_css = [
    "/assets/iderp/css/ecommerce_styles.css"
]

# Override DocType Classes per customizzazioni avanzate
override_doctype_class = {
    "Item": "iderp.overrides.CustomItem",
    "Quotation": "iderp.overrides.CustomQuotation"
}

# Permission Queries per sicurezza avanzata
permission_query_conditions = {
    "Item": "iderp.permissions.get_item_permission_query_conditions"
}

has_permission = {
    "Item": "iderp.permissions.has_item_permission"
}

# Jinja Filters per template
jinja = {
    "methods": [
        "iderp.utils.get_measurement_options",
        "iderp.utils.format_price_with_measurement",
        "iderp.optional_pricing.get_optional_price",  # AGGIUNGI
        "iderp.optional_pricing.format_optional_price"  # AGGIUNGI
    ],
    "filters": [
        "iderp.optional_pricing.optional_price"  # AGGIUNGI
    ]
}

# Regional Settings Italia
country = "Italy"
currency = "EUR"
timezone = "Europe/Rome"

# Development mode settings
# if frappe.conf.get("developer_mode"):
#     doctype_js.update({
#         "Item": [
#             "public/js/item_config.js",
#             "public/js/item_debug.js"
#         ]
#     })

# Error logging specifico iderp
log_clearing_doctypes = {
    "Error Log": 30  # Mantieni 30 giorni di log errori
}

# Translation
default_mail_footer = """
<div style="text-align: center; margin-top: 20px; color: #888;">
    <small>Powered by iderp - Sistema Stampa Digitale v{version}</small>
</div>
""".format(version=app_version)

# Data Import Templates
data_import_tool = [
    {
        "module": "iderp",
        "doctype": "Item",
        "template": "iderp_item_template.xlsx"
    },
    {
        "module": "iderp", 
        "doctype": "Customer",
        "template": "iderp_customer_template.xlsx"
    }
]

# Workspace configuration
standard_portal_menu_items = [
    {
        "title": "Configuratore Prodotti",
        "route": "/iderp-calculator",
        "reference_doctype": "Item",
        "role": "Customer"
    }
]

# Performance monitoring
benchmarks = {
    "pricing_calculation": {
        "method": "iderp.pricing_utils.calculate_universal_item_pricing",
        "threshold": 1.0  # 1 secondo max
    }
}

def boot_session(bootinfo):
    """Add iderp data to boot session"""
    if frappe.session.user != "Guest":
        try:
            bootinfo.iderp = {
                "version": app_version,
                "system_status": get_system_status()
            }
        except Exception:
            # Don't break boot if iderp has issues
            pass

def get_system_status():
    """Get iderp system status for client"""
    try:
        configured_items = frappe.db.count("Item", {"supports_custom_measurement": 1})
        customer_groups = frappe.db.count("Customer Group", 
            {"name": ["in", ["Finale", "Bronze", "Gold", "Diamond"]]})
        
        return {
            "configured_items": configured_items,
            "customer_groups": customer_groups,
            "ready": configured_items > 0 and customer_groups > 0
        }
    except Exception:
        return {"ready": False}
