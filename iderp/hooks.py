# iderp/hooks.py

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
#    "Item": "public/js/item_config.js"
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

# HOOK VALIDAZIONE TEMPORANEAMENTE DISABILITATO
# doc_events = {
#     "Quotation": {
#         "before_submit": "iderp.copy_fields.copy_custom_fields",
#         "before_save": "iderp.universal_pricing.apply_universal_pricing_server_side",
#         "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
#     },
#     "Sales Order": {
#         "before_submit": "iderp.copy_fields.copy_custom_fields", 
#         "before_save": "iderp.universal_pricing.apply_universal_pricing_server_side",
#         "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
#     },
#     "Sales Invoice": {
#         "before_submit": "iderp.copy_fields.copy_custom_fields",
#         "before_save": "iderp.universal_pricing.apply_universal_pricing_server_side",
#         "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
#     },
#     "Delivery Note": {
#         "before_submit": "iderp.copy_fields.copy_custom_fields",
#         "before_save": "iderp.universal_pricing.apply_universal_pricing_server_side",
#         "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
#     },
#     "Item": {
#         "validate": "iderp.pricing_utils.validate_pricing_tiers"  # <-- QUESTO BLOCCA IL SALVATAGGIO
#     }
# }

# VERSIONE RIDOTTA SENZA VALIDAZIONE ITEM
doc_events = {
    "Quotation": {
        "before_submit": "iderp.copy_fields.copy_custom_fields",
        "before_save": "iderp.universal_pricing.apply_universal_pricing_server_side",
        "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
    },
    "Sales Order": {
        "before_submit": "iderp.copy_fields.copy_custom_fields", 
        "before_save": "iderp.universal_pricing.apply_universal_pricing_server_side",
        "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
    },
    "Sales Invoice": {
        "before_submit": "iderp.copy_fields.copy_custom_fields",
        "before_save": "iderp.universal_pricing.apply_universal_pricing_server_side",
        "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
    },
    "Delivery Note": {
        "before_submit": "iderp.copy_fields.copy_custom_fields",
        "before_save": "iderp.universal_pricing.apply_universal_pricing_server_side",
        "validate": "iderp.server_side_minimums.calculate_standard_square_meters_server_side"
    }
    # ITEM VALIDATION RIMOSSA TEMPORANEAMENTE
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