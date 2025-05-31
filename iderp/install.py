import frappe

def after_install():
    """Installazione plugin iderp con supporto multi-unità e scaglioni"""
    print("[iderp] Iniziando installazione plugin...")
    
    # 1. Installa campi custom per documenti di vendita
    install_sales_custom_fields()
    
    # 2. Installa campi custom per configurazione Item
    install_item_config_fields()
    
    # 3. Crea DocType per scaglioni prezzo
    create_pricing_tier_doctype()
    
    print("[iderp] Installazione completata con successo!")
    print("[iderp] Plugin installato con supporto per:")
    print("[iderp] - Vendita al pezzo")
    print("[iderp] - Vendita al metro quadrato con scaglioni") 
    print("[iderp] - Vendita al metro lineare")
    print("[iderp] - Configurazione Item personalizzata")
    print("[iderp] - Tabella scaglioni prezzo")

def install_sales_custom_fields():
    """Installa campi custom per documenti di vendita"""
    doctypes = [
        "Quotation Item",
        "Sales Order Item",
        "Delivery Note Item", 
        "Sales Invoice Item",
        "Purchase Order Item",
        "Purchase Invoice Item",
        "Material Request Item",
    ]
    
    custom_fields = [
        # Campo per tipo di vendita
        {
            "fieldname": "tipo_vendita",
            "label": "Tipo Vendita", 
            "fieldtype": "Select",
            "options": "\nPezzo\nMetro Quadrato\nMetro Lineare",
            "default": "Metro Quadrato",
            "insert_after": "item_code",
            "reqd": 1,
            "description": "Seleziona come vendere questo prodotto",
        },
        
        # Campi per metri quadrati
        {
            "fieldname": "base",
            "label": "Base (cm)",
            "fieldtype": "Float", 
            "insert_after": "tipo_vendita",
            "precision": 2,
            "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
            "description": "Base in centimetri per calcolo mq",
        },
        {
            "fieldname": "altezza",
            "label": "Altezza (cm)",
            "fieldtype": "Float",
            "insert_after": "base",
            "precision": 2, 
            "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
            "description": "Altezza in centimetri per calcolo mq",
        },
        {
            "fieldname": "mq_singolo",
            "label": "m² Singolo",
            "fieldtype": "Float",
            "insert_after": "altezza",
            "precision": 4,
            "read_only": 1,
            "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
            "description": "Metri quadri per singolo pezzo",
        },
        {
            "fieldname": "mq_calcolati",
            "label": "m² Totali",
            "fieldtype": "Float",
            "insert_after": "mq_singolo",
            "precision": 3,
            "read_only": 1,
            "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
            "description": "Metri quadri totali (singolo × quantità)",
        },
        
        # Campi per metri lineari
        {
            "fieldname": "larghezza_materiale",
            "label": "Larghezza Materiale (cm)",
            "fieldtype": "Float",
            "insert_after": "mq_calcolati", 
            "precision": 2,
            "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'",
            "description": "Larghezza del materiale in centimetri",
        },
        {
            "fieldname": "lunghezza",
            "label": "Lunghezza (cm)",
            "fieldtype": "Float",
            "insert_after": "larghezza_materiale",
            "precision": 2,
            "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'", 
            "description": "Lunghezza in centimetri",
        },
        {
            "fieldname": "ml_calcolati",
            "label": "Metri Lineari",
            "fieldtype": "Float",
            "insert_after": "lunghezza",
            "precision": 2,
            "read_only": 1,
            "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'",
            "description": "Metri lineari totali (lunghezza × quantità)",
        },
        
        # Prezzi specifici per tipo
        {
            "fieldname": "prezzo_mq",
            "label": "Prezzo al m² (€)",
            "fieldtype": "Currency",
            "insert_after": "rate",
            "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
            "description": "Prezzo per metro quadrato (da scaglioni o manuale)",
        },
        {
            "fieldname": "prezzo_ml", 
            "label": "Prezzo al ml (€)",
            "fieldtype": "Currency",
            "insert_after": "prezzo_mq",
            "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'",
            "description": "Prezzo per metro lineare",
        },
        
        # Campo informativo
        {
            "fieldname": "note_calcolo",
            "label": "Dettaglio Calcolo",
            "fieldtype": "Text",
            "insert_after": "prezzo_ml",
            "read_only": 1,
            "description": "Mostra come è stato calcolato il prezzo con scaglioni",
        },
    ]
    
    for dt in doctypes:
        for cf in custom_fields:
            create_custom_field(dt, cf)

def install_item_config_fields():
    """Installa campi custom per configurazione Item"""
    custom_fields = [
        {
            "fieldname": "measurement_config_section",
            "fieldtype": "Section Break",
            "label": "Configurazione Vendita Personalizzata",
            "insert_after": "website_specifications",
            "collapsible": 1,
        },
        {
            "fieldname": "supports_custom_measurement",
            "fieldtype": "Check", 
            "label": "Supporta Misure Personalizzate",
            "insert_after": "measurement_config_section",
            "description": "Abilita calcoli per metro quadrato/lineare",
        },
        {
            "fieldname": "tipo_vendita_default",
            "fieldtype": "Select",
            "label": "Tipo Vendita Default",
            "options": "\nPezzo\nMetro Quadrato\nMetro Lineare",
            "insert_after": "supports_custom_measurement",
            "depends_on": "supports_custom_measurement",
        },
        {
            "fieldname": "config_column_break",
            "fieldtype": "Column Break",
            "insert_after": "tipo_vendita_default",
        },
        {
            "fieldname": "larghezza_materiale_default",
            "fieldtype": "Float",
            "label": "Larghezza Materiale Default (cm)",
            "precision": 2,
            "insert_after": "config_column_break",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Lineare'",
        },
        
        # Sezione scaglioni prezzo
        {
            "fieldname": "pricing_tiers_section",
            "fieldtype": "Section Break",
            "label": "Scaglioni Prezzo",
            "insert_after": "larghezza_materiale_default",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Quadrato'",
            "collapsible": 1,
        },
        {
            "fieldname": "pricing_tiers",
            "fieldtype": "Table",
            "label": "Scaglioni Prezzo m²",
            "insert_after": "pricing_tiers_section",
            "options": "Pricing Tier",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Quadrato'",
            "description": "Definisci prezzi diversi in base ai metri quadri totali",
        },
        
        # Limiti misurazione
        {
            "fieldname": "measurement_limits_section", 
            "fieldtype": "Section Break",
            "label": "Limiti Misurazione",
            "insert_after": "pricing_tiers",
            "depends_on": "supports_custom_measurement",
            "collapsible": 1,
        },
        {
            "fieldname": "base_min",
            "fieldtype": "Float",
            "label": "Base Minima (cm)",
            "default": 1,
            "insert_after": "measurement_limits_section",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Quadrato'",
        },
        {
            "fieldname": "base_max", 
            "fieldtype": "Float",
            "label": "Base Massima (cm)",
            "default": 1000,
            "insert_after": "base_min",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Quadrato'",
        },
        {
            "fieldname": "limits_column_break",
            "fieldtype": "Column Break",
            "insert_after": "base_max",
        },
        {
            "fieldname": "altezza_min",
            "fieldtype": "Float", 
            "label": "Altezza Minima (cm)",
            "default": 1,
            "insert_after": "limits_column_break",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Quadrato'",
        },
        {
            "fieldname": "altezza_max",
            "fieldtype": "Float",
            "label": "Altezza Massima (cm)", 
            "default": 1000,
            "insert_after": "altezza_min",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Quadrato'",
        },
        {
            "fieldname": "lunghezza_limits_section",
            "fieldtype": "Section Break",
            "label": "Limiti Lunghezza",
            "insert_after": "altezza_max",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Lineare'",
            "collapsible": 1,
        },
        {
            "fieldname": "lunghezza_min",
            "fieldtype": "Float",
            "label": "Lunghezza Minima (cm)",
            "default": 1,
            "insert_after": "lunghezza_limits_section",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Lineare'",
        },
        {
            "fieldname": "lunghezza_max",
            "fieldtype": "Float",
            "label": "Lunghezza Massima (cm)",
            "default": 10000,
            "insert_after": "lunghezza_min",
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Lineare'",
        },
    ]
    
    for cf in custom_fields:
        create_custom_field("Item", cf)

def create_pricing_tier_doctype():
    """Crea il DocType per gli scaglioni prezzo"""
    
    # Verifica se esiste già
    if frappe.db.exists("DocType", "Pricing Tier"):
        print("[iderp] - DocType Pricing Tier già esistente")
        return
    
    # Crea il DocType
    doctype_json = {
        "doctype": "DocType",
        "name": "Pricing Tier",
        "module": "iderp",
        "istable": 1,
        "editable_grid": 1,
        "engine": "InnoDB",
        "fields": [
            {
                "fieldname": "item_code",
                "fieldtype": "Link",
                "options": "Item",
                "label": "Item Code",
                "reqd": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "from_sqm",
                "fieldtype": "Float",
                "label": "Da m²",
                "precision": 3,
                "reqd": 1,
                "in_list_view": 1,
                "description": "Metri quadri minimi per questo scaglione"
            },
            {
                "fieldname": "to_sqm",
                "fieldtype": "Float", 
                "label": "A m²",
                "precision": 3,
                "in_list_view": 1,
                "description": "Metri quadri massimi (lascia vuoto per 'oltre')"
            },
            {
                "fieldname": "price_per_sqm",
                "fieldtype": "Currency",
                "label": "Prezzo €/m²",
                "reqd": 1,
                "in_list_view": 1,
                "description": "Prezzo per metro quadrato in questo scaglione"
            },
            {
                "fieldname": "is_default",
                "fieldtype": "Check",
                "label": "Prezzo Default",
                "description": "Usa come prezzo di fallback se nessuno scaglione corrisponde"
            }
        ],
        "permissions": [
            {
                "role": "System Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "export": 1,
                "print": 1,
                "email": 1,
                "report": 1,
                "share": 1
            },
            {
                "role": "Sales Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1
            },
            {
                "role": "Sales User",
                "read": 1,
                "write": 1,
                "create": 1
            }
        ]
    }
    
    try:
        doctype_doc = frappe.get_doc(doctype_json)
        doctype_doc.insert(ignore_permissions=True)
        print("[iderp] ✓ DocType Pricing Tier creato")
    except Exception as e:
        print(f"[iderp] ✗ Errore creazione DocType Pricing Tier: {str(e)}")

def create_custom_field(doctype, field_dict):
    """Crea un Custom Field se non esiste già"""
    if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_dict["fieldname"]}):
        try:
            cf_doc = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": doctype,
                **field_dict
            })
            cf_doc.insert(ignore_permissions=True)
            print(f"[iderp] ✓ Aggiunto campo {field_dict['fieldname']} a {doctype}")
        except Exception as e:
            print(f"[iderp] ✗ Errore creazione campo {field_dict['fieldname']}: {str(e)}")
    else:
        print(f"[iderp] - Campo {field_dict['fieldname']} già presente su {doctype}")

# Funzioni di utilità per debug e manutenzione
def reinstall_sales_fields():
    """Reinstalla solo i campi di vendita (per debug)"""
    print("[iderp] Reinstallando campi di vendita...")
    install_sales_custom_fields()
    print("[iderp] Reinstallazione completata!")

def create_sample_pricing_tiers(item_code):
    """Crea scaglioni di esempio per un item"""
    sample_tiers = [
        {"from_sqm": 0, "to_sqm": 10, "price_per_sqm": 10.0},
        {"from_sqm": 10.001, "to_sqm": 50, "price_per_sqm": 8.0},
        {"from_sqm": 50.001, "to_sqm": 100, "price_per_sqm": 7.0},
        {"from_sqm": 100.001, "to_sqm": None, "price_per_sqm": 6.0},
    ]
    
    for tier in sample_tiers:
        if not frappe.db.exists("Pricing Tier", {
            "item_code": item_code, 
            "from_sqm": tier["from_sqm"]
        }):
            tier_doc = frappe.get_doc({
                "doctype": "Pricing Tier",
                "item_code": item_code,
                **tier
            })
            tier_doc.insert(ignore_permissions=True)
            print(f"[iderp] ✓ Creato scaglione {tier['from_sqm']}-{tier['to_sqm']} per {item_code}")

def remove_all_custom_fields():
    """Rimuove tutti i campi custom di iderp (per debug)"""
    field_names = [
        "tipo_vendita", "base", "altezza", "mq_singolo", "mq_calcolati",
        "larghezza_materiale", "lunghezza", "ml_calcolati",
        "prezzo_mq", "prezzo_ml", "note_calcolo"
    ]
    
    doctypes = [
        "Quotation Item", "Sales Order Item", "Delivery Note Item", 
        "Sales Invoice Item", "Purchase Order Item", "Purchase Invoice Item", 
        "Material Request Item"
    ]
    
    for dt in doctypes:
        for field_name in field_names:
            if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": field_name}):
                frappe.delete_doc("Custom Field", {"dt": dt, "fieldname": field_name})
                print(f"[iderp] Rimosso campo {field_name} da {dt}")

def get_pricing_for_item(item_code, total_sqm):
    """Funzione di utilità per ottenere prezzo da scaglioni"""
    tiers = frappe.get_all("Pricing Tier", 
        filters={"item_code": item_code},
        fields=["from_sqm", "to_sqm", "price_per_sqm", "is_default"],
        order_by="from_sqm asc"
    )
    
    # Cerca scaglione appropriato
    for tier in tiers:
        if total_sqm >= tier.from_sqm and (not tier.to_sqm or total_sqm <= tier.to_sqm):
            return tier.price_per_sqm
    
    # Fallback su prezzo default
    default_tier = next((t for t in tiers if t.is_default), None)
    return default_tier.price_per_sqm if default_tier else 0