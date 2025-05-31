app_name = "iderp"
app_title = "iderp"
app_publisher = "idstudio AI"
app_description = "Custom app for ERPNext with e-commerce support"
app_email = "ai@idstudio.org"
app_license = "MIT"

# JavaScript per backend ERPNext
doctype_js = {
    "Quotation": "public/js/item_dimension.js",
    "Sales Order": "public/js/item_dimension.js",
    "Sales Invoice": "public/js/item_dimension.js",
    "Delivery Note": "public/js/item_dimension.js",
    "Work Order": "public/js/item_dimension.js",
    "Item": "public/js/item_config.js"
}

# JavaScript per frontend e-commerce (website)
web_include_js = [
    "/assets/iderp/js/ecommerce_calculator.js"
]

web_include_css = [
    "/assets/iderp/css/ecommerce_styles.css"
]

# Eventi server-side
doc_events = {
    "Quotation": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    "Sales Order": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    "Delivery Note": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    "Sales Invoice": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    
    # Eventi per e-commerce
    "Shopping Cart": {"validate": "iderp.ecommerce.validate_cart_item"},
    "Website Item": {"on_update": "iderp.ecommerce.extend_website_item_context"}
}

# Hook per estendere contesto website
website_context = {
    "extend_website_context": ["iderp.ecommerce.extend_website_item_context"]
}

# Installazione automatica
after_install = "iderp.install.after_install"

# Whitelist API methods per e-commerce
whitelisted_methods = [
    "iderp.ecommerce.calculate_item_price",
    "iderp.ecommerce.add_to_cart_calculated", 
    "iderp.ecommerce.get_item_selling_config"
]

# Override template per pagina prodotto (opzionale)
website_route_rules = [
    {
        "from_route": "/shop/product/<item_code>",
        "to_route": "iderp_product_page"
    }
]

# Custom print formats per documenti di vendita
fixtures = [
    {
        "doctype": "Print Format",
        "filters": {"name": ["in", ["IDERP Sales Order", "IDERP Quotation", "IDERP Invoice"]]}
    }
]

# Permessi aggiuntivi per guest users (e-commerce)
has_website_permission = {
    "Item": "iderp.ecommerce.has_website_permission_for_item"
}

# Standard portal menu items per clienti
standard_portal_menu_items = [
    {
        "title": "I Miei Ordini Personalizzati",
        "route": "/my-custom-orders",
        "reference_doctype": "Sales Order",
        "role": "Customer"
    }
]

# Scheduler per e-commerce (opzionale per future estensioni)
scheduler_events = {
    "hourly": [
        "iderp.ecommerce.cleanup_abandoned_carts"
    ],
    "daily": [
        "iderp.ecommerce.update_product_configurations"
    ]
}

# Jinja helpers per template
jinja = {
    "methods": [
        "iderp.ecommerce.get_measurement_options",
        "iderp.ecommerce.format_price_with_measurement"
    ]
}

# Override website list per prodotti
website_generators = [
    "Website Item"
]

# Boot session data per frontend
boot_session = [
    "iderp.ecommerce.boot_ecommerce_session"
]