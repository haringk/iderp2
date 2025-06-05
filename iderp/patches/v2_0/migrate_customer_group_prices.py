# -*- coding: utf-8 -*-
# Copyright (c) 2024, ID Studio and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute():
    """Migra prezzi gruppo cliente al nuovo formato"""
    
    # Migra prezzi esistenti da Price List a Customer Group Price Rule
    migrate_existing_price_lists()
    
    # Crea regole predefinite per gruppi cliente comuni
    create_default_price_rules()
    
    # Aggiorna riferimenti nei documenti
    update_document_references()
    
    frappe.db.commit()
    print("✅ Migrazione prezzi gruppo cliente completata")


def migrate_existing_price_lists():
    """Migra prezzi da Price List esistenti"""
    
    # Recupera tutti i prezzi con gruppo cliente
    customer_group_prices = frappe.db.sql("""
        SELECT 
            ip.name,
            ip.item_code,
            ip.price_list_rate,
            ip.customer_group,
            ip.valid_from,
            ip.valid_upto,
            pl.name as price_list
        FROM `tabItem Price` ip
        INNER JOIN `tabPrice List` pl ON pl.name = ip.price_list
        WHERE ip.customer_group IS NOT NULL
        AND ip.customer_group != ''
        AND ip.selling = 1
    """, as_dict=True)
    
    # Raggruppa per gruppo cliente
    price_rules_by_group = {}
    for price in customer_group_prices:
        if price.customer_group not in price_rules_by_group:
            price_rules_by_group[price.customer_group] = []
        price_rules_by_group[price.customer_group].append(price)
    
    # Crea regole prezzo per ogni gruppo
    for customer_group, prices in price_rules_by_group.items():
        # Verifica se esiste già una regola
        existing_rule = frappe.db.exists("Customer Group Price Rule", {
            "customer_group": customer_group,
            "rule_name": f"Migrated from {prices[0].price_list}"
        })
        
        if not existing_rule:
            # Crea nuova regola
            rule = frappe.get_doc({
                "doctype": "Customer Group Price Rule",
                "customer_group": customer_group,
                "rule_name": f"Listino {customer_group}",
                "description": f"Migrato da {prices[0].price_list}",
                "priority": 10,
                "is_active": 1,
                "items": []
            })
            
            # Aggiungi articoli
            for price in prices:
                rule.append("items", {
                    "item_code": price.item_code,
                    "price": price.price_list_rate,
                    "min_qty": 0
                })
            
            rule.insert(ignore_permissions=True)
            print(f"✓ Creata regola prezzo per {customer_group}")


def create_default_price_rules():
    """Crea regole prezzo predefinite per gruppi comuni"""
    
    default_rules = [
        {
            "customer_group": "Rivenditori",
            "rule_name": "Sconto Rivenditori Standard",
            "description": "Sconto 30% per rivenditori",
            "priority": 20,
            "discount_percentage": 30
        },
        {
            "customer_group": "Grossisti",
            "rule_name": "Sconto Grossisti",
            "description": "Sconto 40% per grossisti",
            "priority": 30,
            "discount_percentage": 40
        },
        {
            "customer_group": "Privati",
            "rule_name": "Listino Privati",
            "description": "Prezzo pieno per clienti privati",
            "priority": 5,
            "discount_percentage": 0
        }
    ]
    
    for rule_data in default_rules:
        # Controlla se il gruppo cliente esiste
        if frappe.db.exists("Customer Group", rule_data["customer_group"]):
            # Controlla se la regola esiste già
            if not frappe.db.exists("Customer Group Price Rule", {
                "customer_group": rule_data["customer_group"],
                "rule_name": rule_data["rule_name"]
            }):
                rule = frappe.get_doc({
                    "doctype": "Customer Group Price Rule",
                    **rule_data,
                    "is_active": 1
                })
                rule.insert(ignore_permissions=True)
                print(f"✓ Creata regola predefinita: {rule_data['rule_name']}")


def update_document_references():
    """Aggiorna riferimenti nei documenti esistenti"""
    
    # Aggiorna custom script che potrebbero riferirsi al vecchio sistema
    scripts_to_update = frappe.db.sql("""
        SELECT name, script
        FROM `tabClient Script`
        WHERE script LIKE '%price_list%'
        OR script LIKE '%customer_group%'
    """, as_dict=True)
    
    for script in scripts_to_update:
        updated_script = script.script
        
        # Sostituisci riferimenti vecchi con nuovi
        replacements = [
            ("frappe.db.get_value('Item Price'", "iderp.pricing.get_customer_group_price("),
            ("get_price_list_rate", "get_customer_group_price")
        ]
        
        for old, new in replacements:
            if old in updated_script:
                updated_script = updated_script.replace(old, new)
                
        if updated_script != script.script:
            frappe.db.set_value(
                "Client Script",
                script.name,
                "script",
                updated_script
            )
            print(f"✓ Aggiornato script: {script.name}")