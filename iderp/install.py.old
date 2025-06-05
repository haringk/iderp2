# iderp/install.py
"""
Installazione completa IDERP per ERPNext 15
Sistema stampa digitale con pricing universale e customer groups
"""

import frappe
from frappe import _
import time

def after_install():
    """Installazione completa plugin IDERP per ERPNext 15"""
    print("\n" + "="*70)
    print("🚀 INSTALLAZIONE IDERP v2.0 - ERPNext 15 Compatible")
    print("="*70)
    
    try:
        # 1. Installa campi custom per documenti vendita
        print("\n1️⃣ Installazione campi documenti vendita...")
        install_sales_custom_fields()
        
        # 2. Installa campi custom per configurazione Item
        print("\n2️⃣ Installazione configurazione Item...")
        install_item_config_fields()
        
        # 3. Crea Child DocTypes per sistema avanzato
        print("\n3️⃣ Creazione DocTypes avanzati...")
        create_advanced_doctypes()
        
        # 4. Aggiunge tabelle agli Item
        print("\n4️⃣ Configurazione tabelle Item...")
        add_tables_to_item()
        
        # 5. Installa sistema Customer Groups
        print("\n5️⃣ Setup Customer Groups...")
        install_customer_group_system()
        
        # 6. Configura demo data
        print("\n6️⃣ Configurazione demo...")
        setup_demo_data()
        
        # 7. Validazione finale
        print("\n7️⃣ Validazione installazione...")
        validate_installation()
        
        print("\n" + "="*70)
        print("✅ INSTALLAZIONE IDERP COMPLETATA CON SUCCESSO!")
        print("="*70)
        show_installation_summary()
        
    except Exception as e:
        print(f"\n❌ ERRORE INSTALLAZIONE: {e}")
        import traceback
        traceback.print_exc()
        # Non lanciare eccezione per permettere installazione parziale

def install_sales_custom_fields():
    """Installa campi custom per documenti di vendita - ERPNext 15 Compatible"""
    
    doctypes = [
        "Quotation Item",
        "Sales Order Item", 
        "Delivery Note Item",
        "Sales Invoice Item",
        "Purchase Order Item",
        "Purchase Invoice Item",
        "Material Request Item"
    ]
    
    custom_fields = [
        # Tipo vendita principale
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
            "description": "Modalità di vendita per questo prodotto"
        },
        
        # Section Break per Metro Quadrato
        {
            "fieldname": "mq_section_break",
            "fieldtype": "Section Break",
            "label": "Misure Metro Quadrato",
            "insert_after": "tipo_vendita",
            "depends_on": "eval:doc.tipo_vendita==='Metro Quadrato'",
            "collapsible": 1
        },
        
        # Campi Metro Quadrato
        {
            "fieldname": "base",
            "label": "Base (cm)",
            "fieldtype": "Float",
            "insert_after": "mq_section_break",
            "precision": 2,
            "depends_on": "eval:doc.tipo_vendita==='Metro Quadrato'",
            "in_list_view": 1,
            "columns": 2,
            "description": "Base del prodotto in centimetri"
        },
        {
            "fieldname": "altezza",
            "label": "Altezza (cm)", 
            "fieldtype": "Float",
            "insert_after": "base",
            "precision": 2,
            "depends_on": "eval:doc.tipo_vendita==='Metro Quadrato'",
            "in_list_view": 1,
            "columns": 2,
            "description": "Altezza del prodotto in centimetri"
        },
        
        # Column Break
        {
            "fieldname": "mq_column_break",
            "fieldtype": "Column Break",
            "insert_after": "altezza"
        },
        
        {
            "fieldname": "mq_singolo",
            "label": "m² Singolo",
            "fieldtype": "Float",
            "insert_after": "mq_column_break",
            "precision": 4,
            "read_only": 1,
            "depends_on": "eval:doc.tipo_vendita==='Metro Quadrato'",
            "description": "Metri quadri per singolo pezzo (calcolato automaticamente)"
        },
        {
            "fieldname": "mq_calcolati", 
            "label": "m² Totali",
            "fieldtype": "Float",
            "insert_after": "mq_singolo",
            "precision": 3,
            "read_only": 1,
            "depends_on": "eval:doc.tipo_vendita==='Metro Quadrato'",
            "description": "Metri quadri totali (singolo × quantità)"
        },
        
        # Section Break per Metro Lineare
        {
            "fieldname": "ml_section_break",
            "fieldtype": "Section Break",
            "label": "Misure Metro Lineare",
            "insert_after": "mq_calcolati",
            "depends_on": "eval:doc.tipo_vendita==='Metro Lineare'",
            "collapsible": 1
        },
        
        # Campi Metro Lineare
        {
            "fieldname": "lunghezza",
            "label": "Lunghezza (cm)",
            "fieldtype": "Float",
            "insert_after": "ml_section_break",
            "precision": 2,
            "depends_on": "eval:doc.tipo_vendita==='Metro Lineare'",
            "in_list_view": 1,
            "columns": 2,
            "description": "Lunghezza del prodotto in centimetri"
        },
        {
            "fieldname": "larghezza_materiale",
            "label": "Larghezza Materiale (cm)",
            "fieldtype": "Float", 
            "insert_after": "lunghezza",
            "precision": 2,
            "depends_on": "eval:doc.tipo_vendita==='Metro Lineare'",
            "columns": 2,
            "description": "Larghezza del materiale (può essere predefinita)"
        },
        
        # Column Break ML
        {
            "fieldname": "ml_column_break",
            "fieldtype": "Column Break",
            "insert_after": "larghezza_materiale"
        },
        
        {
            "fieldname": "ml_calcolati",
            "label": "Metri Lineari Totali",
            "fieldtype": "Float",
            "insert_after": "ml_column_break",
            "precision": 2,
            "read_only": 1,
            "depends_on": "eval:doc.tipo_vendita==='Metro Lineare'",
            "description": "Metri lineari totali (lunghezza × quantità / 100)"
        },
        
        # Section Break per Pezzi
        {
            "fieldname": "pz_section_break",
            "fieldtype": "Section Break",
            "label": "Vendita a Pezzi",
            "insert_after": "ml_calcolati",
            "depends_on": "eval:doc.tipo_vendita==='Pezzo'",
            "collapsible": 1
        },
        
        {
            "fieldname": "pz_totali",
            "label": "Pezzi Totali",
            "fieldtype": "Float",
            "insert_after": "pz_section_break",
            "precision": 0,
            "read_only": 1,
            "depends_on": "eval:doc.tipo_vendita==='Pezzo'",
            "description": "Numero totale di pezzi"
        },
        
        # Section Break per Prezzi
        {
            "fieldname": "pricing_section_break",
            "fieldtype": "Section Break",
            "label": "Prezzi Specifici",
            "insert_after": "pz_totali",
            "collapsible": 1
        },
        
        # Prezzi specifici per tipo
        {
            "fieldname": "prezzo_mq",
            "label": "Prezzo €/m²",
            "fieldtype": "Currency",
            "insert_after": "pricing_section_break",
            "depends_on": "eval:doc.tipo_vendita==='Metro Quadrato'",
            "columns": 2,
            "description": "Prezzo al metro quadrato (da scaglioni o manuale)"
        },
        {
            "fieldname": "prezzo_ml",
            "label": "Prezzo €/ml",
            "fieldtype": "Currency", 
            "insert_after": "prezzo_mq",
            "depends_on": "eval:doc.tipo_vendita==='Metro Lineare'",
            "columns": 2,
            "description": "Prezzo al metro lineare"
        },
        
        # Column Break Prezzi
        {
            "fieldname": "pricing_column_break",
            "fieldtype": "Column Break",
            "insert_after": "prezzo_ml"
        },
        
        # Campi di controllo
        {
            "fieldname": "auto_calculated",
            "label": "Calcolato Automaticamente",
            "fieldtype": "Check",
            "insert_after": "pricing_column_break",
            "read_only": 1,
            "description": "Indica se il prezzo è stato calcolato automaticamente"
        },
        {
            "fieldname": "manual_rate_override",
            "label": "Prezzo Modificato Manualmente",
            "fieldtype": "Check",
            "insert_after": "auto_calculated",
            "read_only": 1,
            "description": "Indica se il prezzo è stato modificato manualmente"
        },
        {
            "fieldname": "price_locked",
            "label": "Prezzo Bloccato",
            "fieldtype": "Check",
            "insert_after": "manual_rate_override",
            "description": "Blocca il ricalcolo automatico del prezzo"
        },
        
        # Note di calcolo
        {
            "fieldname": "note_calcolo",
            "label": "Dettaglio Calcolo",
            "fieldtype": "Long Text",
            "insert_after": "price_locked",
            "read_only": 1,
            "description": "Mostra come è stato calcolato il prezzo"
        }
    ]
    
    for dt in doctypes:
        print(f"   📋 Configurando {dt}...")
        for cf in custom_fields:
            create_custom_field_v15(dt, cf)

def install_item_config_fields():
    """Installa campi custom per configurazione Item - ERPNext 15"""
    
    custom_fields = [
        # Section principale
        {
            "fieldname": "iderp_config_section",
            "fieldtype": "Section Break",
            "label": "🎯 IDERP - Configurazione Vendita Avanzata",
            "insert_after": "website_specifications",
            "collapsible": 0
        },
        
        # Configurazione base
        {
            "fieldname": "supports_custom_measurement",
            "fieldtype": "Check",
            "label": "Supporta Misure Personalizzate",
            "insert_after": "iderp_config_section",
            "description": "Abilita calcoli automatici per metro quadrato/lineare"
        },
        {
            "fieldname": "tipo_vendita_default",
            "fieldtype": "Select",
            "label": "Tipo Vendita Default",
            "options": "\nPezzo\nMetro Quadrato\nMetro Lineare",
            "insert_after": "supports_custom_measurement",
            "depends_on": "supports_custom_measurement",
            "description": "Tipo di vendita predefinito per questo articolo"
        },
        
        # Column Break
        {
            "fieldname": "iderp_column_break_1",
            "fieldtype": "Column Break",
            "insert_after": "tipo_vendita_default"
        },
        
        # Configurazioni avanzate
        {
            "fieldname": "larghezza_materiale_default",
            "fieldtype": "Float",
            "label": "Larghezza Materiale Default (cm)",
            "precision": 2,
            "insert_after": "iderp_column_break_1",
            "depends_on": "eval:doc.tipo_vendita_default==='Metro Lineare'",
            "description": "Larghezza predefinita del materiale per vendita a metro lineare"
        },
        {
            "fieldname": "min_order_qty",
            "fieldtype": "Float",
            "label": "Quantità Minima Ordine",
            "precision": 3,
            "insert_after": "larghezza_materiale_default",
            "depends_on": "supports_custom_measurement",
            "description": "Quantità minima ordinabile (m², ml, o pezzi)"
        },
        
        # Help text
        {
            "fieldname": "iderp_help",
            "fieldtype": "HTML",
            "label": "",
            "insert_after": "min_order_qty",
            "options": """
            <div class="alert alert-info" style="margin: 15px 0;">
                <h6><i class="fa fa-lightbulb-o"></i> Configurazione IDERP</h6>
                <ul style="margin: 5px 0; padding-left: 20px;">
                    <li><strong>Misure Personalizzate:</strong> Abilita calcoli automatici e scaglioni prezzo</li>
                    <li><strong>Metro Quadrato:</strong> Calcolo base × altezza (cm) → m²</li>
                    <li><strong>Metro Lineare:</strong> Calcolo lunghezza (cm) → metri lineari</li>
                    <li><strong>Pezzo:</strong> Vendita tradizionale per quantità</li>
                    <li><strong>Scaglioni Prezzo:</strong> Configura prezzi dinamici in base alla quantità</li>
                    <li><strong>Customer Groups:</strong> Imposta minimi diversi per tipo cliente</li>
                </ul>
            </div>
            """,
            "depends_on": "supports_custom_measurement"
        }
    ]
    
    print("   📦 Configurando Item...")
    for cf in custom_fields:
        create_custom_field_v15("Item", cf)

def create_advanced_doctypes():
    """Crea DocTypes avanzati per sistema pricing universale"""
    
    # 1. Item Pricing Tier (Child Table per scaglioni)
    create_item_pricing_tier_doctype()
    
    # 2. Customer Group Minimum (Child Table per minimi)
    create_customer_group_minimum_doctype()
    
    # 3. Customer Group Price Rule (DocType principale)
    create_customer_group_price_rule_doctype()

def create_item_pricing_tier_doctype():
    """Crea Child DocType per scaglioni prezzo universale"""
    
    doctype_name = "Item Pricing Tier"
    
    if frappe.db.exists("DocType", doctype_name):
        print(f"   📊 {doctype_name} già esistente")
        return True
    
    child_doctype = {
        "doctype": "DocType",
        "name": doctype_name,
        "module": "IDERP",
        "custom": 1,
        "istable": 1,
        "editable_grid": 1,
        "track_changes": 0,
        "engine": "InnoDB",
        "fields": [
            # Tipo vendita
            {
                "fieldname": "selling_type",
                "fieldtype": "Select",
                "label": "Tipo Vendita",
                "options": "\nMetro Quadrato\nMetro Lineare\nPezzo",
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2,
                "description": "Tipo di vendita per questo scaglione"
            },
            # Range quantità
            {
                "fieldname": "from_qty",
                "fieldtype": "Float",
                "label": "Da Quantità",
                "precision": 3,
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2,
                "description": "Quantità minima (m², ml, o pezzi)"
            },
            {
                "fieldname": "to_qty",
                "fieldtype": "Float",
                "label": "A Quantità",
                "precision": 3,
                "in_list_view": 1,
                "columns": 2,
                "description": "Quantità massima (vuoto = illimitato)"
            },
            # Prezzo
            {
                "fieldname": "price_per_unit",
                "fieldtype": "Currency",
                "label": "Prezzo per Unità",
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2,
                "description": "€/m², €/ml, o €/pezzo"
            },
            # Metadati
            {
                "fieldname": "tier_name",
                "fieldtype": "Data",
                "label": "Nome Scaglione",
                "in_list_view": 1,
                "columns": 3,
                "description": "Nome descrittivo (es: Piccole tirature, Industriale)"
            },
            {
                "fieldname": "is_default",
                "fieldtype": "Check",
                "label": "Default",
                "columns": 1,
                "description": "Prezzo di fallback per questo tipo vendita"
            }
        ],
        "permissions": [
            {
                "role": "System Manager",
                "read": 1, "write": 1, "create": 1, "delete": 1
            },
            {
                "role": "Sales Manager",
                "read": 1, "write": 1, "create": 1, "delete": 1
            },
            {
                "role": "Sales User",
                "read": 1, "write": 1, "create": 1
            }
        ]
    }
    
    try:
        child_doc = frappe.get_doc(child_doctype)
        child_doc.insert(ignore_permissions=True)
        print(f"   ✅ {doctype_name} creato")
        return True
    except Exception as e:
        print(f"   ❌ Errore creazione {doctype_name}: {e}")
        return False

def create_customer_group_minimum_doctype():
    """Crea Child DocType per minimi customer group universale"""
    
    doctype_name = "Customer Group Minimum"
    
    if frappe.db.exists("DocType", doctype_name):
        print(f"   👥 {doctype_name} già esistente")
        return True
    
    child_doctype = {
        "doctype": "DocType",
        "name": doctype_name,
        "module": "IDERP",
        "custom": 1,
        "istable": 1,
        "editable_grid": 1,
        "track_changes": 0,
        "engine": "InnoDB",
        "fields": [
            # Gruppo e tipo
            {
                "fieldname": "customer_group",
                "fieldtype": "Link",
                "label": "Gruppo Cliente",
                "options": "Customer Group",
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2
            },
            {
                "fieldname": "selling_type",
                "fieldtype": "Select",
                "label": "Tipo Vendita",
                "options": "\nMetro Quadrato\nMetro Lineare\nPezzo",
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2,
                "description": "Tipo vendita per cui si applica questa regola"
            },
            # Quantità minima
            {
                "fieldname": "min_qty",
                "fieldtype": "Float",
                "label": "Quantità Minima",
                "precision": 3,
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2,
                "description": "m², ml, o pezzi minimi fatturabili"
            },
            # Modalità calcolo
            {
                "fieldname": "calculation_mode",
                "fieldtype": "Select",
                "label": "Modalità Calcolo",
                "options": "\nPer Riga\nGlobale Preventivo",
                "default": "Per Riga",
                "in_list_view": 1,
                "columns": 2,
                "description": "Come applicare il minimo"
            },
            # Costi fissi
            {
                "fieldname": "fixed_cost",
                "fieldtype": "Currency",
                "label": "Costo Fisso €",
                "precision": 2,
                "description": "Costo fisso aggiuntivo (setup, trasporto, etc.)"
            },
            {
                "fieldname": "fixed_cost_mode",
                "fieldtype": "Select",
                "label": "Modalità Costo Fisso",
                "options": "\nPer Riga\nPer Preventivo\nPer Item Totale",
                "default": "Per Preventivo",
                "depends_on": "eval:doc.fixed_cost > 0"
            },
            # Controlli
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
                "default": 10
            },
            {
                "fieldname": "description",
                "fieldtype": "Text",
                "label": "Descrizione",
                "description": "Descrizione della regola (es: Setup stampa, Gestione ordine)"
            }
        ],
        "permissions": [
            {
                "role": "System Manager",
                "read": 1, "write": 1, "create": 1, "delete": 1
            },
            {
                "role": "Sales Manager",
                "read": 1, "write": 1, "create": 1, "delete": 1
            },
            {
                "role": "Sales User",
                "read": 1, "write": 1, "create": 1
            }
        ]
    }
    
    try:
        child_doc = frappe.get_doc(child_doctype)
        child_doc.insert(ignore_permissions=True)
        print(f"   ✅ {doctype_name} creato")
        return True
    except Exception as e:
        print(f"   ❌ Errore creazione {doctype_name}: {e}")
        return False

def create_customer_group_price_rule_doctype():
    """Crea DocType principale per regole pricing customer group"""
    
    doctype_name = "Customer Group Price Rule"
    
    if frappe.db.exists("DocType", doctype_name):
        print(f"   📋 {doctype_name} già esistente")
        return True
    
    doctype_def = {
        "doctype": "DocType",
        "name": doctype_name,
        "module": "IDERP",
        "custom": 1,
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
                "fieldname": "enabled",
                "fieldtype": "Check",
                "label": "Abilitato",
                "default": 1,
                "in_list_view": 1
            },
            {
                "fieldname": "min_sqm",
                "fieldtype": "Float",
                "label": "m² Minimi",
                "precision": 3,
                "description": "Metri quadri minimi fatturabili (0 = nessun minimo)"
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
                "read": 1, "write": 1, "create": 1, "delete": 1, "print": 1, "export": 1
            },
            {
                "role": "Sales Manager",
                "read": 1, "write": 1, "create": 1, "delete": 1, "print": 1, "export": 1
            },
            {
                "role": "Sales User",
                "read": 1, "print": 1
            }
        ]
    }
    
    try:
        doc = frappe.get_doc(doctype_def)
        doc.insert(ignore_permissions=True)
        print(f"   ✅ {doctype_name} creato")
        return True
    except Exception as e:
        print(f"   ❌ Errore creazione {doctype_name}: {e}")
        return False

def add_tables_to_item():
    """Aggiunge tabelle Child agli Item"""
    
    item_table_fields = [
        # Scaglioni prezzo
        {
            "fieldname": "pricing_section",
            "fieldtype": "Section Break",
            "label": "🎯 Scaglioni Prezzo Universali",
            "insert_after": "iderp_help",
            "collapsible": 1,
            "depends_on": "supports_custom_measurement",
            "description": "Configura prezzi dinamici per tutti i tipi di vendita"
        },
        {
            "fieldname": "pricing_tiers",
            "fieldtype": "Table",
            "label": "Scaglioni Prezzo",
            "insert_after": "pricing_section",
            "options": "Item Pricing Tier",
            "depends_on": "supports_custom_measurement",
            "description": "Definisci prezzi per Metro Quadrato, Metro Lineare e Pezzo"
        },
        {
            "fieldname": "pricing_help",
            "fieldtype": "HTML",
            "label": "",
            "insert_after": "pricing_tiers",
            "options": """
            <div class="alert alert-success" style="margin: 10px 0;">
                <strong>💡 Scaglioni Universali:</strong><br>
                • <strong>Metro Quadrato:</strong> Prezzi basati sui m² totali dell'ordine<br>
                • <strong>Metro Lineare:</strong> Prezzi basati sui metri lineari totali<br>
                • <strong>Pezzo:</strong> Prezzi basati sul numero di pezzi<br>
                • Ogni tipo può avere scaglioni separati e prezzi indipendenti<br>
                • Spunta "Default" per il prezzo di fallback per ogni tipo
            </div>
            """,
            "depends_on": "supports_custom_measurement"
        },
        
        # Minimi customer group
        {
            "fieldname": "customer_group_minimums_section",
            "fieldtype": "Section Break",
            "label": "👥 Minimi per Gruppo Cliente",
            "insert_after": "pricing_help",
            "collapsible": 1,
            "depends_on": "supports_custom_measurement",
            "description": "Configura minimi diversi per gruppi cliente"
        },
        {
            "fieldname": "customer_group_minimums",
            "fieldtype": "Table",
            "label": "Minimi Gruppo Cliente",
            "insert_after": "customer_group_minimums_section",
            "options": "Customer Group Minimum",
            "depends_on": "supports_custom_measurement",
            "description": "Definisci quantità minime per diversi gruppi cliente"
        },
        {
            "fieldname": "customer_group_help",
            "fieldtype": "HTML",
            "label": "",
            "insert_after": "customer_group_minimums",
            "options": """
            <div class="alert alert-warning" style="margin: 10px 0;">
                <strong>🎯 Minimi per Gruppo Cliente:</strong><br>
                • <strong>Per Riga:</strong> Minimo applicato a ogni singola riga<br>
                • <strong>Globale Preventivo:</strong> Minimo applicato UNA volta sul totale item<br>
                • <strong>Costi Fissi:</strong> Setup, gestione ordine, trasporti<br>
                • Esempio: Finale min 0.5m², Bronze min 0.25m², Gold min 0.1m², Diamond nessun minimo
            </div>
            """,
            "depends_on": "supports_custom_measurement"
        }
    ]
    
    print("   🏗️ Aggiungendo tabelle a Item...")
    for field in item_table_fields:
        create_custom_field_v15("Item", field)

def install_customer_group_system():
    """Installa sistema Customer Groups completo"""
    
    print("   👥 Configurando Customer Groups...")
    
    # Crea gruppi standard
    create_standard_customer_groups()
    
    # Crea clienti demo
    create_demo_customers()

def create_standard_customer_groups():
    """Crea gruppi cliente standard per stampa digitale"""
    
    # Trova gruppo radice
    root_group = get_root_customer_group()
    if not root_group:
        print("      ❌ Impossibile trovare gruppo radice clienti")
        return
    
    groups = [
        {
            "customer_group_name": "Finale",
            "parent_customer_group": root_group,
            "is_group": 0,
            "description": "Clienti finali - minimi più alti per costi setup"
        },
        {
            "customer_group_name": "Bronze",
            "parent_customer_group": root_group,
            "is_group": 0,
            "description": "Clienti Bronze - minimi medi"
        },
        {
            "customer_group_name": "Gold",
            "parent_customer_group": root_group,
            "is_group": 0,
            "description": "Clienti Gold - minimi bassi"
        },
        {
            "customer_group_name": "Diamond",
            "parent_customer_group": root_group,
            "is_group": 0,
            "description": "Clienti Diamond - nessun minimo"
        }
    ]
    
    created_count = 0
    for group_data in groups:
        if not frappe.db.exists("Customer Group", group_data["customer_group_name"]):
            try:
                group_doc = frappe.get_doc({
                    "doctype": "Customer Group",
                    **group_data
                })
                group_doc.insert(ignore_permissions=True)
                created_count += 1
                print(f"      ✅ Gruppo '{group_data['customer_group_name']}' creato")
            except Exception as e:
                print(f"      ❌ Errore gruppo {group_data['customer_group_name']}: {e}")
        else:
            print(f"      📋 Gruppo '{group_data['customer_group_name']}' già esistente")
    
    print(f"      📊 {created_count} nuovi gruppi creati")

def create_demo_customers():
    """Crea clienti demo per ogni gruppo"""
    
    import random
    
    # Trova territorio di default
    default_territory = frappe.db.get_value("Territory", {"is_group": 0}, "name")
    if not default_territory:
        default_territory = "Rest Of The World"
    
    customer_configs = [
        {"name": "Cliente Finale Demo", "group": "Finale", "code": "FINALE-001"},
        {"name": "Studio Grafico Bronze", "group": "Bronze", "code": "BRONZE-001"},
        {"name": "Agenzia Gold Marketing", "group": "Gold", "code": "GOLD-001"},
        {"name": "Tipografia Diamond SRL", "group": "Diamond", "code": "DIAMOND-001"}
    ]
    
    created_count = 0
    for config in customer_configs:
        if not frappe.db.exists("Customer", config["code"]):
            try:
                customer_doc = frappe.get_doc({
                    "doctype": "Customer",
                    "customer_name": config["name"],
                    "customer_code": config["code"],
                    "customer_group": config["group"],
                    "territory": default_territory,
                    "customer_type": "Company"
                })
                customer_doc.insert(ignore_permissions=True)
                created_count += 1
                print(f"      ✅ Cliente '{config['name']}' ({config['group']}) creato")
            except Exception as e:
                print(f"      ❌ Errore cliente {config['name']}: {e}")
        else:
            print(f"      📋 Cliente '{config['code']}' già esistente")
    
    print(f"      📊 {created_count} nuovi clienti demo creati")

def setup_demo_data():
    """Configura dati demo per test immediato"""
    
    print("   🧪 Configurando dati demo...")
    
    # Trova primo item disponibile
    test_item = frappe.db.get_value("Item", {"disabled": 0}, "item_code")
    
    if not test_item:
        print("      ⚠️ Nessun item disponibile per demo")
        return
    
    try:
        item_doc = frappe.get_doc("Item", test_item)
        
        # Abilita misure personalizzate
        item_doc.supports_custom_measurement = 1
        item_doc.tipo_vendita_default = "Metro Quadrato"
        
        # Aggiungi scaglioni demo se non esistono
        if not hasattr(item_doc, 'pricing_tiers') or not item_doc.pricing_tiers:
            
            demo_tiers = [
                # Metro Quadrato
                {"selling_type": "Metro Quadrato", "from_qty": 0.0, "to_qty": 0.5, "price_per_unit": 25.0, "tier_name": "Micro m²"},
                {"selling_type": "Metro Quadrato", "from_qty": 0.5, "to_qty": 2.0, "price_per_unit": 18.0, "tier_name": "Piccolo m²"},
                {"selling_type": "Metro Quadrato", "from_qty": 2.0, "to_qty": None, "price_per_unit": 12.0, "tier_name": "Grande m²", "is_default": 1},
                
                # Metro Lineare
                {"selling_type": "Metro Lineare", "from_qty": 0.0, "to_qty": 5.0, "price_per_unit": 8.0, "tier_name": "Piccolo ml"},
                {"selling_type": "Metro Lineare", "from_qty": 5.0, "to_qty": 20.0, "price_per_unit": 6.0, "tier_name": "Medio ml"},
                {"selling_type": "Metro Lineare", "from_qty": 20.0, "to_qty": None, "price_per_unit": 4.0, "tier_name": "Grande ml", "is_default": 1},
                
                # Pezzo
                {"selling_type": "Pezzo", "from_qty": 1.0, "to_qty": 10.0, "price_per_unit": 5.0, "tier_name": "Retail"},
                {"selling_type": "Pezzo", "from_qty": 10.0, "to_qty": 100.0, "price_per_unit": 3.0, "tier_name": "Wholesale"},
                {"selling_type": "Pezzo", "from_qty": 100.0, "to_qty": None, "price_per_unit": 2.0, "tier_name": "Bulk", "is_default": 1}
            ]
            
            item_doc.pricing_tiers = []
            for tier in demo_tiers:
                item_doc.append("pricing_tiers", tier)
        
        # Aggiungi minimi demo se non esistono
        if not hasattr(item_doc, 'customer_group_minimums') or not item_doc.customer_group_minimums:
            
            existing_groups = ["Finale", "Bronze", "Gold", "Diamond"]
            for group in existing_groups:
                if frappe.db.exists("Customer Group", group):
                    
                    # Metro Quadrato
                    min_mq = 0.5 if group == "Finale" else (0.25 if group == "Bronze" else (0.1 if group == "Gold" else 0))
                    item_doc.append("customer_group_minimums", {
                        "customer_group": group,
                        "selling_type": "Metro Quadrato",
                        "min_qty": min_mq,
                        "calculation_mode": "Globale Preventivo" if group in ["Finale", "Gold"] else "Per Riga",
                        "fixed_cost": 5.0 if group == "Finale" else 0,
                        "fixed_cost_mode": "Per Preventivo",
                        "enabled": 1,
                        "description": f"Minimo m² {group}"
                    })
                    
                    # Metro Lineare
                    min_ml = 2.0 if group == "Finale" else (1.0 if group == "Bronze" else (0.5 if group == "Gold" else 0))
                    item_doc.append("customer_group_minimums", {
                        "customer_group": group,
                        "selling_type": "Metro Lineare",
                        "min_qty": min_ml,
                        "calculation_mode": "Per Riga",
                        "fixed_cost": 3.0 if group == "Finale" else 0,
                        "fixed_cost_mode": "Per Riga",
                        "enabled": 1,
                        "description": f"Minimo ml {group}"
                    })
                    
                    # Pezzo
                    min_pz = 5 if group == "Finale" else (3 if group == "Bronze" else (1 if group == "Gold" else 0))
                    item_doc.append("customer_group_minimums", {
                        "customer_group": group,
                        "selling_type": "Pezzo",
                        "min_qty": min_pz,
                        "calculation_mode": "Per Riga",
                        "fixed_cost": 0,
                        "enabled": 1,
                        "description": f"Minimo pz {group}"
                    })
        
        item_doc.save(ignore_permissions=True)
        print(f"      ✅ Item demo '{test_item}' configurato con scaglioni e minimi")
        
    except Exception as e:
        print(f"      ❌ Errore setup demo item: {e}")

def validate_installation():
    """Validazione completa installazione"""
    
    errors = []
    warnings = []
    
    # Verifica DocTypes
    required_doctypes = ["Item Pricing Tier", "Customer Group Minimum", "Customer Group Price Rule"]
    for dt in required_doctypes:
        if not frappe.db.exists("DocType", dt):
            errors.append(f"DocType '{dt}' mancante")
    
    # Verifica Custom Fields su Quotation Item
    required_fields = ["tipo_vendita", "base", "altezza", "mq_singolo", "mq_calcolati", "note_calcolo"]
    for field in required_fields:
        if not frappe.db.exists("Custom Field", {"dt": "Quotation Item", "fieldname": field}):
            errors.append(f"Campo '{field}' mancante su Quotation Item")
    
    # Verifica Custom Fields su Item
    item_fields = ["supports_custom_measurement", "tipo_vendita_default", "pricing_tiers", "customer_group_minimums"]
    for field in item_fields:
        if not frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": field}):
            errors.append(f"Campo '{field}' mancante su Item")
    
    # Verifica Customer Groups
    groups = ["Finale", "Bronze", "Gold", "Diamond"]
    missing_groups = [g for g in groups if not frappe.db.exists("Customer Group", g)]
    if missing_groups:
        warnings.append(f"Gruppi clienti mancanti: {', '.join(missing_groups)}")
    
    # Verifica item configurati
    configured_items = frappe.db.count("Item", {"supports_custom_measurement": 1})
    if configured_items == 0:
        warnings.append("Nessun item configurato per misure personalizzate")
    
    # Risultato validazione
    if errors:
        print("      ❌ ERRORI CRITICI:")
        for error in errors:
            print(f"         • {error}")
        return False
    elif warnings:
        print("      ⚠️ AVVISI:")
        for warning in warnings:
            print(f"         • {warning}")
        print("      ✅ Installazione OK con avvisi")
        return True
    else:
        print("      ✅ Validazione superata completamente!")
        return True

def show_installation_summary():
    """Mostra riepilogo installazione"""
    
    # Conta elementi installati
    doctypes_count = sum([
        1 for dt in ["Item Pricing Tier", "Customer Group Minimum", "Customer Group Price Rule"]
        if frappe.db.exists("DocType", dt)
    ])
    
    sales_fields_count = frappe.db.count("Custom Field", {"dt": "Quotation Item"})
    item_fields_count = frappe.db.count("Custom Field", {"dt": "Item"})
    groups_count = frappe.db.count("Customer Group", {"name": ["in", ["Finale", "Bronze", "Gold", "Diamond"]]})
    customers_count = frappe.db.count("Customer", {"customer_group": ["in", ["Finale", "Bronze", "Gold", "Diamond"]]})
    configured_items = frappe.db.count("Item", {"supports_custom_measurement": 1})
    
    print("\n📊 RIEPILOGO INSTALLAZIONE:")
    print(f"   • DocTypes installati: {doctypes_count}/3")
    print(f"   • Custom Fields vendita: {sales_fields_count}")
    print(f"   • Custom Fields Item: {item_fields_count}")
    print(f"   • Gruppi clienti: {groups_count}/4")
    print(f"   • Clienti demo: {customers_count}")
    print(f"   • Item configurati: {configured_items}")
    
    print("\n🚀 PROSSIMI PASSI:")
    print("   1. Vai su Item → Abilita 'Supporta Misure Personalizzate'")
    print("   2. Configura scaglioni prezzo nella tabella 'Scaglioni Prezzo'")
    print("   3. Imposta minimi per gruppo nella tabella 'Minimi Gruppo Cliente'")
    print("   4. Crea una Quotation con clienti diversi per testare")
    print("   5. Verifica calcoli automatici e minimi applicati")
    
    print("\n💡 DEMO RAPIDO:")
    if configured_items > 0:
        demo_item = frappe.db.get_value("Item", {"supports_custom_measurement": 1}, "item_code")
        print(f"   • Item demo configurato: {demo_item}")
        print("   • Clienti demo: FINALE-001, BRONZE-001, GOLD-001, DIAMOND-001")
        print("   • Test: Crea Quotation con misure 30×40cm = 0.12 m²")
        print("   • Risultato atteso: minimi diversi per gruppo cliente")

# ================================
# UTILITY FUNCTIONS
# ================================

def create_custom_field_v15(doctype, field_dict):
    """Crea Custom Field compatibile ERPNext 15"""
    
    if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field_dict["fieldname"]}):
        try:
            cf_doc = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": doctype,
                **field_dict
            })
            cf_doc.insert(ignore_permissions=True)
            # Force commit per ERPNext 15
            frappe.db.commit()
            print(f"         ✅ {field_dict['fieldname']}")
        except Exception as e:
            print(f"         ❌ {field_dict['fieldname']}: {str(e)}")
    else:
        print(f"         📋 {field_dict['fieldname']} (già esistente)")

def get_root_customer_group():
    """Trova gruppo cliente radice"""
    
    # Cerca gruppo radice (senza parent)
    root_groups = frappe.get_all("Customer Group",
        filters={"is_group": 1},
        fields=["name", "parent_customer_group"],
        order_by="creation"
    )
    
    for group in root_groups:
        if not group.parent_customer_group:
            return group.name
    
    # Se non trova, usa il primo disponibile
    if root_groups:
        return root_groups[0].name
    
    # Ultima risorsa: crea gruppo radice
    try:
        root_doc = frappe.get_doc({
            "doctype": "Customer Group",
            "customer_group_name": "All Customer Groups",
            "is_group": 1
        })
        root_doc.insert(ignore_permissions=True)
        return "All Customer Groups"
    except:
        return None

# ================================
# COMMAND SHORTCUTS
# ================================

def reinstall_all():
    """Reinstallazione completa"""
    print("[IDERP] Reinstallazione completa...")
    after_install()

def quick_validation():
    """Validazione rapida"""
    return validate_installation()

def show_status():
    """Mostra stato installazione"""
    show_installation_summary()

# Alias per console
ri = reinstall_all
qv = quick_validation
ss = show_status