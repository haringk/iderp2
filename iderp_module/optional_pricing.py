# iderp/optional_pricing.py

"""
Modulo per gestione calcolo prezzi optional
Sistema stampa digitale iderp - ERPNext 15
"""

import frappe
from frappe import _
from frappe.utils import flt, cint
import json

def calculate_optional_totals(doc, method=None):
    """
    Calcola totali optional per documenti vendita
    Hook chiamato su validate
    """
    if not hasattr(doc, 'items'):
        return
    
    total_optional_amount = 0
    
    for item in doc.items:
        if hasattr(item, 'item_optionals') and item.item_optionals:
            item_optional_total = 0
            
            for opt in item.item_optionals:
                # Calcola prezzo singolo optional
                opt.total_price = calculate_single_optional_price(opt, item, doc)
                item_optional_total += flt(opt.total_price)
            
            # Aggiorna totale optional sulla riga
            if hasattr(item, 'optional_total'):
                item.optional_total = item_optional_total
            
            total_optional_amount += item_optional_total
    
    # Salva totale documento se campo disponibile
    if hasattr(doc, 'total_optional_amount'):
        doc.total_optional_amount = total_optional_amount
    
    # Log per debug
    if total_optional_amount > 0:
        frappe.logger().info(f"Totale optional calcolato per {doc.doctype} {doc.name}: €{total_optional_amount}")


def calculate_single_optional_price(optional_row, item_row, parent_doc):
    """
    Calcola prezzo singolo optional basato sul tipo di pricing
    """
    if not optional_row.optional:
        return 0
    
    try:
        # Carica dettagli optional
        opt_doc = frappe.get_cached_doc("Item Optional", optional_row.optional)
        
        # Imposta dettagli se mancanti
        if not optional_row.pricing_type:
            optional_row.pricing_type = opt_doc.pricing_type
        if not optional_row.unit_price:
            optional_row.unit_price = opt_doc.price
        
        # Calcola in base al tipo
        if optional_row.pricing_type == "Fisso":
            return flt(optional_row.unit_price) * flt(optional_row.quantity or 1)
        
        elif optional_row.pricing_type == "Percentuale":
            # Percentuale sul valore riga
            base_amount = flt(item_row.rate) * flt(item_row.qty)
            return base_amount * flt(optional_row.unit_price) / 100
        
        elif optional_row.pricing_type == "Per Metro Quadrato":
            # Usa m² calcolati o quantità
            mq = flt(getattr(item_row, 'mq_calcolati', 0)) or flt(optional_row.quantity or 1)
            return flt(optional_row.unit_price) * mq
        
        elif optional_row.pricing_type == "Per Metro Lineare":
            # Usa ml calcolati o quantità
            ml = flt(getattr(item_row, 'ml_calcolati', 0)) or flt(optional_row.quantity or 1)
            return flt(optional_row.unit_price) * ml
        
        else:
            return flt(optional_row.unit_price) * flt(optional_row.quantity or 1)
            
    except Exception as e:
        frappe.log_error(f"Errore calcolo optional {optional_row.optional}: {str(e)}")
        return 0


def update_optional_totals(doc, method=None):
    """
    Aggiorna totali optional dopo salvataggio
    Hook chiamato su on_update
    """
    # Aggiorna totale documento se necessario
    if hasattr(doc, 'grand_total') and hasattr(doc, 'total_optional_amount'):
        # Il grand_total dovrebbe già includere gli optional
        # Questa funzione serve per tracking/reporting
        pass


def validate_optional(doc, method=None):
    """
    Validazioni per Item Optional
    """
    # Valida tipo prezzo e valore
    if doc.pricing_type == "Percentuale" and flt(doc.price) > 100:
        frappe.throw(_("Per tipo Percentuale, il valore non può superare 100"))
    
    if flt(doc.price) <= 0:
        frappe.throw(_("Il prezzo/valore deve essere maggiore di zero"))
    
    # Valida applicabilità
    validate_optional_applicability(doc)


def validate_optional_applicability(doc):
    """
    Valida regole di applicabilità optional
    """
    if not doc.applicable_for:
        return
    
    all_items_count = sum(1 for row in doc.applicable_for if row.all_items)
    
    if all_items_count > 1:
        frappe.throw(_("Puoi avere solo una riga con 'Tutti gli Articoli' selezionato"))
    
    if all_items_count == 1 and len(doc.applicable_for) > 1:
        frappe.throw(_("Se selezioni 'Tutti gli Articoli', non puoi specificare articoli singoli"))


@frappe.whitelist()
def get_optional_price(optional, pricing_type, base_amount=0, quantity=1):
    """
    API per ottenere prezzo calcolato di un optional
    """
    opt_doc = frappe.get_doc("Item Optional", optional)
    
    if pricing_type == "Fisso":
        return flt(opt_doc.price) * flt(quantity)
    
    elif pricing_type == "Percentuale":
        return flt(base_amount) * flt(opt_doc.price) / 100
    
    elif pricing_type in ["Per Metro Quadrato", "Per Metro Lineare"]:
        return flt(opt_doc.price) * flt(quantity)
    
    return 0


@frappe.whitelist()
def format_optional_price(optional, pricing_type, price):
    """
    Formatta prezzo optional per visualizzazione
    """
    from frappe.utils import fmt_money
    
    if pricing_type == "Fisso":
        return fmt_money(price, currency=frappe.defaults.get_global_default("currency"))
    
    elif pricing_type == "Percentuale":
        return f"{flt(price)}%"
    
    elif pricing_type == "Per Metro Quadrato":
        return f"{fmt_money(price, currency=frappe.defaults.get_global_default('currency'))}/m²"
    
    elif pricing_type == "Per Metro Lineare":
        return f"{fmt_money(price, currency=frappe.defaults.get_global_default('currency'))}/ml"
    
    return fmt_money(price, currency=frappe.defaults.get_global_default("currency"))


def optional_price(value, pricing_type=None):
    """
    Filtro Jinja per formattare prezzi optional
    """
    return format_optional_price(None, pricing_type or "Fisso", value)


@frappe.whitelist()
def apply_optional_template(template_name, parent_doctype, parent_name, item_idx):
    """
    Applica template optional a una riga documento
    """
    template = frappe.get_doc("Optional Template", template_name)
    parent_doc = frappe.get_doc(parent_doctype, parent_name)
    
    # Trova riga item
    item_row = None
    for idx, row in enumerate(parent_doc.items):
        if idx == cint(item_idx) - 1:
            item_row = row
            break
    
    if not item_row:
        frappe.throw(_("Riga articolo non trovata"))
    
    # Verifica compatibilità
    if item_row.item_code != template.item_code:
        frappe.throw(_("Il template è per un articolo diverso"))
    
    # Pulisci optional esistenti
    item_row.item_optionals = []
    
    # Applica optional dal template
    for tpl_opt in template.optionals:
        if tpl_opt.is_mandatory or tpl_opt.default_selected:
            opt_doc = frappe.get_doc("Item Optional", tpl_opt.optional)
            
            item_row.append("item_optionals", {
                "optional": opt_doc.name,
                "description": opt_doc.description,
                "pricing_type": opt_doc.pricing_type,
                "unit_price": opt_doc.price,
                "quantity": 1
            })
    
    # Salva e ricalcola
    parent_doc.save()
    
    return {
        "success": True,
        "message": _("Template applicato con successo")
    }


@frappe.whitelist()
def get_optional_summary(doctype, docname):
    """
    Ottieni riepilogo optional per documento
    """
    doc = frappe.get_doc(doctype, docname)
    
    summary = {}
    total_amount = 0
    
    if hasattr(doc, 'items'):
        for item in doc.items:
            if hasattr(item, 'item_optionals'):
                for opt in item.item_optionals:
                    if opt.optional not in summary:
                        summary[opt.optional] = {
                            "name": opt.optional,
                            "description": opt.description,
                            "pricing_type": opt.pricing_type,
                            "total_qty": 0,
                            "total_amount": 0,
                            "items": []
                        }
                    
                    summary[opt.optional]["total_qty"] += flt(opt.quantity)
                    summary[opt.optional]["total_amount"] += flt(opt.total_price)
                    summary[opt.optional]["items"].append({
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "qty": opt.quantity,
                        "amount": opt.total_price
                    })
                    
                    total_amount += flt(opt.total_price)
    
    return {
        "optionals": list(summary.values()),
        "total_amount": total_amount,
        "currency": frappe.defaults.get_global_default("currency")
    }


def cleanup_optional_orphans():
    """
    Task schedulato per pulizia optional orfani
    """
    # Rimuovi optional da documenti cancellati
    # Implementare se necessario
    pass
