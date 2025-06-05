# iderp/api/optional.py

"""
API REST per gestione optional
Sistema stampa digitale IDERP - ERPNext 15
"""

import frappe
from frappe import _
from frappe.utils import flt, cint
import json

@frappe.whitelist()
def get_item_optionals(item_code):
    """
    Ottieni tutti gli optional applicabili per un articolo
    
    Args:
        item_code: Codice articolo
        
    Returns:
        Lista di optional applicabili con dettagli prezzi
    """
    if not frappe.has_permission("Item", "read"):
        frappe.throw(_("Permesso negato"), frappe.PermissionError)
    
    # Query optional attivi
    optionals = frappe.get_all("Item Optional",
        filters={"enabled": 1},
        fields=["name", "optional_name", "description", "pricing_type", "price"]
    )
    
    applicable_optionals = []
    
    for opt in optionals:
        # Verifica applicabilità
        if is_optional_applicable(opt.name, item_code):
            applicable_optionals.append({
                "optional": opt.name,
                "optional_name": opt.optional_name,
                "description": opt.description or opt.optional_name,
                "pricing_type": opt.pricing_type,
                "price": opt.price,
                "formatted_price": format_optional_price_display(opt)
            })
    
    return {
        "success": True,
        "optionals": applicable_optionals,
        "count": len(applicable_optionals)
    }


def is_optional_applicable(optional_name, item_code):
    """
    Verifica se un optional è applicabile a un articolo
    """
    opt_doc = frappe.get_doc("Item Optional", optional_name)
    
    # Se non ci sono regole, è applicabile a tutti
    if not opt_doc.applicable_for:
        return True
    
    # Verifica regole
    for rule in opt_doc.applicable_for:
        # Tutti gli articoli
        if rule.all_items:
            return True
        
        # Articolo specifico
        if rule.item_code == item_code:
            return True
        
        # Gruppo articoli
        if rule.item_group:
            item_group = frappe.db.get_value("Item", item_code, "item_group")
            if rule.item_group == item_group:
                return True
    
    return False


def format_optional_price_display(opt):
    """
    Formatta prezzo per visualizzazione UI
    """
    currency = frappe.db.get_default("currency")
    
    if opt.pricing_type == "Fisso":
        return frappe.utils.fmt_money(opt.price, currency=currency)
    elif opt.pricing_type == "Percentuale":
        return f"{opt.price}%"
    elif opt.pricing_type == "Per Metro Quadrato":
        return f"{frappe.utils.fmt_money(opt.price, currency=currency)}/m²"
    elif opt.pricing_type == "Per Metro Lineare":
        return f"{frappe.utils.fmt_money(opt.price, currency=currency)}/ml"
    
    return str(opt.price)


@frappe.whitelist()
def apply_template(template_name, doctype, docname, item_idx):
    """
    Applica template optional a riga documento
    
    Args:
        template_name: Nome del template
        doctype: Tipo documento (Quotation, Sales Order, etc)
        docname: Nome documento
        item_idx: Indice riga articolo (1-based)
    """
    if not frappe.has_permission(doctype, "write", docname):
        frappe.throw(_("Permesso negato"), frappe.PermissionError)
    
    try:
        template = frappe.get_doc("Optional Template", template_name)
        doc = frappe.get_doc(doctype, docname)
        
        # Trova riga
        item_idx = cint(item_idx) - 1
        if item_idx < 0 or item_idx >= len(doc.items):
            frappe.throw(_("Indice riga non valido"))
        
        item_row = doc.items[item_idx]
        
        # Verifica compatibilità
        if item_row.item_code != template.item_code:
            frappe.throw(_("Template non compatibile con l'articolo selezionato"))
        
        # Pulisci optional esistenti
        if hasattr(item_row, 'item_optionals'):
            item_row.item_optionals = []
        
        # Applica optional dal template
        applied_count = 0
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
                applied_count += 1
        
        # Salva documento
        doc.save()
        
        return {
            "success": True,
            "message": _("Template '{0}' applicato: {1} optional aggiunti").format(
                template.template_name, applied_count
            ),
            "applied_count": applied_count
        }
        
    except Exception as e:
        frappe.log_error(f"Errore applicazione template: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist()
def calculate_optional_price(optional, base_amount, quantity, extra_params=None):
    """
    Calcola prezzo di un optional
    
    Args:
        optional: Nome optional
        base_amount: Importo base per calcoli percentuali
        quantity: Quantità (m², ml, pezzi)
        extra_params: Parametri aggiuntivi (dict as JSON string)
    """
    try:
        if isinstance(extra_params, str):
            extra_params = json.loads(extra_params) if extra_params else {}
        
        opt_doc = frappe.get_doc("Item Optional", optional)
        
        price = 0
        
        if opt_doc.pricing_type == "Fisso":
            price = flt(opt_doc.price) * flt(quantity)
            
        elif opt_doc.pricing_type == "Percentuale":
            price = flt(base_amount) * flt(opt_doc.price) / 100
            
        elif opt_doc.pricing_type == "Per Metro Quadrato":
            mq = flt(extra_params.get('mq_calcolati', quantity))
            price = flt(opt_doc.price) * mq
            
        elif opt_doc.pricing_type == "Per Metro Lineare":
            ml = flt(extra_params.get('ml_calcolati', quantity))
            price = flt(opt_doc.price) * ml
        
        return {
            "success": True,
            "price": price,
            "formatted_price": frappe.utils.fmt_money(price),
            "pricing_type": opt_doc.pricing_type,
            "unit_price": opt_doc.price
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "price": 0
        }


@frappe.whitelist()
def get_optional_summary(doctype, docname):
    """
    Ottieni riepilogo dettagliato optional documento
    """
    if not frappe.has_permission(doctype, "read", docname):
        frappe.throw(_("Permesso negato"), frappe.PermissionError)
    
    doc = frappe.get_doc(doctype, docname)
    
    # Raccogli dati optional
    optional_data = {}
    total_amount = 0
    items_with_optionals = 0
    
    if hasattr(doc, 'items'):
        for item in doc.items:
            if hasattr(item, 'item_optionals') and item.item_optionals:
                items_with_optionals += 1
                
                for opt in item.item_optionals:
                    if opt.optional not in optional_data:
                        optional_data[opt.optional] = {
                            "optional": opt.optional,
                            "description": opt.description,
                            "pricing_type": opt.pricing_type,
                            "unit_price": opt.unit_price,
                            "total_qty": 0,
                            "total_amount": 0,
                            "occurrences": [],
                            "formatted_unit_price": format_price_by_type(
                                opt.unit_price, opt.pricing_type
                            )
                        }
                    
                    optional_data[opt.optional]["total_qty"] += flt(opt.quantity)
                    optional_data[opt.optional]["total_amount"] += flt(opt.total_price)
                    optional_data[opt.optional]["occurrences"].append({
                        "item_code": item.item_code,
                        "item_name": item.item_name,
                        "idx": item.idx,
                        "qty": opt.quantity,
                        "amount": opt.total_price
                    })
                    
                    total_amount += flt(opt.total_price)
    
    # Prepara risposta
    summary = list(optional_data.values())
    
    # Ordina per importo totale decrescente
    summary.sort(key=lambda x: x["total_amount"], reverse=True)
    
    return {
        "success": True,
        "summary": summary,
        "total_amount": total_amount,
        "formatted_total": frappe.utils.fmt_money(total_amount),
        "items_with_optionals": items_with_optionals,
        "unique_optionals": len(summary),
        "currency": frappe.db.get_default("currency")
    }


def format_price_by_type(price, pricing_type):
    """
    Formatta prezzo in base al tipo
    """
    currency = frappe.db.get_default("currency")
    
    if pricing_type == "Percentuale":
        return f"{price}%"
    elif pricing_type == "Per Metro Quadrato":
        return f"{frappe.utils.fmt_money(price, currency=currency)}/m²"
    elif pricing_type == "Per Metro Lineare":
        return f"{frappe.utils.fmt_money(price, currency=currency)}/ml"
    else:
        return frappe.utils.fmt_money(price, currency=currency)


@frappe.whitelist()
def toggle_optional(doctype, docname, item_idx, optional_name, action="add"):
    """
    Aggiungi o rimuovi optional da riga
    
    Args:
        action: 'add' o 'remove'
    """
    if not frappe.has_permission(doctype, "write", docname):
        frappe.throw(_("Permesso negato"), frappe.PermissionError)
    
    try:
        doc = frappe.get_doc(doctype, docname)
        item_idx = cint(item_idx) - 1
        
        if item_idx < 0 or item_idx >= len(doc.items):
            frappe.throw(_("Indice riga non valido"))
        
        item_row = doc.items[item_idx]
        
        if action == "add":
            # Verifica che non sia già presente
            for opt in item_row.get('item_optionals', []):
                if opt.optional == optional_name:
                    return {
                        "success": False,
                        "message": _("Optional già presente")
                    }
            
            # Aggiungi optional
            opt_doc = frappe.get_doc("Item Optional", optional_name)
            
            if not hasattr(item_row, 'item_optionals'):
                item_row.item_optionals = []
            
            item_row.append('item_optionals', {
                'optional': optional_name,
                'description': opt_doc.description,
                'pricing_type': opt_doc.pricing_type,
                'unit_price': opt_doc.price,
                'quantity': 1
            })
            
            message = _("Optional aggiunto")
            
        elif action == "remove":
            # Rimuovi optional
            if hasattr(item_row, 'item_optionals'):
                item_row.item_optionals = [
                    opt for opt in item_row.item_optionals 
                    if opt.optional != optional_name
                ]
            
            message = _("Optional rimosso")
        
        else:
            frappe.throw(_("Azione non valida"))
        
        # Salva documento
        doc.save()
        
        return {
            "success": True,
            "message": message
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist()
def get_templates_for_item(item_code):
    """
    Ottieni template disponibili per articolo
    """
    templates = frappe.get_all("Optional Template",
        filters={"item_code": item_code},
        fields=["name", "template_name", "is_default"],
        order_by="is_default desc, creation desc"
    )
    
    # Aggiungi dettagli optional per ogni template
    for template in templates:
        template_doc = frappe.get_doc("Optional Template", template.name)
        template["optionals_count"] = len(template_doc.optionals)
        template["mandatory_count"] = sum(
            1 for opt in template_doc.optionals if opt.is_mandatory
        )
    
    return {
        "success": True,
        "templates": templates
    }
