# iderp/customer_group_pricing.py
"""
Gestione prezzi differenziati per gruppo cliente
"""

import frappe
from frappe import _
from frappe.model.document import Document

@frappe.whitelist()
def get_customer_group_pricing(customer, item_code):
    """
    Ottieni regole prezzo per un cliente specifico
    """
    if not customer or not item_code:
        return {}
    
    # Ottieni gruppo del cliente
    customer_group = frappe.db.get_value("Customer", customer, "customer_group")
    if not customer_group:
        return {}
    
    # Cerca regole per questo gruppo e item
    rules = frappe.get_all("Customer Group Price Rule",
        filters={
            "customer_group": customer_group,
            "item_code": item_code,
            "enabled": 1
        },
        fields=["*"]
    )
    
    if not rules:
        # Cerca regole per gruppo "All Customer Groups"
        rules = frappe.get_all("Customer Group Price Rule",
            filters={
                "customer_group": "All Customer Groups", 
                "item_code": item_code,
                "enabled": 1
            },
            fields=["*"]
        )
    
    return rules[0] if rules else {}

def apply_customer_group_rules(doc, method=None):
    """
    Hook per applicare regole gruppo su documenti vendita
    """
    if not hasattr(doc, "customer") or not hasattr(doc, "items"):
        return
    
    customer_rules = {}
    
    for item in doc.items:
        if not item.item_code:
            continue
            
        # Cache rules per evitare query multiple
        if item.item_code not in customer_rules:
            customer_rules[item.item_code] = get_customer_group_pricing(
                doc.customer, 
                item.item_code
            )
        
        rule = customer_rules[item.item_code]
        if not rule:
            continue
        
        # Salva flag che sono state applicate regole
        item.customer_group_rules_applied = 1
        
        # Applica minimi per metro quadrato
        if item.tipo_vendita == "Metro Quadrato" and rule.get("min_sqm"):
            if item.mq_calcolati < rule["min_sqm"]:
                # Calcola come se fossero i m² minimi
                old_mq = item.mq_calcolati
                effective_mq = rule["min_sqm"]
                
                # Ricalcola prezzo con m² minimi
                if item.prezzo_mq:
                    new_rate = (effective_mq / item.qty) * item.prezzo_mq if item.qty > 0 else 0
                    item.rate = new_rate
                    
                    item.note_calcolo += f"\n⚠️ MINIMO APPLICATO: {rule['min_sqm']} m²"
                    item.note_calcolo += f"\n📊 Calcolato su {effective_mq} m² invece di {old_mq:.3f} m²"
        
        # Applica importo minimo ordine
        if rule.get("min_amount") and item.rate < rule["min_amount"]:
            item.rate = rule["min_amount"]
            item.note_calcolo += f"\n⚠️ IMPORTO MINIMO: €{rule['min_amount']}"
        
        # Applica sconto percentuale gruppo
        if rule.get("discount_percentage"):
            discount = rule["discount_percentage"] / 100
            item.rate = item.rate * (1 - discount)
            item.discount_percentage = rule["discount_percentage"]
            item.note_calcolo += f"\n🎁 Sconto gruppo {rule['customer_group']}: {rule['discount_percentage']}%"

def create_customer_group_price_rule_doctype():
    """Crea il DocType per le regole gruppo cliente"""
    
    if frappe.db.exists("DocType", "Customer Group Price Rule"):
        print("[iderp] - DocType 'Customer Group Price Rule' già esistente")
        return
    
    # Prima crea la child table
    create_customer_group_pricing_tier_doctype()
    
    # Poi crea il DocType principale
    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": "Customer Group Price Rule",
        "module": "Custom",
        "custom": 0,
        "is_submittable": 0,
        "track_changes": 1,
        "fields": [
            {
                "fieldname": "customer_group",
                "fieldtype": "Link",
                "label": "Gruppo Cliente",
                "options": "Customer Group",
                "reqd": 1,
                "in_list_view": 1,
                "in_standard_filter": 1
            },
            {
                "fieldname": "item_code",
                "fieldtype": "Link", 
                "label": "Articolo",
                "options": "Item",
                "reqd": 1,
                "in_list_view": 1,
                "in_standard_filter": 1
            },
            {
                "fieldname": "column_break_1",
                "fieldtype": "Column Break"
            },
            {
                "fieldname": "enabled",
                "fieldtype": "Check",
                "label": "Abilitato",
                "default": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "priority",
                "fieldtype": "Int",
                "label": "Priorità",
                "default": 0,
                "description": "Priorità più alta viene applicata per prima"
            },
            {
                "fieldname": "section_break_1",
                "fieldtype": "Section Break",
                "label": "Minimi e Limiti"
            },
            {
                "fieldname": "min_sqm",
                "fieldtype": "Float",
                "label": "m² Minimi",
                "precision": 3,
                "description": "Metri quadri minimi fatturabili (0 = nessun minimo)"
            },
            {
                "fieldname": "min_amount",
                "fieldtype": "Currency",
                "label": "Importo Minimo",
                "description": "Importo minimo per riga ordine"
            },
            {
                "fieldname": "column_break_2",
                "fieldtype": "Column Break"
            },
            {
                "fieldname": "min_quantity",
                "fieldtype": "Int",
                "label": "Quantità Minima",
                "description": "Quantità minima ordinabile"
            },
            {
                "fieldname": "max_quantity",
                "fieldtype": "Int",
                "label": "Quantità Massima",
                "description": "Quantità massima ordinabile"
            },
            {
                "fieldname": "section_break_2",
                "fieldtype": "Section Break",
                "label": "Prezzi e Sconti"
            },
            {
                "fieldname": "discount_percentage",
                "fieldtype": "Percent",
                "label": "Sconto %",
                "description": "Sconto percentuale per questo gruppo"
            },
            {
                "fieldname": "use_custom_pricing_tiers",
                "fieldtype": "Check",
                "label": "Usa Scaglioni Personalizzati",
                "description": "Utilizza scaglioni prezzo specifici per questo gruppo invece di quelli dell'articolo"
            },
            {
                "fieldname": "pricing_tiers",
                "fieldtype": "Table",
                "label": "Scaglioni Prezzo Personalizzati",
                "options": "Customer Group Pricing Tier",
                "depends_on": "use_custom_pricing_tiers",
                "description": "Scaglioni prezzo specifici per questo gruppo"
            },
            {
                "fieldname": "section_break_3",
                "fieldtype": "Section Break",
                "label": "Note e Validità"
            },
            {
                "fieldname": "valid_from",
                "fieldtype": "Date",
                "label": "Valido Dal",
                "description": "Data inizio validità (vuoto = sempre valido)"
            },
            {
                "fieldname": "valid_till",
                "fieldtype": "Date",
                "label": "Valido Fino Al",
                "description": "Data fine validità (vuoto = sempre valido)"
            },
            {
                "fieldname": "column_break_3",
                "fieldtype": "Column Break"
            },
            {
                "fieldname": "notes",
                "fieldtype": "Text",
                "label": "Note",
                "description": "Note interne su questa regola"
            }
        ],
        "permissions": [
            {
                "role": "System Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "print": 1,
                "export": 1
            },
            {
                "role": "Sales Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "print": 1,
                "export": 1
            },
            {
                "role": "Sales User",
                "read": 1,
                "print": 1
            }
        ]
    })
    
    doc.insert(ignore_permissions=True)
    print("[iderp] ✓ DocType 'Customer Group Price Rule' creato")

def create_customer_group_pricing_tier_doctype():
    """Crea child table per scaglioni prezzo gruppo"""
    
    if frappe.db.exists("DocType", "Customer Group Pricing Tier"):
        print("[iderp] - Child Table 'Customer Group Pricing Tier' già esistente")
        return
    
    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": "Customer Group Pricing Tier",
        "module": "Custom",
        "custom": 1,
        "istable": 1,
        "editable_grid": 1,
        "fields": [
            {
                "fieldname": "from_sqm",
                "fieldtype": "Float",
                "label": "Da m²",
                "precision": 3,
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2
            },
            {
                "fieldname": "to_sqm",
                "fieldtype": "Float",
                "label": "A m²",
                "precision": 3,
                "in_list_view": 1,
                "columns": 2,
                "description": "Vuoto = illimitato"
            },
            {
                "fieldname": "price_per_sqm",
                "fieldtype": "Currency",
                "label": "€/m²",
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2
            },
            {
                "fieldname": "description",
                "fieldtype": "Data",
                "label": "Descrizione",
                "in_list_view": 1,
                "columns": 2
            }
        ]
    })
    
    doc.insert(ignore_permissions=True)
    print("[iderp] ✓ Child Table 'Customer Group Pricing Tier' creata")

def install_customer_group_fields():
    """Installa campi per supporto gruppi cliente"""
    
    from iderp.install import create_custom_field
    
    custom_fields = [
        {
            "fieldname": "customer_group_rules_applied",
            "label": "Regole Gruppo Applicate",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "note_calcolo",
            "description": "Indica se sono state applicate regole del gruppo cliente"
        }
    ]
    
    doctypes = ["Quotation Item", "Sales Order Item", "Sales Invoice Item", "Delivery Note Item"]
    
    for dt in doctypes:
        for cf in custom_fields:
            create_custom_field(dt, cf)
    
    print("[iderp] ✓ Campi gruppo cliente aggiunti ai documenti vendita")

def create_sample_customer_group_rules():
    """Crea regole di esempio per dimostrare il funzionamento"""
    
    # Verifica se esistono già
    if frappe.db.exists("Customer Group Price Rule", {"customer_group": "Commercial"}):
        print("[iderp] - Regole esempio già esistenti")
        return
    
    # Trova un item di esempio
    sample_item = frappe.db.get_value("Item", 
        {"supports_custom_measurement": 1, "tipo_vendita_default": "Metro Quadrato"}, 
        "item_code"
    )
    
    if not sample_item:
        print("[iderp] - Nessun item configurato per metri quadri, saltando esempi")
        return
    
    # Regola 1: Clienti Commercial - Nessun minimo, sconto 15%
    try:
        rule1 = frappe.get_doc({
            "doctype": "Customer Group Price Rule",
            "customer_group": "Commercial",
            "item_code": sample_item,
            "enabled": 1,
            "priority": 10,
            "min_sqm": 0,
            "min_amount": 0,
            "discount_percentage": 15,
            "notes": "Clienti commerciali - Sconto 15%, nessun minimo"
        })
        rule1.insert(ignore_permissions=True)
        print(f"[iderp] ✓ Regola esempio creata per gruppo Commercial")
    except:
        pass
    
    # Regola 2: Clienti Individual - Minimo 1m²
    try:
        rule2 = frappe.get_doc({
            "doctype": "Customer Group Price Rule",
            "customer_group": "Individual", 
            "item_code": sample_item,
            "enabled": 1,
            "priority": 5,
            "min_sqm": 1.0,
            "min_amount": 50,
            "discount_percentage": 0,
            "notes": "Clienti privati - Minimo 1m² o €50"
        })
        rule2.insert(ignore_permissions=True)
        print(f"[iderp] ✓ Regola esempio creata per gruppo Individual")
    except:
        pass

# Integrazione con calcolo prezzi esistente
def get_customer_specific_price_for_sqm(customer, item_code, total_sqm):
    """
    Ottieni prezzo per m² considerando il gruppo cliente
    """
    if not customer:
        # Se non c'è cliente, usa prezzi standard
        from iderp.pricing_utils import get_price_for_sqm
        return get_price_for_sqm(item_code, total_sqm)
    
    # Ottieni regole gruppo cliente
    rule = get_customer_group_pricing(customer, item_code)
    
    if rule and rule.get("use_custom_pricing_tiers") and rule.get("pricing_tiers"):
        # Usa scaglioni personalizzati del gruppo
        for tier in rule["pricing_tiers"]:
            if total_sqm >= tier["from_sqm"]:
                if not tier["to_sqm"] or total_sqm <= tier["to_sqm"]:
                    return {
                        "price_per_sqm": tier["price_per_sqm"],
                        "tier_name": tier.get("description", f"{tier['from_sqm']}-{tier['to_sqm']} m²"),
                        "from_sqm": tier["from_sqm"],
                        "to_sqm": tier["to_sqm"],
                        "customer_group_rule": True
                    }
    
    # Altrimenti usa prezzi standard dell'item
    from iderp.pricing_utils import get_price_for_sqm
    standard_price = get_price_for_sqm(item_code, total_sqm)
    
    # Applica eventuale sconto gruppo
    if rule and rule.get("discount_percentage") and standard_price:
        discount = rule["discount_percentage"] / 100
        standard_price["price_per_sqm"] = standard_price["price_per_sqm"] * (1 - discount)
        standard_price["customer_group_discount"] = rule["discount_percentage"]
    
    return standard_price