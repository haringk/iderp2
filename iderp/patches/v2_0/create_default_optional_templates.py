# -*- coding: utf-8 -*-
# Copyright (c) 2024, idstudio and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute():
    """Crea template predefiniti per articoli opzionali"""
    
    # Crea template comuni
    create_common_templates()
    
    # Associa template ad articoli esistenti
    associate_templates_to_items()
    
    frappe.db.commit()
    print("✅ Template opzionali creati")


def create_common_templates():
    """Crea template opzionali comuni"""
    
    templates = [
        {
            "template_name": "Accessori Tenda Standard",
            "description": "Accessori standard per tende",
            "items": [
                {
                    "item_name": "Bastone Tenda",
                    "default_qty": 1,
                    "is_mandatory": 1,
                    "item_group": "Accessori"
                },
                {
                    "item_name": "Supporti Bastone",
                    "default_qty": 2,
                    "is_mandatory": 1,
                    "item_group": "Accessori"
                },
                {
                    "item_name": "Anelli Tenda",
                    "default_qty": 10,
                    "is_mandatory": 0,
                    "item_group": "Accessori"
                },
                {
                    "item_name": "Ganci Tenda",
                    "default_qty": 10,
                    "is_mandatory": 0,
                    "item_group": "Accessori"
                }
            ]
        },
        {
            "template_name": "Installazione Base",
            "description": "Servizi di installazione base",
            "items": [
                {
                    "item_name": "Installazione Standard",
                    "default_qty": 1,
                    "is_mandatory": 0,
                    "item_group": "Servizi"
                },
                {
                    "item_name": "Rimozione Vecchio Prodotto",
                    "default_qty": 1,
                    "is_mandatory": 0,
                    "item_group": "Servizi"
                }
            ]
        },
        {
            "template_name": "Finiture Premium",
            "description": "Finiture e lavorazioni premium",
            "items": [
                {
                    "item_name": "Orlatura Speciale",
                    "default_qty": 1,
                    "is_mandatory": 0,
                    "item_group": "Lavorazioni"
                },
                {
                    "item_name": "Rinforzo Perimetrale",
                    "default_qty": 1,
                    "is_mandatory": 0,
                    "item_group": "Lavorazioni"
                },
                {
                    "item_name": "Trattamento Antimacchia",
                    "default_qty": 1,
                    "is_mandatory": 0,
                    "item_group": "Trattamenti"
                }
            ]
        }
    ]
    
    for template_data in templates:
        # Controlla se il template esiste già
        if not frappe.db.exists("Optional Template", {
            "template_name": template_data["template_name"]
        }):
            # Estrai gli articoli
            items = template_data.pop("items", [])
            
            # Crea template
            template = frappe.get_doc({
                "doctype": "Optional Template",
                **template_data,
                "is_active": 1,
                "items": []
            })
            
            # Aggiungi articoli solo se esistono nel sistema
            for item_data in items:
                # Cerca articolo per nome o crea se necessario
                item_code = get_or_create_item(
                    item_data["item_name"],
                    item_data["item_group"]
                )
                
                if item_code:
                    template.append("items", {
                        "item_code": item_code,
                        "default_qty": item_data["default_qty"],
                        "is_mandatory": item_data["is_mandatory"]
                    })
            
            if template.items:
                template.insert(ignore_permissions=True)
                print(f"✓ Creato template: {template_data['template_name']}")


def get_or_create_item(item_name, item_group):
    """Recupera o crea un articolo"""
    
    # Cerca articolo esistente
    item_code = frappe.db.get_value("Item", {"item_name": item_name}, "name")
    
    if item_code:
        return item_code
        
    # Se il gruppo articoli non esiste, usa quello predefinito
    if not frappe.db.exists("Item Group", item_group):
        item_group = "All Item Groups"
        
    # Crea nuovo articolo
    try:
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_name.replace(" ", "-").upper(),
            "item_name": item_name,
            "item_group": item_group,
            "stock_uom": "Nos",
            "is_stock_item": 0,
            "is_sales_item": 1,
            "is_purchase_item": 1,
            "description": f"{item_name} - Articolo opzionale"
        })
        item.insert(ignore_permissions=True)
        print(f"  → Creato articolo: {item_name}")
        return item.name
    except Exception as e:
        print(f"  ⚠ Impossibile creare articolo {item_name}: {str(e)}")
        return None


def associate_templates_to_items():
    """Associa template ad articoli che potrebbero beneficiarne"""
    
    # Associazioni predefinite basate su pattern nome articolo
    associations = [
        {
            "pattern": "%tenda%",
            "template": "Accessori Tenda Standard"
        },
        {
            "pattern": "%tessuto%",
            "template": "Finiture Premium"
        }
    ]
    
    for assoc in associations:
        # Trova articoli che corrispondono al pattern
        items = frappe.db.sql("""
            SELECT name
            FROM `tabItem`
            WHERE LOWER(item_name) LIKE %s
            AND is_sales_item = 1
        """, (assoc["pattern"],))
        
        if items and frappe.db.exists("Optional Template", assoc["template"]):
            for (item_code,) in items:
                # Verifica se l'associazione esiste già
                existing = frappe.db.exists("Item Optional Template", {
                    "parent": item_code,
                    "optional_template": assoc["template"]
                })
                
                if not existing:
                    # Aggiungi associazione template
                    item_doc = frappe.get_doc("Item", item_code)
                    
                    # Verifica se il campo esiste (potrebbe essere custom)
                    if hasattr(item_doc, "optional_templates"):
                        item_doc.append("optional_templates", {
                            "optional_template": assoc["template"]
                        })
                        item_doc.save(ignore_permissions=True)
                        print(f"✓ Associato template '{assoc['template']}' a '{item_code}'")
