import frappe

def after_install():
    """Installazione completa plugin iderp - ERPNext 15 Compatible"""
    print("[iderp] === Installazione ERPNext 15 Safe Mode ===")
    
    try:
        # 1. Installa campi custom per documenti di vendita
        install_sales_custom_fields()
        
        # 2. Installa campi custom per configurazione Item
        install_item_config_fields()
        
        # 3. DISABILITATO PER ORA: Child Tables (potrebbero causare errori)
        # create_item_pricing_tier_child_table()
        # add_pricing_table_to_item()
        
        print("[iderp] ✅ Installazione base completata")
        print("[iderp] ✓ Custom Fields per vendita installati")
        print("[iderp] ✓ Configurazione Item installata")
        print("[iderp] ⚠️ DocTypes avanzati disabilitati temporaneamente")
        
    except Exception as e:
        print(f"[iderp] ❌ Errore installazione: {e}")
        # Non lanciare eccezione per permettere installazione parziale

def install_sales_custom_fields():
    """Installa campi custom per documenti di vendita - ERPNext 15"""
    print("[iderp] Installando campi vendita...")
    
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
            "in_list_view": 1,
            "columns": 2,
            "description": "Seleziona come vendere questo prodotto",
        },
        
        # Campi per metri quadrati
        {
            "fieldname": "base",
            "label": "Base (cm)",
            "fieldtype": "Float", 
            "insert_after": "tipo_vendita",
            "precision": 2,
            "depends_on": "doc.tipo_vendita === 'Metro Quadrato'",  # ERPNext 15 syntax
            "in_list_view": 1,
            "columns": 2,
            "description": "Base in centimetri per calcolo mq",
        },
        {
            "fieldname": "altezza",
            "label": "Altezza (cm)",
            "fieldtype": "Float",
            "insert_after": "base",
            "precision": 2, 
            "depends_on": "doc.tipo_vendita === 'Metro Quadrato'",  # ERPNext 15 syntax
            "in_list_view": 1,
            "columns": 2,
            "description": "Altezza in centimetri per calcolo mq",
        },
        {
            "fieldname": "mq_singolo",
            "label": "m² Singolo",
            "fieldtype": "Float",
            "insert_after": "altezza",
            "precision": 4,
            "read_only": 1,
            "depends_on": "doc.tipo_vendita === 'Metro Quadrato'",
            "in_list_view": 1,
            "columns": 2,
            "description": "Metri quadri per singolo pezzo",
        },
        {
            "fieldname": "mq_calcolati",
            "label": "m² Totali",
            "fieldtype": "Float",
            "insert_after": "mq_singolo",
            "precision": 3,
            "read_only": 1,
            "depends_on": "doc.tipo_vendita === 'Metro Quadrato'",
            "in_list_view": 1,
            "columns": 2,
            "description": "Metri quadri totali (singolo × quantità)",
        },
        
        # Campi per metri lineari
        {
            "fieldname": "larghezza_materiale",
            "label": "Larghezza Materiale (cm)",
            "fieldtype": "Float",
            "insert_after": "mq_calcolati", 
            "precision": 2,
            "depends_on": "doc.tipo_vendita === 'Metro Lineare'",
            "in_list_view": 1,
            "columns": 2,
            "description": "Larghezza del materiale in centimetri",
        },
        {
            "fieldname": "lunghezza",
            "label": "Lunghezza (cm)",
            "fieldtype": "Float",
            "insert_after": "larghezza_materiale",
            "precision": 2,
            "depends_on": "doc.tipo_vendita === 'Metro Lineare'",
            "in_list_view": 1,
            "columns": 2,
            "description": "Lunghezza in centimetri",
        },
        {
            "fieldname": "ml_calcolati",
            "label": "Metri Lineari",
            "fieldtype": "Float",
            "insert_after": "lunghezza",
            "precision": 2,
            "read_only": 1,
            "depends_on": "doc.tipo_vendita === 'Metro Lineare'",
            "in_list_view": 1,
            "columns": 2,
            "description": "Metri lineari totali (lunghezza × quantità)",
        },
        
        # Prezzi specifici per tipo
        {
            "fieldname": "prezzo_mq",
            "label": "Prezzo al m² (€)",
            "fieldtype": "Currency",
            "insert_after": "rate",
            "depends_on": "doc.tipo_vendita === 'Metro Quadrato'",
            "description": "Prezzo per metro quadrato (da scaglioni o manuale)",
        },
        {
            "fieldname": "prezzo_ml", 
            "label": "Prezzo al ml (€)",
            "fieldtype": "Currency",
            "insert_after": "prezzo_mq",
            "depends_on": "doc.tipo_vendita === 'Metro Lineare'",
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
        }
    ]
    
    for dt in doctypes:
        for cf in custom_fields:
            create_custom_field(dt, cf)

def install_item_config_fields():
    """Installa campi custom per configurazione Item base - ERPNext 15"""
    print("[iderp] Installando configurazione Item...")
    
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
            "depends_on": "tipo_vendita_default === 'Metro Lineare'",  # ERPNext 15 syntax
        },
    ]
    
    for cf in custom_fields:
        create_custom_field("Item", cf)

def create_custom_field(doctype, field_dict):
    """Crea Custom Field compatibile ERPNext 15"""
    if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_dict["fieldname"]}):
        try:
            # ERPNext 15 compatible
            cf_doc = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": doctype,
                **field_dict
            })
            
            # Use save() instead of insert() for ERPNext 15
            cf_doc.save(ignore_permissions=True)
            
            # Force commit for ERPNext 15
            frappe.db.commit()
            
            print(f"[iderp] ✓ Campo {field_dict['fieldname']} aggiunto a {doctype}")
        except Exception as e:
            print(f"[iderp] ✗ Errore campo {field_dict['fieldname']}: {str(e)}")
    else:
        print(f"[iderp] - Campo {field_dict['fieldname']} già presente su {doctype}")

# ===== FUNZIONI UTILITY =====

def reinstall_all():
    """Reinstalla tutto da capo"""
    print("[iderp] === Reinstallazione completa ===")
    after_install()

def show_available_items():
    """Mostra item disponibili per test"""
    items = frappe.get_all("Item", 
        fields=["item_code", "item_name"], 
        filters={"disabled": 0},
        limit=10
    )
    
    print("[iderp] === Item disponibili per test ===")
    for item in items:
        print(f"[iderp] - {item.item_code}: {item.item_name}")
    
    return items

def validate_installation():
    """Valida che l'installazione sia corretta"""
    print("[iderp] === Validazione installazione ===")
    
    errors = []
    
    # Verifica campi su Quotation Item
    required_fields = ["tipo_vendita", "base", "altezza", "mq_singolo", "mq_calcolati"]
    for field in required_fields:
        if not frappe.db.exists("Custom Field", {"dt": "Quotation Item", "fieldname": field}):
            errors.append(f"Campo {field} mancante su Quotation Item")
    
    # Verifica campi su Item
    item_fields = ["supports_custom_measurement", "tipo_vendita_default"]
    for field in item_fields:
        if not frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": field}):
            errors.append(f"Campo {field} mancante su Item")
    
    if errors:
        print("[iderp] ✗ Errori trovati:")
        for error in errors:
            print(f"[iderp]   - {error}")
        return False
    else:
        print("[iderp] ✅ Installazione valida!")
        return True

def get_installation_status():
    """Ottieni stato dettagliato dell'installazione"""
    print("[iderp] === Stato installazione ===")
    
    # Campi vendita
    sales_fields = ["tipo_vendita", "base", "altezza", "mq_singolo", "mq_calcolati", "note_calcolo"]
    for field in sales_fields:
        has_field = frappe.db.exists("Custom Field", {"dt": "Quotation Item", "fieldname": field})
        print(f"[iderp] Campo {field}: {'✓' if has_field else '✗'}")
    
    # Campi Item
    item_fields = ["supports_custom_measurement", "tipo_vendita_default"]
    for field in item_fields:
        has_field = frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": field})
        print(f"[iderp] Item {field}: {'✓' if has_field else '✗'}")
    
    # Item configurati
    configured_items = frappe.db.sql("""
        SELECT item_code 
        FROM `tabItem` 
        WHERE supports_custom_measurement = 1
        LIMIT 5
    """, as_dict=True)
    
    print(f"[iderp] Item configurati: {len(configured_items)}")
    for item in configured_items:
        print(f"[iderp]   - {item.item_code}")
    
    print("[iderp] === Fine stato ===")
    
    

# import frappe
# 
# 
# import frappe
# 
# def after_install():
#     """Installazione sicura per ERPNext 15"""
#     print("[iderp] === Installazione ERPNext 15 Safe Mode ===")
#     
#     try:
#         # 1. Solo Custom Fields essenziali per ora
#         install_essential_custom_fields()
#         print("[iderp] ✓ Custom Fields essenziali installati")
#         
#         # 2. Skip DocTypes per ora (potrebbero causare errori)
#         # install_item_config_fields()
#         # create_item_pricing_tier_child_table()
#         
#         print("[iderp] ✓ Installazione base completata")
#         
#     except Exception as e:
#         print(f"[iderp] ❌ Errore installazione: {e}")
#         # Non lanciare eccezione per permettere installazione parziale
# 
# # def install_essential_custom_fields():
# #     """Installa solo i campi essenziali"""
# #     
# #     # Campi base per Quotation Item
# #     essential_fields = [
# #         {
# #             "fieldname": "tipo_vendita",
# #             "label": "Tipo Vendita", 
# #             "fieldtype": "Select",
# #             "options": "\nPezzo\nMetro Quadrato\nMetro Lineare",
# #             "default": "Metro Quadrato",
# #             "insert_after": "item_code",
# #             "reqd": 1
# #         },
# #         {
# #             "fieldname": "base",
# #             "label": "Base (cm)",
# #             "fieldtype": "Float", 
# #             "insert_after": "tipo_vendita",
# #             "precision": 2,
# #             "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'"
# #         },
# #         {
# #             "fieldname": "altezza",
# #             "label": "Altezza (cm)",
# #             "fieldtype": "Float",
# #             "insert_after": "base",
# #             "precision": 2, 
# #             "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'"
# #         }
# #     ]
# #     
# #     # Applica a Quotation Item
# #     for field in essential_fields:
# #         create_custom_field_safe("Quotation Item", field)
# 
# # def create_custom_field_safe(doctype, field_dict):
# #     """Crea Custom Field con gestione errori"""
# #     try:
# #         if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_dict["fieldname"]}):
# #             cf_doc = frappe.get_doc({
# #                 "doctype": "Custom Field",
# #                 "dt": doctype,
# #                 **field_dict
# #             })
# #             cf_doc.insert(ignore_permissions=True)
# #             print(f"[iderp] ✓ Campo {field_dict['fieldname']} aggiunto a {doctype}")
# #         else:
# #             print(f"[iderp] - Campo {field_dict['fieldname']} già presente su {doctype}")
# #     except Exception as e:
# #         print(f"[iderp] ✗ Errore campo {field_dict['fieldname']}: {str(e)}")
# 
# #  def after_install():
# #     """Installazione completa plugin iderp"""
# #     print("[iderp] === Iniziando installazione plugin ===")
# #     
# #     # 1. Installa campi custom per documenti di vendita
# #     install_sales_custom_fields()
# #     
# #     # 2. Installa campi custom per configurazione Item
# #     install_item_config_fields()
# #     
# #     # 3. Crea Child Table per scaglioni prezzo
# #     create_item_pricing_tier_child_table()
# #     
# #     # 4. Aggiunge tabella scaglioni all'Item
# #     add_pricing_table_to_item()
# #     
# #     # 5. NUOVO: Installa sistema Customer Group Pricing
# #     install_customer_group_pricing_system()
# #     
# #     print("[iderp] === Installazione completata ===")
# #     print("[iderp] ✓ Vendita al pezzo")
# #     print("[iderp] ✓ Vendita al metro quadrato con scaglioni") 
# #     print("[iderp] ✓ Vendita al metro lineare")
# #     print("[iderp] ✓ Configurazione Item con scaglioni prezzo")
# #     print("[iderp] ✓ NUOVO: Customer Group Pricing con minimi")
# #     print("[iderp] ✓ Gruppi: Finale, Bronze, Gold, Diamond")
# #     print("[iderp] ✓ Sistema completo pronto all'uso")
# 
# def install_customer_group_pricing_system():
#     """Installa il sistema Customer Group Pricing semplificato"""
#     print("[iderp] Installando Customer Group Pricing...")
#     
#     from iderp.customer_group_pricing import setup_complete_customer_groups
#     
#     # Setup completo: DocType, gruppi, clienti, regole
#     setup_complete_customer_groups()
#     
#     print("[iderp] ✓ Customer Group Pricing installato")
#     
# 
# def setup_universal_pricing_demo():
#     """Setup demo completo per tutti i tipi di vendita"""
#     print("[iderp] === Setup demo pricing universale ===")
#     
#     # Trova item di test
#     test_item = frappe.db.get_value("Item", {"supports_custom_measurement": 1}, "item_code")
#     
#     if not test_item:
#         print("[iderp] ❌ Nessun item configurato")
#         return False
#     
#     try:
#         item_doc = frappe.get_doc("Item", test_item)
#         
#         # SCAGLIONI PER TUTTI I TIPI
#         item_doc.pricing_tiers = []
#         
#         # Metro Quadrato
#         mq_tiers = [
#             {"selling_type": "Metro Quadrato", "from_qty": 0, "to_qty": 0.5, "price_per_unit": 20.0, "tier_name": "Micro m²"},
#             {"selling_type": "Metro Quadrato", "from_qty": 0.5, "to_qty": 2, "price_per_unit": 15.0, "tier_name": "Piccolo m²"},
#             {"selling_type": "Metro Quadrato", "from_qty": 2, "to_qty": None, "price_per_unit": 10.0, "tier_name": "Grande m²", "is_default": 1}
#         ]
#         
#         # Metro Lineare  
#         ml_tiers = [
#             {"selling_type": "Metro Lineare", "from_qty": 0, "to_qty": 5, "price_per_unit": 8.0, "tier_name": "Piccolo ml"},
#             {"selling_type": "Metro Lineare", "from_qty": 5, "to_qty": 20, "price_per_unit": 6.0, "tier_name": "Medio ml"},
#             {"selling_type": "Metro Lineare", "from_qty": 20, "to_qty": None, "price_per_unit": 4.0, "tier_name": "Grande ml", "is_default": 1}
#         ]
#         
#         # Pezzo
#         pz_tiers = [
#             {"selling_type": "Pezzo", "from_qty": 1, "to_qty": 10, "price_per_unit": 5.0, "tier_name": "Retail"},
#             {"selling_type": "Pezzo", "from_qty": 10, "to_qty": 100, "price_per_unit": 3.0, "tier_name": "Wholesale"},
#             {"selling_type": "Pezzo", "from_qty": 100, "to_qty": None, "price_per_unit": 2.0, "tier_name": "Bulk", "is_default": 1}
#         ]
#         
#         # Aggiungi tutti gli scaglioni
#         for tier_data in mq_tiers + ml_tiers + pz_tiers:
#             item_doc.append("pricing_tiers", tier_data)
#         
#         # MINIMI PER GRUPPI
#         item_doc.customer_group_minimums = []
#         
#         # Minimi diversi per tipo vendita
#         minimums = [
#             # Finale
#             {"customer_group": "Finale", "selling_type": "Metro Quadrato", "min_qty": 0.5, "calculation_mode": "Globale Preventivo", "fixed_cost": 5.0, "fixed_cost_mode": "Per Preventivo"},
#             {"customer_group": "Finale", "selling_type": "Metro Lineare", "min_qty": 2.0, "calculation_mode": "Per Riga", "fixed_cost": 3.0, "fixed_cost_mode": "Per Riga"},
#             {"customer_group": "Finale", "selling_type": "Pezzo", "min_qty": 5, "calculation_mode": "Per Riga", "fixed_cost": 0},
#             
#             # Bronze
#             {"customer_group": "Bronze", "selling_type": "Metro Quadrato", "min_qty": 0.25, "calculation_mode": "Globale Preventivo", "fixed_cost": 3.0, "fixed_cost_mode": "Per Preventivo"},
#             {"customer_group": "Bronze", "selling_type": "Metro Lineare", "min_qty": 1.0, "calculation_mode": "Per Riga", "fixed_cost": 2.0, "fixed_cost_mode": "Per Riga"},
#             {"customer_group": "Bronze", "selling_type": "Pezzo", "min_qty": 3, "calculation_mode": "Per Riga", "fixed_cost": 0},
#             
#             # Gold  
#             {"customer_group": "Gold", "selling_type": "Metro Quadrato", "min_qty": 0.1, "calculation_mode": "Globale Preventivo", "fixed_cost": 0},
#             {"customer_group": "Gold", "selling_type": "Metro Lineare", "min_qty": 0.5, "calculation_mode": "Per Riga", "fixed_cost": 0},
#             {"customer_group": "Gold", "selling_type": "Pezzo", "min_qty": 1, "calculation_mode": "Per Riga", "fixed_cost": 0},
#             
#             # Diamond
#             {"customer_group": "Diamond", "selling_type": "Metro Quadrato", "min_qty": 0, "calculation_mode": "Per Riga", "fixed_cost": 0},
#             {"customer_group": "Diamond", "selling_type": "Metro Lineare", "min_qty": 0, "calculation_mode": "Per Riga", "fixed_cost": 0},
#             {"customer_group": "Diamond", "selling_type": "Pezzo", "min_qty": 0, "calculation_mode": "Per Riga", "fixed_cost": 0}
#         ]
#         
#         for min_data in minimums:
#             item_doc.append("customer_group_minimums", min_data)
#         
#         item_doc.save(ignore_permissions=True)
#         
#         print(f"[iderp] ✅ Demo universale configurato per {test_item}")
#         print("[iderp] 📊 3 tipi vendita × 4 gruppi cliente = 12 configurazioni")
#         print("[iderp] 💰 Scaglioni + Minimi + Costi fissi")
#         
#         return True
#         
#     except Exception as e:
#         print(f"[iderp] ❌ Errore setup demo: {e}")
#         return False
# 
# 
# def install_sales_custom_fields():
#     """Installa campi custom per documenti di vendita"""
#     print("[iderp] Installando campi vendita...")
#     
#     doctypes = [
#         "Quotation Item",
#         "Sales Order Item",
#         "Delivery Note Item", 
#         "Sales Invoice Item",
#         "Purchase Order Item",
#         "Purchase Invoice Item",
#         "Material Request Item",
#     ]
#     
#     custom_fields = [
#         # Campo per tipo di vendita
#         {
#             "fieldname": "tipo_vendita",
#             "label": "Tipo Vendita", 
#             "fieldtype": "Select",
#             "options": "\nPezzo\nMetro Quadrato\nMetro Lineare",
#             "default": "Metro Quadrato",
#             "insert_after": "item_code",
#             "reqd": 1,
#             "description": "Seleziona come vendere questo prodotto",
#         },
#         
#         # Campi per metri quadrati
# # Nel array custom_fields, sostituisci i campi base/altezza con:
#         {
#             "fieldname": "base",
#             "label": "Base (cm)",
#             "fieldtype": "Float", 
#             "insert_after": "tipo_vendita",
#             "precision": 2,
#             "depends_on": "doc.tipo_vendita === 'Metro Quadrato'",  # ERPNext 15 syntax
#             "in_list_view": 1,
#             "columns": 2,
#             "description": "Base in centimetri per calcolo mq",
#         },
#         {
#             "fieldname": "altezza",
#             "label": "Altezza (cm)",
#             "fieldtype": "Float",
#             "insert_after": "base",
#             "precision": 2, 
#             "depends_on": "doc.tipo_vendita === 'Metro Quadrato'",  # ERPNext 15 syntax
#             "in_list_view": 1,
#             "columns": 2,
#             "description": "Altezza in centimetri per calcolo mq",
#         },
#         {
#             "fieldname": "mq_singolo",
#             "label": "m² Singolo",
#             "fieldtype": "Float",
#             "insert_after": "altezza",
#             "precision": 4,
#             "read_only": 1,
#             "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
#             "description": "Metri quadri per singolo pezzo",
#         },
#         {
#             "fieldname": "mq_calcolati",
#             "label": "m² Totali",
#             "fieldtype": "Float",
#             "insert_after": "mq_singolo",
#             "precision": 3,
#             "read_only": 1,
#             "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
#             "description": "Metri quadri totali (singolo × quantità)",
#         },
#         
#         # Campi per metri lineari
#         {
#             "fieldname": "larghezza_materiale",
#             "label": "Larghezza Materiale (cm)",
#             "fieldtype": "Float",
#             "insert_after": "mq_calcolati", 
#             "precision": 2,
#             "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'",
#             "description": "Larghezza del materiale in centimetri",
#         },
#         {
#             "fieldname": "lunghezza",
#             "label": "Lunghezza (cm)",
#             "fieldtype": "Float",
#             "insert_after": "larghezza_materiale",
#             "precision": 2,
#             "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'", 
#             "description": "Lunghezza in centimetri",
#         },
#         {
#             "fieldname": "ml_calcolati",
#             "label": "Metri Lineari",
#             "fieldtype": "Float",
#             "insert_after": "lunghezza",
#             "precision": 2,
#             "read_only": 1,
#             "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'",
#             "description": "Metri lineari totali (lunghezza × quantità)",
#         },
#         
#         # Prezzi specifici per tipo
#         {
#             "fieldname": "prezzo_mq",
#             "label": "Prezzo al m² (€)",
#             "fieldtype": "Currency",
#             "insert_after": "rate",
#             "depends_on": "eval:doc.tipo_vendita=='Metro Quadrato'",
#             "description": "Prezzo per metro quadrato (da scaglioni o manuale)",
#         },
#         {
#             "fieldname": "prezzo_ml", 
#             "label": "Prezzo al ml (€)",
#             "fieldtype": "Currency",
#             "insert_after": "prezzo_mq",
#             "depends_on": "eval:doc.tipo_vendita=='Metro Lineare'",
#             "description": "Prezzo per metro lineare",
#         },
#         
#         # Campo informativo
#         {
#             "fieldname": "note_calcolo",
#             "label": "Dettaglio Calcolo",
#             "fieldtype": "Text",
#             "insert_after": "prezzo_ml",
#             "read_only": 1,
#             "description": "Mostra come è stato calcolato il prezzo con scaglioni",
#         },
#         
#         # NUOVO: Campo per customer group rules
#         {
#             "fieldname": "customer_group_rules_applied",
#             "label": "Regole Gruppo Applicate",
#             "fieldtype": "Check",
#             "read_only": 1,
#             "insert_after": "note_calcolo",
#             "description": "Indica se sono state applicate regole del gruppo cliente"
#         }
#     ]
#     
#     for dt in doctypes:
#         for cf in custom_fields:
#             create_custom_field(dt, cf)
# 
# def install_item_config_fields():
#     """Installa campi custom per configurazione Item base"""
#     print("[iderp] Installando configurazione Item...")
#     
#     custom_fields = [
#         {
#             "fieldname": "measurement_config_section",
#             "fieldtype": "Section Break",
#             "label": "Configurazione Vendita Personalizzata",
#             "insert_after": "website_specifications",
#             "collapsible": 1,
#         },
#         {
#             "fieldname": "supports_custom_measurement",
#             "fieldtype": "Check", 
#             "label": "Supporta Misure Personalizzate",
#             "insert_after": "measurement_config_section",
#             "description": "Abilita calcoli per metro quadrato/lineare",
#         },
#         {
#             "fieldname": "tipo_vendita_default",
#             "fieldtype": "Select",
#             "label": "Tipo Vendita Default",
#             "options": "\nPezzo\nMetro Quadrato\nMetro Lineare",
#             "insert_after": "supports_custom_measurement",
#             "depends_on": "supports_custom_measurement",
#         },
#         {
#             "fieldname": "config_column_break",
#             "fieldtype": "Column Break",
#             "insert_after": "tipo_vendita_default",
#         },
#         {
#             "fieldname": "larghezza_materiale_default",
#             "fieldtype": "Float",
#             "label": "Larghezza Materiale Default (cm)",
#             "precision": 2,
#             "insert_after": "config_column_break",
#             "depends_on": "eval:doc.tipo_vendita_default=='Metro Lineare'",
#         },
#     ]
#     
#     for cf in custom_fields:
#         create_custom_field("Item", cf)
# 
# def create_item_pricing_tier_child_table():
#     """Crea Child Table per scaglioni prezzo MULTI-TIPO VENDITA"""
#     print("[iderp] Creando Child Table per scaglioni universali...")
#     
#     # Verifica se esiste già
#     if frappe.db.exists("DocType", "Item Pricing Tier"):
#         print("[iderp] - Child Table già esistente")
#         # Aggiungi nuovi campi se mancano
#         add_multi_type_pricing_fields()
#         return True
#     
#     child_doctype = {
#         "doctype": "DocType",
#         "name": "Item Pricing Tier",
#         "module": "Custom",
#         "custom": 1,
#         "istable": 1,
#         "editable_grid": 1,
#         "track_changes": 0,
#         "engine": "InnoDB",
#         "fields": [
#             {
#                 "fieldname": "selling_type",
#                 "fieldtype": "Select",
#                 "label": "Tipo Vendita",
#                 "options": "\nMetro Quadrato\nMetro Lineare\nPezzo",
#                 "reqd": 1,
#                 "in_list_view": 1,
#                 "columns": 2,
#                 "description": "Tipo di vendita per questo scaglione"
#             },
#             {
#                 "fieldname": "from_qty",
#                 "fieldtype": "Float",
#                 "label": "Da Quantità",
#                 "precision": 3,
#                 "reqd": 1,
#                 "in_list_view": 1,
#                 "columns": 2,
#                 "description": "Quantità minima (m², ml, o pezzi)"
#             },
#             {
#                 "fieldname": "to_qty",
#                 "fieldtype": "Float", 
#                 "label": "A Quantità",
#                 "precision": 3,
#                 "in_list_view": 1,
#                 "columns": 2,
#                 "description": "Quantità massima (vuoto = illimitato)"
#             },
#             {
#                 "fieldname": "price_per_unit",
#                 "fieldtype": "Currency",
#                 "label": "Prezzo/Unità",
#                 "reqd": 1,
#                 "in_list_view": 1,
#                 "columns": 2,
#                 "description": "€/m², €/ml, o €/pezzo"
#             },
#             {
#                 "fieldname": "tier_name",
#                 "fieldtype": "Data",
#                 "label": "Nome Scaglione",
#                 "in_list_view": 1,
#                 "columns": 3,
#                 "description": "Es: Piccole tirature, Industriale, Retail, ecc."
#             },
#             {
#                 "fieldname": "is_default",
#                 "fieldtype": "Check",
#                 "label": "Default",
#                 "columns": 1,
#                 "description": "Prezzo di fallback per questo tipo vendita"
#             }
#         ],
#         "permissions": [
#             {
#                 "role": "System Manager",
#                 "read": 1,
#                 "write": 1,
#                 "create": 1,
#                 "delete": 1
#             },
#             {
#                 "role": "Sales Manager", 
#                 "read": 1,
#                 "write": 1,
#                 "create": 1,
#                 "delete": 1
#             },
#             {
#                 "role": "Sales User",
#                 "read": 1,
#                 "write": 1,
#                 "create": 1
#             }
#         ]
#     }
#     
#     try:
#         child_doc = frappe.get_doc(child_doctype)
#         child_doc.insert(ignore_permissions=True)
#         print("[iderp] ✓ Child Table 'Item Pricing Tier' multi-tipo creata")
#         return True
#     except Exception as e:
#         print(f"[iderp] ✗ Errore creazione Child Table: {e}")
#         return False
# 
# def add_multi_type_pricing_fields():
#     """Aggiungi campi per multi-tipo se mancanti"""
#     
#     try:
#         doctype_doc = frappe.get_doc("DocType", "Item Pricing Tier")
#         
#         # Verifica se selling_type esiste già
#         has_selling_type = any(field.fieldname == "selling_type" for field in doctype_doc.fields)
#         
#         if not has_selling_type:
#             print("[iderp] Aggiungendo campi multi-tipo...")
#             
#             # Rinomina campi esistenti
#             for field in doctype_doc.fields:
#                 if field.fieldname == "from_sqm":
#                     field.fieldname = "from_qty"
#                     field.label = "Da Quantità"
#                     field.description = "Quantità minima (m², ml, o pezzi)"
#                 elif field.fieldname == "to_sqm":
#                     field.fieldname = "to_qty"
#                     field.label = "A Quantità"
#                     field.description = "Quantità massima (vuoto = illimitato)"
#                 elif field.fieldname == "price_per_sqm":
#                     field.fieldname = "price_per_unit"
#                     field.label = "Prezzo/Unità"
#                     field.description = "€/m², €/ml, o €/pezzo"
#             
#             # Aggiungi campo selling_type all'inizio
#             new_field = {
#                 "fieldname": "selling_type",
#                 "fieldtype": "Select",
#                 "label": "Tipo Vendita",
#                 "options": "\nMetro Quadrato\nMetro Lineare\nPezzo",
#                 "reqd": 1,
#                 "in_list_view": 1,
#                 "columns": 2,
#                 "description": "Tipo di vendita per questo scaglione",
#                 "idx": 1
#             }
#             
#             doctype_doc.insert(0, "fields", new_field)
#             doctype_doc.save()
#             
#             print("[iderp] ✓ Campi multi-tipo aggiunti")
#         else:
#             print("[iderp] - Campi multi-tipo già presenti")
#             
#         return True
#         
#     except Exception as e:
#         print(f"[iderp] ✗ Errore aggiunta campi: {e}")
#         return False
# 
# def add_pricing_table_to_item():
#     """Aggiunge la tabella scaglioni all'Item"""
#     print("[iderp] Aggiungendo tabella scaglioni all'Item...")
#     
#     item_fields = [
# {
#     "fieldname": "pricing_section",
#     "fieldtype": "Section Break",
#     "label": "Scaglioni Prezzo Universali",  # <-- Cambia anche il label
#     "insert_after": "larghezza_materiale_default",
#     "collapsible": 1,
#     "depends_on": "eval:doc.supports_custom_measurement",  # <-- Rimuovi la condizione Metro Quadrato
#     "description": "Configura prezzi per tutti i tipi di vendita: m², ml, pezzi"
# },
# {
#     "fieldname": "pricing_tiers",
#     "fieldtype": "Table",
#     "label": "Scaglioni Prezzo",
#     "insert_after": "pricing_section",
#     "options": "Item Pricing Tier",
#     "depends_on": "eval:doc.supports_custom_measurement",  # <-- Rimuovi la condizione Metro Quadrato
#     "description": "Definisci prezzi per tutti i tipi di vendita"
# },
# {
#     "fieldname": "pricing_help",
#     "fieldtype": "HTML",
#     "label": "",
#     "insert_after": "pricing_tiers",
#     "options": """
#     <div class="alert alert-info">
#         <strong>💡 Come funzionano gli scaglioni universali:</strong><br>
#         • <strong>Metro Quadrato</strong>: Prezzi in base ai m² totali dell'ordine<br>
#         • <strong>Metro Lineare</strong>: Prezzi in base ai metri lineari totali<br>
#         • <strong>Pezzo</strong>: Prezzi in base al numero di pezzi<br>
#         • Il sistema sceglierà automaticamente il prezzo giusto per tipo<br>
#         • Usa il campo "Tipo Vendita" per differenziare gli scaglioni<br>
#         • Spunta "Default" per il prezzo di fallback per ogni tipo
#     </div>
#     """,
#     "depends_on": "eval:doc.supports_custom_measurement"  # <-- Rimuovi la condizione Metro Quadrato
# },
#     ]
#     
#     for field in item_fields:
#         create_custom_field("Item", field)
# 
# def create_custom_field(doctype, field_dict):
#     """Crea Custom Field compatibile ERPNext 15"""
#     if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_dict["fieldname"]}):
#         try:
#             # ERPNext 15 compatible
#             cf_doc = frappe.get_doc({
#                 "doctype": "Custom Field",
#                 "dt": doctype,
#                 **field_dict
#             })
#             
#             # Use save() instead of insert() for ERPNext 15
#             cf_doc.save(ignore_permissions=True)
#             
#             # Force commit for ERPNext 15
#             frappe.db.commit()
#             
#             print(f"[iderp] ✓ Campo {field_dict['fieldname']} aggiunto a {doctype}")
#         except Exception as e:
#             print(f"[iderp] ✗ Errore campo {field_dict['fieldname']}: {str(e)}")
#     else:
#         print(f"[iderp] - Campo {field_dict['fieldname']} già presente su {doctype}")
#         
# 
# # ===== FUNZIONI UTILITY =====
# 
# def reinstall_all():
#     """Reinstalla tutto da capo"""
#     print("[iderp] === Reinstallazione completa ===")
#     after_install()
# 
# def create_sample_pricing_for_item(item_code):
#     """Crea scaglioni di esempio per un item"""
#     print(f"[iderp] Creando scaglioni esempio per {item_code}...")
#     
#     if not frappe.db.exists("Item", item_code):
#         print(f"[iderp] ✗ Item {item_code} non trovato")
#         return False
#     
#     try:
#         item_doc = frappe.get_doc("Item", item_code)
#         
#         # Abilita misure personalizzate
#         item_doc.supports_custom_measurement = 1
#         item_doc.tipo_vendita_default = "Metro Quadrato"
#         
#         # Scaglioni di esempio specifici per stampa digitale
#         sample_tiers = [
#             {
#                 "from_sqm": 0,
#                 "to_sqm": 0.25,
#                 "price_per_sqm": 20.0,
#                 "tier_name": "Micro tirature"
#             },
#             {
#                 "from_sqm": 0.25,
#                 "to_sqm": 1,
#                 "price_per_sqm": 15.0,
#                 "tier_name": "Piccole tirature"
#             },
#             {
#                 "from_sqm": 1,
#                 "to_sqm": 5,
#                 "price_per_sqm": 12.0,
#                 "tier_name": "Tirature medie"
#             },
#             {
#                 "from_sqm": 5,
#                 "to_sqm": None,
#                 "price_per_sqm": 8.0,
#                 "tier_name": "Tirature grandi",
#                 "is_default": 1
#             }
#         ]
#         
#         # Pulisci e aggiungi scaglioni
#         item_doc.pricing_tiers = []
#         for tier_data in sample_tiers:
#             item_doc.append("pricing_tiers", tier_data)
#         
#         item_doc.save(ignore_permissions=True)
#         print(f"[iderp] ✓ Scaglioni esempio creati per {item_code}")
#         return True
#         
#     except Exception as e:
#         print(f"[iderp] ✗ Errore creazione scaglioni: {e}")
#         return False
# 
# def show_available_items():
#     """Mostra item disponibili per test"""
#     items = frappe.get_all("Item", 
#         fields=["item_code", "item_name"], 
#         filters={"disabled": 0},
#         limit=10
#     )
#     
#     print("[iderp] === Item disponibili per test ===")
#     for item in items:
#         print(f"[iderp] - {item.item_code}: {item.item_name}")
#     
#     if items:
#         print(f"[iderp] Per test: create_sample_pricing_for_item('{items[0].item_code}')")
#     
#     return items
# 
# def quick_test_setup():
#     """Setup rapido per test con primo item disponibile"""
#     print("[iderp] === Setup rapido per test ===")
#     
#     # Mostra item disponibili
#     items = show_available_items()
#     
#     if items:
#         # Prendi il primo item e crea scaglioni
#         test_item = items[0].item_code
#         print(f"[iderp] Configurando {test_item} per test...")
#         
#         if create_sample_pricing_for_item(test_item):
#             print(f"[iderp] ✓ Setup test completato!")
#             print(f"[iderp] Vai su Item → {test_item} → Scaglioni Prezzo m²")
#             print(f"[iderp] Poi testa in una Quotation con diversi Customer Group")
#             return test_item
#     else:
#         print("[iderp] ✗ Nessun item disponibile per test")
#         return None
# 
# def validate_installation():
#     """Valida che l'installazione sia corretta"""
#     print("[iderp] === Validazione installazione ===")
#     
#     errors = []
#     
#     # Verifica Child DocType
#     if not frappe.db.exists("DocType", "Item Pricing Tier"):
#         errors.append("DocType 'Item Pricing Tier' mancante")
#     
#     # Verifica campi su Quotation Item
#     required_fields = ["tipo_vendita", "base", "altezza", "mq_singolo", "mq_calcolati"]
#     for field in required_fields:
#         if not frappe.db.exists("Custom Field", {"dt": "Quotation Item", "fieldname": field}):
#             errors.append(f"Campo {field} mancante su Quotation Item")
#     
#     # Verifica campi su Item
#     item_fields = ["supports_custom_measurement", "tipo_vendita_default", "pricing_tiers"]
#     for field in item_fields:
#         if not frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": field}):
#             errors.append(f"Campo {field} mancante su Item")
#     
#     if errors:
#         print("[iderp] ✗ Errori trovati:")
#         for error in errors:
#             print(f"[iderp]   - {error}")
#         return False
#     else:
#         print("[iderp] ✓ Installazione valida!")
#         return True
# 
# def get_installation_status():
#     """Ottieni stato dettagliato dell'installazione"""
#     print("[iderp] === Stato installazione ===")
#     
#     # Child DocType
#     has_child_doctype = frappe.db.exists("DocType", "Item Pricing Tier")
#     print(f"[iderp] Child DocType: {'✓' if has_child_doctype else '✗'}")
#     
#     # Campi vendita
#     sales_fields = ["tipo_vendita", "base", "altezza", "mq_singolo", "mq_calcolati", "note_calcolo"]
#     for field in sales_fields:
#         has_field = frappe.db.exists("Custom Field", {"dt": "Quotation Item", "fieldname": field})
#         print(f"[iderp] Campo {field}: {'✓' if has_field else '✗'}")
#     
#     # Campi Item
#     item_fields = ["supports_custom_measurement", "pricing_tiers"]
#     for field in item_fields:
#         has_field = frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": field})
#         print(f"[iderp] Item {field}: {'✓' if has_field else '✗'}")
#     
#     # Item configurati
#     configured_items = frappe.db.sql("""
#         SELECT item_code 
#         FROM `tabItem` 
#         WHERE supports_custom_measurement = 1
#         LIMIT 5
#     """, as_dict=True)
#     
#     print(f"[iderp] Item configurati: {len(configured_items)}")
#     for item in configured_items:
#         print(f"[iderp]   - {item.item_code}")
#     
#     print("[iderp] === Fine stato ===")
#     
# def setup_global_minimums_demo():
#     """Setup demo per minimi globali"""
#     print("[iderp] Configurando demo minimi globali...")
#     
#     # Aggiorna campo se necessario
#     from iderp.customer_group_minimums_fix import add_global_minimum_fields
#     add_global_minimum_fields()
#     
#     # Trova item di test
#     test_item = frappe.db.get_value("Item", {"supports_custom_measurement": 1}, "item_code")
#     
#     if test_item:
#         try:
#             item_doc = frappe.get_doc("Item", test_item)
#             
#             # Configura minimi misti: alcuni per riga, altri globali
#             item_doc.customer_group_minimums = []
#             
#             # Finale: Globale (più vantaggioso)
#             item_doc.append("customer_group_minimums", {
#                 "customer_group": "Finale",
#                 "min_sqm": 0.5,
#                 "calculation_mode": "Globale Preventivo",
#                 "enabled": 1,
#                 "description": "Setup UNA volta per preventivo",
#                 "priority": 10
#             })
#             
#             # Bronze: Per riga (standard)
#             item_doc.append("customer_group_minimums", {
#                 "customer_group": "Bronze", 
#                 "min_sqm": 0.25,
#                 "calculation_mode": "Per Riga",
#                 "enabled": 1,
#                 "description": "Minimo per ogni riga",
#                 "priority": 20
#             })
#             
#             # Gold: Globale
#             item_doc.append("customer_group_minimums", {
#                 "customer_group": "Gold",
#                 "min_sqm": 0.1,
#                 "calculation_mode": "Globale Preventivo",
#                 "enabled": 1,
#                 "description": "Minimo globale preferenziale",
#                 "priority": 30
#             })
#             
#             # Diamond: Nessun minimo
#             item_doc.append("customer_group_minimums", {
#                 "customer_group": "Diamond",
#                 "min_sqm": 0,
#                 "calculation_mode": "Per Riga",
#                 "enabled": 1,
#                 "description": "Nessun minimo",
#                 "priority": 40
#             })
#             
#             item_doc.save(ignore_permissions=True)
#             
#             print(f"[iderp] ✅ Demo minimi globali configurato per {test_item}")
#             print("[iderp] 🎯 Finale/Gold: minimi globali")
#             print("[iderp] 📄 Bronze: minimi per riga")
#             print("[iderp] 💎 Diamond: nessun minimo")
#             
#         except Exception as e:
#             print(f"[iderp] ❌ Errore setup demo: {e}")