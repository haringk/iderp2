app_name = "iderp"
app_title = "iderp"
app_publisher = "idstudio AI"
app_description = "Custom app for ERPNext with multi-unit sales and customer group pricing"
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

# CSS per backend
app_include_css = [
    "/assets/iderp/css/iderp.css"
]

# JavaScript e CSS per frontend e-commerce (website)
web_include_js = [
    "/assets/iderp/js/ecommerce_calculator.js"
]

web_include_css = [
    "/assets/iderp/css/ecommerce_styles.css"
]


# UNICA SEZIONE doc_events - UNIFICATA E CORRETTA
doc_events = {
    "Quotation": {
        "before_submit": "iderp.copy_fields.copy_custom_fields",
        "before_save": "iderp.server_side_minimums.apply_customer_group_minimums_server_side",
        "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
    },
    "Sales Order": {
        "before_submit": "iderp.copy_fields.copy_custom_fields", 
        "before_save": "iderp.server_side_minimums.apply_customer_group_minimums_server_side",
        "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
    },
    "Sales Invoice": {
        "before_submit": "iderp.copy_fields.copy_custom_fields",
        "before_save": "iderp.server_side_minimums.apply_customer_group_minimums_server_side",
        "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
    },
    "Delivery Note": {
        "before_submit": "iderp.copy_fields.copy_custom_fields",
        "before_save": "iderp.server_side_minimums.apply_customer_group_minimums_server_side",
        "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
    },
    "Item": {
        "validate": "iderp.pricing_utils.validate_pricing_tiers"
    }
}

# Whitelist API methods per Customer Group Pricing
whitelisted_methods = [
    "iderp.pricing_utils.get_item_pricing_tiers",
    "iderp.pricing_utils.calculate_item_pricing",
    "iderp.pricing_utils.get_customer_group_min_sqm",
    "iderp.customer_group_pricing.get_customer_group_pricing",
    "iderp.customer_group_pricing.get_customer_specific_price_for_sqm"
]

# Installazione automatica
after_install = "iderp.install.after_install"

# ===== SEZIONE E-COMMERCE (DA ABILITARE GRADUALMENTE) =====

# Questi hook verranno abilitati man mano che implementiamo le funzionalità

# Eventi per e-commerce (commentati per ora)
# doc_events.update({
#     "Shopping Cart": {"validate": "iderp.ecommerce.validate_cart_item"},
#     "Website Item": {"on_update": "iderp.ecommerce.extend_website_item_context"}
# })

# Hook per estendere contesto website
# website_context = {
#     "extend_website_context": ["iderp.ecommerce.extend_website_item_context"]
# }

# Override template per pagina prodotto
# website_route_rules = [
#     {
#         "from_route": "/shop/product/<item_code>",
#         "to_route": "iderp_product_page"
#     }
# ]

# Jinja helpers per template
# jinja = {
#     "methods": [
#         "iderp.ecommerce.get_measurement_options",
#         "iderp.ecommerce.format_price_with_measurement"
#     ]
# }

# Custom print formats
# fixtures = [
#     {
#         "doctype": "Print Format",
#         "filters": {"name": ["in", ["IDERP Sales Order", "IDERP Quotation", "IDERP Invoice"]]}
#     }
# ]

# Portal menu items per clienti
# standard_portal_menu_items = [
#     {
#         "title": "I Miei Ordini Personalizzati",
#         "route": "/my-custom-orders",
#         "reference_doctype": "Sales Order",
#         "role": "Customer"
#     }
# ]

# Scheduler per e-commerce
# scheduler_events = {
#     "hourly": [
#         "iderp.ecommerce.cleanup_abandoned_carts"
#     ],
#     "daily": [
#         "iderp.ecommerce.update_product_configurations"
#     ]
# }

# Permessi per guest users
# has_website_permission = {
#     "Item": "iderp.ecommerce.has_website_permission_for_item"
# }