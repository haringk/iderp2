# -*- coding: utf-8 -*-
# Copyright (c) 2024, ID Studio and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, nowdate, getdate
from typing import Dict, List, Optional, Tuple


@frappe.whitelist()
def get_customer_group_price(
    item_code: str,
    customer: str,
    qty: float = 1,
    transaction_date: str = None
) -> Dict:
    """
    Ottiene il prezzo per un articolo basato sul gruppo cliente
    
    Args:
        item_code: Codice articolo
        customer: Cliente
        qty: Quantità (per scaglioni prezzo)
        transaction_date: Data transazione
        
    Returns:
        dict: Prezzo e dettagli regola applicata
    """
    if not item_code or not customer:
        return {}
        
    # Recupera gruppo cliente
    customer_group = frappe.db.get_value("Customer", customer, "customer_group")
    if not customer_group:
        return {}
        
    transaction_date = getdate(transaction_date or nowdate())
    
    # Cerca regole prezzo attive per gruppo cliente
    price_rules = frappe.db.sql("""
        SELECT 
            cgpr.name as rule_name,
            cgpr.priority,
            igpr.price,
            igpr.discount_percentage,
            igpr.min_qty,
            igpr.max_qty
        FROM `tabCustomer Group Price Rule` cgpr
        INNER JOIN `tabItem Group Price Rule` igpr ON igpr.parent = cgpr.name
        WHERE cgpr.customer_group = %s
        AND igpr.item_code = %s
        AND cgpr.is_active = 1
        AND (cgpr.valid_from IS NULL OR cgpr.valid_from <= %s)
        AND (cgpr.valid_to IS NULL OR cgpr.valid_to >= %s)
        AND (igpr.min_qty IS NULL OR igpr.min_qty <= %s)
        AND (igpr.max_qty IS NULL OR igpr.max_qty >= %s)
        ORDER BY cgpr.priority DESC, igpr.min_qty DESC
        LIMIT 1
    """, (customer_group, item_code, transaction_date, transaction_date, qty, qty), as_dict=True)
    
    if price_rules:
        rule = price_rules[0]
        
        # Se c'è uno sconto percentuale, calcola dal prezzo base
        if rule.discount_percentage and not rule.price:
            base_price = get_item_base_price(item_code)
            rule["price"] = base_price * (1 - rule.discount_percentage / 100)
            
        return {
            "price": flt(rule.price, 2),
            "discount_percentage": rule.discount_percentage,
            "rule_name": rule.rule_name,
            "applied": True
        }
    
    # Cerca nei tier di prezzo (scaglioni quantità)
    tier_price = get_item_tier_price(item_code, customer_group, qty)
    if tier_price:
        return tier_price
        
    # Nessuna regola trovata
    return {"applied": False}


def get_item_base_price(item_code: str) -> float:
    """Recupera prezzo base articolo dal listino predefinito"""
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
            return flt(price)
            
    # Fallback su prezzo standard articolo
    return flt(frappe.db.get_value("Item", item_code, "standard_rate") or 0)


def get_item_tier_price(
    item_code: str,
    customer_group: str,
    qty: float
) -> Optional[Dict]:
    """
    Recupera prezzo da fasce quantità (tier pricing)
    
    Args:
        item_code: Codice articolo
        customer_group: Gruppo cliente
        qty: Quantità
        
    Returns:
        dict: Prezzo tier se trovato
    """
    # Cerca tier prezzo attivi
    tiers = frappe.db.sql("""
        SELECT 
            ipt.tier_name,
            ipt.price,
            ipt.discount_percentage
        FROM `tabItem Pricing Tier` ipt
        WHERE ipt.parent = %s
        AND ipt.customer_group = %s
        AND ipt.min_qty <= %s
        AND (ipt.max_qty IS NULL OR ipt.max_qty >= %s)
        AND ipt.is_active = 1
        ORDER BY ipt.min_qty DESC
        LIMIT 1
    """, (item_code, customer_group, qty, qty), as_dict=True)
    
    if tiers:
        tier = tiers[0]
        
        # Calcola prezzo con sconto se necessario
        if tier.discount_percentage and not tier.price:
            base_price = get_item_base_price(item_code)
            tier["price"] = base_price * (1 - tier.discount_percentage / 100)
            
        return {
            "price": flt(tier.price, 2),
            "discount_percentage": tier.discount_percentage,
            "rule_name": f"Tier: {tier.tier_name}",
            "applied": True
        }
        
    return None


@frappe.whitelist()
def apply_customer_group_discounts(
    customer: str,
    items: List[Dict],
    posting_date: str = None
) -> List[Dict]:
    """
    Applica sconti gruppo cliente a lista articoli
    
    Args:
        customer: Cliente
        items: Lista articoli (dict o json)
        posting_date: Data documento
        
    Returns:
        list: Articoli aggiornati con prezzi scontati
    """
    if isinstance(items, str):
        import json
        items = json.loads(items)
        
    if not customer or not items:
        return items
        
    updated_items = []
    
    for item in items:
        if not item.get("item_code"):
            continue
            
        # Ottieni prezzo gruppo
        price_info = get_customer_group_price(
            item["item_code"],
            customer,
            item.get("qty", 1),
            posting_date
        )
        
        if price_info.get("applied"):
            item["rate"] = price_info["price"]
            if price_info.get("discount_percentage"):
                item["discount_percentage"] = price_info["discount_percentage"]
            item["price_rule_applied"] = price_info.get("rule_name")
            
        updated_items.append(item)
        
    return updated_items


@frappe.whitelist()
def get_customer_group_rules(customer_group: str) -> List[Dict]:
    """
    Recupera tutte le regole prezzo attive per un gruppo cliente
    
    Args:
        customer_group: Gruppo cliente
        
    Returns:
        list: Lista regole prezzo
    """
    if not customer_group:
        return []
        
    rules = frappe.db.sql("""
        SELECT 
            cgpr.name,
            cgpr.rule_name,
            cgpr.priority,
            cgpr.valid_from,
            cgpr.valid_to,
            cgpr.description
        FROM `tabCustomer Group Price Rule` cgpr
        WHERE cgpr.customer_group = %s
        AND cgpr.is_active = 1
        ORDER BY cgpr.priority DESC
    """, customer_group, as_dict=True)
    
    # Aggiungi dettagli articoli per ogni regola
    for rule in rules:
        rule["items"] = frappe.db.sql("""
            SELECT 
                item_code,
                item_name,
                price,
                discount_percentage,
                min_qty,
                max_qty
            FROM `tabItem Group Price Rule`
            WHERE parent = %s
            ORDER BY item_code
        """, rule.name, as_dict=True)
        
    return rules


def validate_price_rules_overlap(doc, method=None):
    """
    Valida che non ci siano sovrapposizioni nelle regole prezzo
    Hook per Customer Group Price Rule
    """
    if doc.doctype != "Customer Group Price Rule":
        return
        
    # Controlla sovrapposizioni date
    overlapping = frappe.db.sql("""
        SELECT name
        FROM `tabCustomer Group Price Rule`
        WHERE customer_group = %s
        AND name != %s
        AND is_active = 1
        AND (
            (valid_from IS NULL AND valid_to IS NULL)
            OR (valid_from <= %s AND (valid_to IS NULL OR valid_to >= %s))
            OR (valid_to >= %s AND (valid_from IS NULL OR valid_from <= %s))
        )
        LIMIT 1
    """, (
        doc.customer_group,
        doc.name,
        doc.valid_to or "9999-12-31",
        doc.valid_from or "1900-01-01",
        doc.valid_from or "1900-01-01",
        doc.valid_to or "9999-12-31"
    ))
    
    if overlapping:
        frappe.msgprint(
            _("Attenzione: Esistono altre regole prezzo attive per {0} che si sovrappongono nel periodo").format(
                doc.customer_group
            ),
            indicator="orange"
        )


def calculate_customer_discount_amount(
    customer: str,
    total_amount: float,
    items: List[Dict]
) -> Tuple[float, str]:
    """
    Calcola sconto totale per cliente basato su regole gruppo
    
    Args:
        customer: Cliente
        total_amount: Importo totale
        items: Lista articoli
        
    Returns:
        tuple: (importo_sconto, descrizione_sconto)
    """
    customer_group = frappe.db.get_value("Customer", customer, "customer_group")
    if not customer_group:
        return 0, ""
        
    # Cerca regole sconto su totale ordine
    discount_rules = frappe.db.sql("""
        SELECT 
            discount_percentage,
            discount_amount,
            min_order_value,
            description
        FROM `tabCustomer Group Discount Rule`
        WHERE customer_group = %s
        AND is_active = 1
        AND (min_order_value IS NULL OR min_order_value <= %s)
        ORDER BY min_order_value DESC
        LIMIT 1
    """, (customer_group, total_amount), as_dict=True)
    
    if discount_rules:
        rule = discount_rules[0]
        
        if rule.discount_percentage:
            discount = total_amount * rule.discount_percentage / 100
            desc = f"{rule.discount_percentage}% sconto {customer_group}"
        elif rule.discount_amount:
            discount = min(rule.discount_amount, total_amount)
            desc = f"Sconto fisso {customer_group}"
        else:
            discount = 0
            desc = ""
            
        if rule.description:
            desc = rule.description
            
        return flt(discount, 2), desc
        
    return 0, ""
