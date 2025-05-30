app_name = "iderp"
app_title = "iderp"
app_publisher = "idstudio AI"
app_description = "Custom app for ERPNext"
app_email = "ai@idstudio.org"
app_license = "MIT"

app_include_js = "/assets/iderp/js/item_dimension.js"

app_include_js = "/assets/iderp/js/iderp.js"
app_include_css = "/assets/iderp/css/iderp.css"

doctype_js = {
    "Quotation": "iderp/public/js/item_dimension.js",
    "Sales Order": "iderp/public/js/item_dimension.js",
	"Sales Invoice": "iderp/public/js/item_dimension.js",
	"Delivery Note": "iderp/public/js/item_dimension.js",
	"Work Order": "iderp/public/js/item_dimension.js",
	"Web Order": "iderp/public/js/item_dimension.js",
	# ...ecc.
}

doc_events = {
    "Quotation": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    "Sales Order": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    "Delivery Note": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    "Sales Invoice": {"before_submit": "iderp.copy_fields.copy_custom_fields"},
    # Aggiungi altri DocType se necessario
}

# Esegui la creazione dei campi custom automaticamente
after_install = "iderp.install.after_install"