# -*- coding: utf-8 -*-
# Copyright (c) 2024, ID Studio and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute():
    """Aggiorna impostazioni UOM per articoli a metratura"""
    
    # Crea UOM personalizzate se non esistono
    create_custom_uoms()
    
    # Aggiorna articoli esistenti
    update_existing_items()
    
    # Configura conversioni UOM
    setup_uom_conversions()
    
    frappe.db.commit()
    print("✅ Aggiornamento UOM completato")


def create_custom_uoms():
    """Crea unità di misura personalizzate"""
    
    custom_uoms = [
        {
            "uom_name": "Mq",
            "must_be_whole_number": 0,
            "enabled": 1,
            "description": "Metro quadrato"
        },
        {
            "uom_name": "Metro",
            "must_be_whole_number": 0,
            "enabled": 1,
            "description": "Metro lineare"
        },
        {
            "uom_name": "ml",
            "must_be_whole_number": 0,
            "enabled": 1,
            "description": "Metro lineare (alternativo)"
        }
    ]
    
    for uom_data in custom_uoms:
        if not frappe.db.exists("UOM", uom_data["uom_name"]):
            uom = frappe.get_doc({
                "doctype": "UOM",
                **uom_data
            })
            uom.insert(ignore_permissions=True)
            print(f"✓ Creata UOM: {uom_data['uom_name']}")


def update_existing_items():
    """Aggiorna articoli che potrebbero usare metrature"""
    
    # Trova articoli con indicazioni di metratura nel nome o descrizione
    potential_items = frappe.db.sql("""
        SELECT 
            name,
            item_name,
            description,
            stock_uom
        FROM `tabItem`
        WHERE 
            (LOWER(item_name) LIKE '%metr%'
            OR LOWER(item_name) LIKE '%mq%'
            OR LOWER(item_name) LIKE '%m²%'
            OR LOWER(description) LIKE '%metro quadr%'
            OR LOWER(description) LIKE '%metri quadr%')
            AND stock_uom NOT IN ('Mq', 'Metro')
    """, as_dict=True)
    
    for item in potential_items:
        print(f"⚠ Articolo '{item.name}' potrebbe necessitare UOM metratura (attuale: {item.stock_uom})")
        
        # Suggerisci UOM basata su keywords
        suggested_uom = None
        if any(kw in item.item_name.lower() or kw in (item.description or "").lower() 
               for kw in ["mq", "m²", "metro quadr", "metri quadr"]):
            suggested_uom = "Mq"
        elif any(kw in item.item_name.lower() or kw in (item.description or "").lower() 
                 for kw in ["metro linear", "metri linear", "ml"]):
            suggested_uom = "Metro"
            
        if suggested_uom:
            # Crea notifica per amministratore
            create_uom_update_notification(item.name, item.stock_uom, suggested_uom)


def setup_uom_conversions():
    """Configura conversioni UOM standard"""
    
    conversions = [
        # Da Mq a unità base
        {
            "from_uom": "Mq",
            "to_uom": "Square Meter",
            "value": 1.0
        },
        {
            "from_uom": "Mq",
            "to_uom": "Square Centimeter",
            "value": 10000.0
        },
        # Da Metro a unità base
        {
            "from_uom": "Metro",
            "to_uom": "Meter",
            "value": 1.0
        },
        {
            "from_uom": "Metro",
            "to_uom": "Centimeter",
            "value": 100.0
        },
        {
            "from_uom": "Metro",
            "to_uom": "Millimeter",
            "value": 1000.0
        }
    ]
    
    for conv in conversions:
        # Verifica che entrambe le UOM esistano
        if frappe.db.exists("UOM", conv["from_uom"]) and frappe.db.exists("UOM", conv["to_uom"]):
            # Controlla se la conversione esiste già
            existing = frappe.db.exists("UOM Conversion Factor", {
                "from_uom": conv["from_uom"],
                "to_uom": conv["to_uom"]
            })
            
            if not existing:
                doc = frappe.get_doc({
                    "doctype": "UOM Conversion Factor",
                    **conv
                })
                doc.insert(ignore_permissions=True)
                print(f"✓ Creata conversione: {conv['from_uom']} → {conv['to_uom']}")


def create_uom_update_notification(item_code, current_uom, suggested_uom):
    """Crea notifica per suggerire aggiornamento UOM"""
    
    message = f"""
    <p>L'articolo <b>{item_code}</b> potrebbe necessitare un aggiornamento dell'unità di misura:</p>
    <ul>
        <li>UOM attuale: <b>{current_uom}</b></li>
        <li>UOM suggerita: <b>{suggested_uom}</b></li>
    </ul>
    <p><a href="/app/item/{item_code}" class="btn btn-primary btn-sm">Modifica Articolo</a></p>
    """
    
    # Crea ToDo per amministratore
    todo = frappe.get_doc({
        "doctype": "ToDo",
        "description": message,
        "reference_type": "Item",
        "reference_name": item_code,
        "assigned_by": "Administrator",
        "owner": "Administrator",
        "priority": "Low",
        "status": "Open"
    })
    todo.insert(ignore_permissions=True)
