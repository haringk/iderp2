import frappe

def after_install():
    """Installazione completa plugin iderp"""
    print("[iderp] === Iniziando installazione plugin ===")
    
    # 1. Installa campi custom per documenti di vendita
    install_sales_custom_fields()
    
    # 2. Installa campi custom per configurazione Item
    install_item_config_fields()
    
    # 3. Crea Child Table per scaglioni prezzo
    create_item_pricing_tier_child_table()
    
    # 4. Aggiunge tabella scaglioni all'Item
    add_pricing_table_to_item()
    
    # 5. NUOVO: Installa sistema Customer Group Pricing
    install_customer_group_pricing_system()
    
    print("[iderp] === Installazione completata ===")
    print("[iderp] ✓ Vendita al pezzo")
    print("[iderp] ✓ Vendita al metro quadrato con scaglioni") 
    print("[iderp] ✓ Vendita al metro lineare")
    print("[iderp] ✓ Configurazione Item con scaglioni prezzo")
    print("[iderp] ✓ NUOVO: Customer Group Pricing con minimi")
    print("[iderp] ✓ Gruppi: Finale, Bronze, Gold, Diamond")
    print("[iderp] ✓ Sistema completo pronto all'uso")

def install_customer_group_pricing_system():
    """Installa il sistema Customer Group Pricing semplificato"""
    print("[iderp] Installando Customer Group Pricing...")
    
    from iderp.customer_group_pricing import setup_complete_customer_groups
    
    # Setup completo: DocType, gruppi, clienti, regole
    setup_complete_customer_groups()
    
    print("[iderp] ✓ Customer Group Pricing installato")

def install_sales_custom_fields():
    """Installa campi custom per documenti di vendita"""
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
        
        # NUOVO: Campo per customer group rules
        {
            "fieldname": "customer_group_rules_applied",
            "label": "Regole Gruppo Applicate",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "note_calcolo",
            "description": "Indica se sono state applicate regole del gruppo cliente"
        }
    ]
    
    for dt in doctypes:
        for cf in custom_fields:
            create_custom_field(dt, cf)

def install_item_config_fields():
    """Installa campi custom per configurazione Item base"""
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
            "depends_on": "eval:doc.tipo_vendita_default=='Metro Lineare'",
        },
    ]
    
    for cf in custom_fields:
        create_custom_field("Item", cf)

def create_item_pricing_tier_child_table():
    """Crea Child Table per scaglioni prezzo"""
    print("[iderp] Creando Child Table per scaglioni...")
    
    # Verifica se esiste già
    if frappe.db.exists("DocType", "Item Pricing Tier"):
        print("[iderp] - Child Table già esistente")
        return True
    
    child_doctype = {
        "doctype": "DocType",
        "name": "Item Pricing Tier",
        "module": "Custom",
        "custom": 1,
        "istable": 1,
        "editable_grid": 1,
        "track_changes": 0,
        "engine": "InnoDB",
        "fields": [
            {
                "fieldname": "from_sqm",
                "fieldtype": "Float",
                "label": "Da m²",
                "precision": 3,
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2,
                "description": "Metri quadri minimi"
            },
            {
                "fieldname": "to_sqm",
                "fieldtype": "Float", 
                "label": "A m²",
                "precision": 3,
                "in_list_view": 1,
                "columns": 2,
                "description": "Metri quadri massimi (vuoto = illimitato)"
            },
            {
                "fieldname": "price_per_sqm",
                "fieldtype": "Currency",
                "label": "€/m²",
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2,
                "description": "Prezzo per metro quadrato"
            },
            {
                "fieldname": "tier_name",
                "fieldtype": "Data",
                "label": "Nome Scaglione",
                "in_list_view": 1,
                "columns": 3,
                "description": "Es: Piccole tirature, Industriale, ecc."
            },
            {
                "fieldname": "is_default",
                "fieldtype": "Check",
                "label": "Default",
                "columns": 1,
                "description": "Prezzo di fallback"
            }
        ],
        "permissions": [
            {
                "role": "System Manager",
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1
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
        child_doc = frappe.get_doc(child_doctype)
        child_doc.insert(ignore_permissions=True)
        print("[iderp] ✓ Child Table 'Item Pricing Tier' creata")
        return True
    except Exception as e:
        print(f"[iderp] ✗ Errore creazione Child Table: {e}")
        return False

def add_pricing_table_to_item():
    """Aggiunge la tabella scaglioni all'Item"""
    print("[iderp] Aggiungendo tabella scaglioni all'Item...")
    
    item_fields = [
        {
            "fieldname": "pricing_section",
            "fieldtype": "Section Break",
            "label": "Scaglioni Prezzo m²",
            "insert_after": "larghezza_materiale_default",
            "collapsible": 1,
            "depends_on": "eval:doc.supports_custom_measurement && doc.tipo_vendita_default=='Metro Quadrato'",
            "description": "Configura prezzi diversi in base ai metri quadri totali dell'ordine"
        },
        {
            "fieldname": "pricing_tiers",
            "fieldtype": "Table",
            "label": "Scaglioni Prezzo",
            "insert_after": "pricing_section",
            "options": "Item Pricing Tier",
            "depends_on": "eval:doc.supports_custom_measurement && doc.tipo_vendita_default=='Metro Quadrato'",
            "description": "Definisci prezzi per fasce di metri quadri"
        },
        {
            "fieldname": "pricing_help",
            "fieldtype": "HTML",
            "label": "",
            "insert_after": "pricing_tiers",
            "options": """
            <div class="alert alert-info">
                <strong>💡 Come funzionano gli scaglioni:</strong><br>
                • I prezzi si applicano in base ai <strong>metri quadri totali</strong> dell'ordine<br>
                • Esempio: 0-10m² = €10/m², 10-50m² = €8/m², oltre 50m² = €6/m²<br>
                • Il sistema sceglierà automaticamente il prezzo giusto<br>
                • Lascia "A m²" vuoto per indicare "oltre X metri quadri"<br>
                • Spunta "Default" per il prezzo di fallback
            </div>
            """,
            "depends_on": "eval:doc.supports_custom_measurement && doc.tipo_vendita_default=='Metro Quadrato'"
        }
    ]
    
    for field in item_fields:
        create_custom_field("Item", field)

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

def create_sample_pricing_for_item(item_code):
    """Crea scaglioni di esempio per un item"""
    print(f"[iderp] Creando scaglioni esempio per {item_code}...")
    
    if not frappe.db.exists("Item", item_code):
        print(f"[iderp] ✗ Item {item_code} non trovato")
        return False
    
    try:
        item_doc = frappe.get_doc("Item", item_code)
        
        # Abilita misure personalizzate
        item_doc.supports_custom_measurement = 1
        item_doc.tipo_vendita_default = "Metro Quadrato"
        
        # Scaglioni di esempio specifici per stampa digitale
        sample_tiers = [
            {
                "from_sqm": 0,
                "to_sqm": 0.25,
                "price_per_sqm": 20.0,
                "tier_name": "Micro tirature"
            },
            {
                "from_sqm": 0.25,
                "to_sqm": 1,
                "price_per_sqm": 15.0,
                "tier_name": "Piccole tirature"
            },
            {
                "from_sqm": 1,
                "to_sqm": 5,
                "price_per_sqm": 12.0,
                "tier_name": "Tirature medie"
            },
            {
                "from_sqm": 5,
                "to_sqm": None,
                "price_per_sqm": 8.0,
                "tier_name": "Tirature grandi",
                "is_default": 1
            }
        ]
        
        # Pulisci e aggiungi scaglioni
        item_doc.pricing_tiers = []
        for tier_data in sample_tiers:
            item_doc.append("pricing_tiers", tier_data)
        
        item_doc.save(ignore_permissions=True)
        print(f"[iderp] ✓ Scaglioni esempio creati per {item_code}")
        return True
        
    except Exception as e:
        print(f"[iderp] ✗ Errore creazione scaglioni: {e}")
        return False

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
    
    if items:
        print(f"[iderp] Per test: create_sample_pricing_for_item('{items[0].item_code}')")
    
    return items

def quick_test_setup():
    """Setup rapido per test con primo item disponibile"""
    print("[iderp] === Setup rapido per test ===")
    
    # Mostra item disponibili
    items = show_available_items()
    
    if items:
        # Prendi il primo item e crea scaglioni
        test_item = items[0].item_code
        print(f"[iderp] Configurando {test_item} per test...")
        
        if create_sample_pricing_for_item(test_item):
            print(f"[iderp] ✓ Setup test completato!")
            print(f"[iderp] Vai su Item → {test_item} → Scaglioni Prezzo m²")
            print(f"[iderp] Poi testa in una Quotation con diversi Customer Group")
            return test_item
    else:
        print("[iderp] ✗ Nessun item disponibile per test")
        return None

def validate_installation():
    """Valida che l'installazione sia corretta"""
    print("[iderp] === Validazione installazione ===")
    
    errors = []
    
    # Verifica Child DocType
    if not frappe.db.exists("DocType", "Item Pricing Tier"):
        errors.append("DocType 'Item Pricing Tier' mancante")
    
    # Verifica campi su Quotation Item
    required_fields = ["tipo_vendita", "base", "altezza", "mq_singolo", "mq_calcolati"]
    for field in required_fields:
        if not frappe.db.exists("Custom Field", {"dt": "Quotation Item", "fieldname": field}):
            errors.append(f"Campo {field} mancante su Quotation Item")
    
    # Verifica campi su Item
    item_fields = ["supports_custom_measurement", "tipo_vendita_default", "pricing_tiers"]
    for field in item_fields:
        if not frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": field}):
            errors.append(f"Campo {field} mancante su Item")
    
    if errors:
        print("[iderp] ✗ Errori trovati:")
        for error in errors:
            print(f"[iderp]   - {error}")
        return False
    else:
        print("[iderp] ✓ Installazione valida!")
        return True

def get_installation_status():
    """Ottieni stato dettagliato dell'installazione"""
    print("[iderp] === Stato installazione ===")
    
    # Child DocType
    has_child_doctype = frappe.db.exists("DocType", "Item Pricing Tier")
    print(f"[iderp] Child DocType: {'✓' if has_child_doctype else '✗'}")
    
    # Campi vendita
    sales_fields = ["tipo_vendita", "base", "altezza", "mq_singolo", "mq_calcolati", "note_calcolo"]
    for field in sales_fields:
        has_field = frappe.db.exists("Custom Field", {"dt": "Quotation Item", "fieldname": field})
        print(f"[iderp] Campo {field}: {'✓' if has_field else '✗'}")
    
    # Campi Item
    item_fields = ["supports_custom_measurement", "pricing_tiers"]
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