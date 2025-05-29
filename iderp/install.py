import frappe

def after_install():
    doctypes = [
        "Quotation Item",
        "Sales Order Item",
        "Delivery Note Item",
        "Sales Invoice Item",
        "Purchase Order Item",
        "Purchase Invoice Item",
        "Material Request Item",
    ]
    custom_fields = [
        {
            "fieldname": "base",
            "label": "Base (cm)",
            "fieldtype": "Float",
            "insert_after": "item_code",
            "precision": 2,
        },
        {
            "fieldname": "altezza",
            "label": "Altezza (cm)",
            "fieldtype": "Float",
            "insert_after": "base",
            "precision": 2,
        },
        {
            "fieldname": "prezzo_mq",
            "label": "Prezzo al Mq",
            "fieldtype": "Currency",
            "insert_after": "rate",
        },
        {
            "fieldname": "mq_calcolati",
            "label": "Metri quadri",
            "fieldtype": "Float",
            "insert_after": "altezza",
            "precision": 3,
            "read_only": 1,
            "description": "Base x Altezza / 1000000",
        },
    ]
    for dt in doctypes:
        for cf in custom_fields:
            if not frappe.db.exists("Custom Field", {"dt": dt, "fieldname": cf["fieldname"]}):
                cf_doc = frappe.get_doc({
                    "doctype": "Custom Field",
                    "dt": dt,
                    **cf
                })
                cf_doc.insert(ignore_permissions=True)
