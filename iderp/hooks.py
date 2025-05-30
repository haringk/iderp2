app_name = "iderp"
app_title = "iderp"
app_publisher = "idstudio AI"
app_description = "Custom app for ERPNext"
app_email = "ai@idstudio.org"
app_license = "MIT"

doctype_js = {
    "Quotation": "public/js/item_dimension.js",
    "Sales Order": "public/js/item_dimension.js",
    "Sales Invoice": "public/js/item_dimension.js",
    "Delivery Note": "public/js/item_dimension.js",
    "Work Order": "public/js/item_dimension.js"
}

doc_events = {
    "Quotation": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    "Sales Order": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    "Delivery Note": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    "Sales Invoice": {"before_submit": "iderp.copy_fields.copy_custom_fields"}
}

after_install = "iderp.install.after_install"
