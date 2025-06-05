# -*- coding: utf-8 -*-
# Copyright (c) 2024, ID Studio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint


@frappe.whitelist()
def get_item_details(item_code, customer=None, company=None):
    """
    Recupera dettagli articolo inclusi base, altezza e prezzo personalizzato
    
    Args:
        item_code: Codice articolo
        customer: Cliente (opzionale) per prezzi personalizzati
        company: Azienda
        
    Returns:
        dict: Dettagli articolo
    """
    if not item_code:
        return {}
        
    # Recupera dettagli base articolo
    item = frappe.get_doc("Item", item_code)
    
    # Prepara risposta base
    details = {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "description": item.description,
        "stock_uom": item.stock_uom,
        "uom": item.stock_uom,
        "conversion_factor": 1.0,
        "base": 0,
        "altezza": 0,
        "rate": 0
    }
    
    # Recupera dimensioni predefinite se esistono
    if frappe.db.exists("Item", {"name": item_code}):
        dimensions = frappe.db.get_value(
            "Item",
            item_code,
            ["base_default", "altezza_default"],
            as_dict=True
        )
        
        if dimensions:
            details["base"] = flt(dimensions.get("base_default", 0))
            details["altezza"] = flt(dimensions.get("altezza_default", 0))
    
    # Se c'è un cliente, cerca prezzi personalizzati
    if customer:
        price = get_customer_item_price(item_code, customer, company)
        if price:
            details["rate"] = price
    else:
        # Prezzo standard
        price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
        if price_list:
            price = frappe.db.get_value(
                "Item Price",
                {
                    "item_code": item_code,
                    "price_list": price_list,
                    "selling": 1
                },
                "price_list_rate"
            )
            if price:
                details["rate"] = flt(price)
    
    return details


@frappe.whitelist()
def get_customer_item_price(item_code, customer, company=None):
    """
    Ottiene il prezzo articolo per un cliente specifico considerando:
    1. Prezzi specifici per cliente
    2. Prezzi per gruppo cliente
    3. Regole prezzo attive
    
    Args:
        item_code: Codice articolo
        customer: Cliente
        company: Azienda (opzionale)
        
    Returns:
        float: Prezzo articolo
    """
    if not item_code or not customer:
        return 0
        
    # 1. Cerca prezzo specifico per cliente
    customer_price = frappe.db.get_value(
        "Item Price",
        {
            "item_code": item_code,
            "customer": customer,
            "selling": 1
        },
        "price_list_rate"
    )
    
    if customer_price:
        return flt(customer_price)
    
    # 2. Recupera gruppo cliente
    customer_group = frappe.db.get_value("Customer", customer, "customer_group")
    
    if customer_group:
        # Cerca nelle regole prezzo gruppo cliente (DocType personalizzato)
        group_price = frappe.db.sql("""
            SELECT igpr.price
            FROM `tabItem Group Price Rule` igpr
            INNER JOIN `tabCustomer Group Price Rule` cgpr ON cgpr.name = igpr.parent
            WHERE cgpr.customer_group = %s
            AND igpr.item_code = %s
            AND cgpr.is_active = 1
            ORDER BY cgpr.priority DESC
            LIMIT 1
        """, (customer_group, item_code), as_dict=True)
        
        if group_price and group_price[0].get("price"):
            return flt(group_price[0]["price"])
        
        # Cerca prezzo standard per gruppo cliente
        group_standard_price = frappe.db.get_value(
            "Item Price",
            {
                "item_code": item_code,
                "customer_group": customer_group,
                "selling": 1
            },
            "price_list_rate"
        )
        
        if group_standard_price:
            return flt(group_standard_price)
    
    # 3. Prezzo di listino predefinito
    default_price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
    if default_price_list:
        default_price = frappe.db.get_value(
            "Item Price",
            {
                "item_code": item_code,
                "price_list": default_price_list,
                "selling": 1
            },
            "price_list_rate"
        )
        
        if default_price:
            return flt(default_price)
    
    # 4. Ultimo tentativo - prezzo da scheda articolo
    return flt(frappe.db.get_value("Item", item_code, "standard_rate") or 0)


@frappe.whitelist()
def calculate_item_metrics(base_mm, altezza_mm, qty=1, uom="Mq"):
    """
    Calcola metriche articolo (mq, metri lineari, ecc)
    
    Args:
        base_mm: Base in millimetri
        altezza_mm: Altezza in millimetri  
        qty: Quantità
        uom: Unità di misura
        
    Returns:
        dict: Metriche calcolate
    """
    base_mm = flt(base_mm)
    altezza_mm = flt(altezza_mm)
    qty = flt(qty) or 1
    
    metrics = {
        "base_m": base_mm / 1000,
        "altezza_m": altezza_mm / 1000,
        "mq_unitari": 0,
        "mq_totali": 0,
        "metri_lineari": 0
    }
    
    if uom == "Mq" and base_mm > 0 and altezza_mm > 0:
        # Calcolo metri quadri
        metrics["mq_unitari"] = metrics["base_m"] * metrics["altezza_m"]
        metrics["mq_totali"] = metrics["mq_unitari"] * qty
        
    elif uom == "Metro" and (base_mm > 0 or altezza_mm > 0):
        # Calcolo metri lineari (usa la dimensione maggiore)
        max_dimension = max(base_mm, altezza_mm) / 1000
        metrics["metri_lineari"] = max_dimension * qty
    
    return metrics


@frappe.whitelist()
def validate_item_dimensions(item_code, base_mm, altezza_mm):
    """
    Valida che le dimensioni rientrino nei limiti dell'articolo
    
    Args:
        item_code: Codice articolo
        base_mm: Base in millimetri
        altezza_mm: Altezza in millimetri
        
    Returns:
        dict: Risultato validazione con eventuali errori
    """
    if not item_code:
        return {"valid": False, "message": _("Codice articolo mancante")}
        
    # Recupera limiti dimensionali se configurati
    limits = frappe.db.get_value(
        "Item",
        item_code,
        ["min_base", "max_base", "min_altezza", "max_altezza"],
        as_dict=True
    )
    
    if not limits:
        return {"valid": True}
        
    base_mm = flt(base_mm)
    altezza_mm = flt(altezza_mm)
    errors = []
    
    # Valida base
    if limits.get("min_base") and base_mm < limits["min_base"]:
        errors.append(_("Base minima: {0}mm").format(limits["min_base"]))
        
    if limits.get("max_base") and base_mm > limits["max_base"]:
        errors.append(_("Base massima: {0}mm").format(limits["max_base"]))
        
    # Valida altezza
    if limits.get("min_altezza") and altezza_mm < limits["min_altezza"]:
        errors.append(_("Altezza minima: {0}mm").format(limits["min_altezza"]))
        
    if limits.get("max_altezza") and altezza_mm > limits["max_altezza"]:
        errors.append(_("Altezza massima: {0}mm").format(limits["max_altezza"]))
    
    if errors:
        return {
            "valid": False,
            "message": _("Dimensioni non valide per {0}:").format(item_code) + " " + ", ".join(errors)
        }
    
    return {"valid": True}


@frappe.whitelist()
def get_item_optionals(item_code):
    """
    Recupera articoli opzionali associati all'articolo
    
    Args:
        item_code: Codice articolo principale
        
    Returns:
        list: Lista articoli opzionali
    """
    if not item_code:
        return []
        
    optionals = frappe.db.sql("""
        SELECT 
            io.optional_item_code,
            io.optional_item_name,
            io.default_qty,
            io.is_mandatory,
            io.price_rule,
            i.stock_uom,
            i.description
        FROM `tabItem Optional` io
        INNER JOIN `tabItem` i ON i.name = io.optional_item_code
        WHERE io.parent = %s
        AND io.is_active = 1
        ORDER BY io.display_order, io.optional_item_name
    """, item_code, as_dict=True)
    
    # Aggiungi prezzi per ogni opzionale
    for opt in optionals:
        opt["rate"] = get_optional_item_price(
            opt["optional_item_code"],
            opt.get("price_rule")
        )
    
    return optionals


def get_optional_item_price(item_code, price_rule=None):
    """Recupera prezzo articolo opzionale"""
    if price_rule == "Free":
        return 0
    elif price_rule == "50% Discount":
        base_price = flt(frappe.db.get_value("Item", item_code, "standard_rate"))
        return base_price * 0.5
    else:
        return flt(frappe.db.get_value("Item", item_code, "standard_rate"))
