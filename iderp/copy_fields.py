import frappe

def copy_custom_fields(doc, method=None):
    # Campi custom da copiare
    fields = ["base", "altezza", "prezzo_mq", "mq_calcolati"]
    if not hasattr(doc, "items"):
        return
    for item in doc.items:
        if hasattr(item, "linked_document_type") and hasattr(item, "linked_document_name"):
            try:
                prev = frappe.get_doc(item.linked_document_type, item.linked_document_name)
                for f in fields:
                    if hasattr(prev, f) and hasattr(item, f):
                        setattr(item, f, getattr(prev, f, None))
            except Exception:
                continue
        # Ricalcolo mq in automatico
        try:
            if getattr(item, "base", None) and getattr(item, "altezza", None):
                item.mq_calcolati = (float(item.base) * float(item.altezza)) / 10000
        except Exception:
            pass
