# -*- coding: utf-8 -*-
# Copyright (c) 2024, idstudio and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Aggiunge custom field per gestione metrature"""
    
    # Definizione custom fields
    custom_fields = {
        # Campi su Item (articolo)
        "Item": [
            {
                "fieldname": "section_metrature",
                "label": "Metrature",
                "fieldtype": "Section Break",
                "insert_after": "stock_uom",
                "collapsible": 1
            },
            {
                "fieldname": "base_default",
                "label": "Base Predefinita (mm)",
                "fieldtype": "Float",
                "insert_after": "section_metrature",
                "description": "Base predefinita in millimetri"
            },
            {
                "fieldname": "altezza_default",
                "label": "Altezza Predefinita (mm)",
                "fieldtype": "Float",
                "insert_after": "base_default",
                "description": "Altezza predefinita in millimetri"
            },
            {
                "fieldname": "column_break_metr1",
                "fieldtype": "Column Break",
                "insert_after": "altezza_default"
            },
            {
                "fieldname": "min_base",
                "label": "Base Minima (mm)",
                "fieldtype": "Float",
                "insert_after": "column_break_metr1",
                "description": "Limite minimo per la base"
            },
            {
                "fieldname": "max_base",
                "label": "Base Massima (mm)",
                "fieldtype": "Float",
                "insert_after": "min_base",
                "description": "Limite massimo per la base"
            },
            {
                "fieldname": "min_altezza",
                "label": "Altezza Minima (mm)",
                "fieldtype": "Float",
                "insert_after": "max_base",
                "description": "Limite minimo per l'altezza"
            },
            {
                "fieldname": "max_altezza",
                "label": "Altezza Massima (mm)",
                "fieldtype": "Float",
                "insert_after": "min_altezza",
                "description": "Limite massimo per l'altezza"
            }
        ],
        
        # Campi comuni per documenti vendita
        "Quotation Item": get_sales_item_fields(),
        "Sales Order Item": get_sales_item_fields(),
        "Delivery Note Item": get_delivery_item_fields(),
        "Sales Invoice Item": get_sales_item_fields(),
        
        # Campi comuni per documenti acquisto
        "Purchase Order Item": get_purchase_item_fields(),
        "Purchase Receipt Item": get_purchase_item_fields(),
        "Purchase Invoice Item": get_purchase_item_fields(),
        
        # Campi su Customer per gestione fiscale italiana
        "Customer": [
            {
                "fieldname": "fiscal_code",
                "label": "Codice Fiscale",
                "fieldtype": "Data",
                "insert_after": "tax_id",
                "length": 16,
                "description": "Codice fiscale per persone fisiche"
            },
            {
                "fieldname": "default_sales_taxes_template",
                "label": "Template Tasse Predefinito",
                "fieldtype": "Link",
                "options": "Sales Taxes and Charges Template",
                "insert_after": "tax_category"
            }
        ]
    }
    
    # Crea i custom fields
    create_custom_fields(custom_fields, update=True)
    
    # Aggiorna proprietà campi esistenti
    update_field_properties()
    
    print("✅ Custom fields metrature aggiunti con successo")


def get_sales_item_fields():
    """Campi comuni per righe documenti vendita"""
    return [
        {
            "fieldname": "section_dimensioni",
            "label": "Dimensioni",
            "fieldtype": "Section Break",
            "insert_after": "description",
            "collapsible": 1
        },
        {
            "fieldname": "base",
            "label": "Base (mm)",
            "fieldtype": "Float",
            "insert_after": "section_dimensioni",
            "description": "Base in millimetri",
            "in_list_view": 1
        },
        {
            "fieldname": "altezza",
            "label": "Altezza (mm)",
            "fieldtype": "Float",
            "insert_after": "base",
            "description": "Altezza in millimetri",
            "in_list_view": 1
        },
        {
            "fieldname": "mq_totali",
            "label": "Mq Totali",
            "fieldtype": "Float",
            "insert_after": "altezza",
            "read_only": 1,
            "description": "Metri quadri totali calcolati",
            "in_list_view": 1
        }
    ]


def get_delivery_item_fields():
    """Campi per righe DDT (include info spedizione)"""
    fields = get_sales_item_fields()
    
    # Aggiungi campi specifici per spedizione
    fields.extend([
        {
            "fieldname": "column_break_ship1",
            "fieldtype": "Column Break",
            "insert_after": "mq_totali"
        },
        {
            "fieldname": "total_weight",
            "label": "Peso Totale (kg)",
            "fieldtype": "Float",
            "insert_after": "column_break_ship1",
            "description": "Peso totale della riga"
        },
        {
            "fieldname": "volume",
            "label": "Volume (m³)",
            "fieldtype": "Float",
            "insert_after": "total_volume",
            "description": "Volume totale della riga"
        },
        {
            "fieldname": "no_of_packages",
            "label": "Numero Colli",
            "fieldtype": "Int",
            "insert_after": "volume",
            "description": "Numero di colli per questa riga"
        }
    ])
    
    return fields


def get_purchase_item_fields():
    """Campi per righe documenti acquisto"""
    # Simili ai campi vendita ma senza alcune opzioni
    return [
        {
            "fieldname": "section_dimensioni",
            "label": "Dimensioni",
            "fieldtype": "Section Break",
            "insert_after": "description",
            "collapsible": 1
        },
        {
            "fieldname": "base",
            "label": "Base (mm)",
            "fieldtype": "Float",
            "insert_after": "section_dimensioni",
            "description": "Base in millimetri"
        },
        {
            "fieldname": "altezza",
            "label": "Altezza (mm)",
            "fieldtype": "Float",
            "insert_after": "base",
            "description": "Altezza in millimetri"
        },
        {
            "fieldname": "mq_totali",
            "label": "Mq Totali",
            "fieldtype": "Float",
            "insert_after": "altezza",
            "read_only": 1,
            "description": "Metri quadri totali calcolati"
        }
    ]


def update_field_properties():
    """Aggiorna proprietà di campi esistenti per compatibilità"""
    
    # Lista campi da rendere visibili in griglia
    fields_to_show_in_grid = [
        ("Quotation Item", ["base", "altezza", "mq_totali"]),
        ("Sales Order Item", ["base", "altezza", "mq_totali"]),
        ("Sales Invoice Item", ["base", "altezza", "mq_totali"]),
        ("Delivery Note Item", ["base", "altezza", "mq_totali"])
    ]
    
    for doctype, fields in fields_to_show_in_grid:
        for field in fields:
            frappe.db.sql("""
                UPDATE `tabCustom Field`
                SET in_list_view = 1
                WHERE dt = %s AND fieldname = %s
            """, (doctype, field))
    
    frappe.db.commit()
