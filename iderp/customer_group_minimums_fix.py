# iderp/customer_group_minimums_fix.py
"""
FIX CRITICO: Aggiunge Child Table Customer Group Minimums all'Item
Risolve l'inconsistenza tra JavaScript e database
"""

import frappe

def install_customer_group_minimums_child_table():
    """
    Installa la Child Table Customer Group Minimums che manca sull'Item
    Questa è necessaria per far funzionare il JavaScript che cerca item_config.customer_group_minimums
    """
    print("[iderp] === FIX: Installando Customer Group Minimums Child Table ===")
    
    # 1. Crea Child DocType Customer Group Minimum
    create_customer_group_minimum_child_doctype()
    
    # 2. Aggiunge campo tabella all'Item  
    add_customer_group_minimums_table_to_item()
    
    # 3. Test setup
    test_customer_group_minimums_setup()
    
    print("[iderp] ✅ Fix Customer Group Minimums completato!")

def create_customer_group_minimum_child_doctype():
    """Crea il Child DocType per Customer Group Minimum con minimi globali"""
    
    doctype_name = "Customer Group Minimum"
    
    if frappe.db.exists("DocType", doctype_name):
        print(f"[iderp] - Child DocType '{doctype_name}' già esistente")
        # Aggiungi nuovo campo se non esiste
        add_global_minimum_fields()
        return True
    
    child_doctype = {
        "doctype": "DocType",
        "name": doctype_name,
        "module": "Custom", 
        "custom": 1,
        "istable": 1,
        "editable_grid": 1,
        "track_changes": 0,
        "engine": "InnoDB",
        "fields": [
            {
                "fieldname": "customer_group",
                "fieldtype": "Link",
                "label": "Gruppo Cliente",
                "options": "Customer Group",
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2,
                "description": "Gruppo cliente per cui si applica il minimo"
            },
            {
                "fieldname": "min_sqm",
                "fieldtype": "Float",
                "label": "Minimo m²",
                "precision": 3,
                "reqd": 1,
                "in_list_view": 1,
                "columns": 2,
                "description": "Metri quadri minimi fatturabili per questo gruppo"
            },
            {
                "fieldname": "calculation_mode",
                "fieldtype": "Select",
                "label": "Modalità Calcolo",
                "options": "\nPer Riga\nGlobale Preventivo",
                "default": "Per Riga",
                "in_list_view": 1,
                "columns": 2,
                "description": "Come applicare il minimo: per singola riga o globalmente sul preventivo"
            },
            {
                "fieldname": "enabled",
                "fieldtype": "Check",
                "label": "Abilitato",
                "default": 1,
                "in_list_view": 1,
                "columns": 1,
                "description": "Abilita questa regola"
            },
            {
                "fieldname": "description",
                "fieldtype": "Data",
                "label": "Descrizione",
                "in_list_view": 1,
                "columns": 3,
                "description": "Descrizione del minimo (es: 'Costi fissi setup')"
            },
            {
                "fieldname": "priority",
                "fieldtype": "Int",
                "label": "Priorità",
                "default": 10,
                "columns": 1,
                "description": "Priorità applicazione (maggiore = prima)"
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
        print(f"[iderp] ✓ Child DocType '{doctype_name}' creato con minimi globali")
        return True
    except Exception as e:
        print(f"[iderp] ✗ Errore creazione Child DocType: {e}")
        return False

def add_global_minimum_fields():
    """Aggiungi campo calculation_mode se non esiste"""
    
    # Verifica se il campo esiste già
    existing_field = frappe.db.sql("""
        SELECT fieldname FROM `tabDocField` 
        WHERE parent = 'Customer Group Minimum' 
        AND fieldname = 'calculation_mode'
    """)
    
    if existing_field:
        print("[iderp] - Campo 'calculation_mode' già presente")
        return True
    
    try:
        # Aggiungi il campo al DocType esistente
        doctype_doc = frappe.get_doc("DocType", "Customer Group Minimum")
        
        # Trova posizione dopo min_sqm
        insert_idx = 0
        for i, field in enumerate(doctype_doc.fields):
            if field.fieldname == "min_sqm":
                insert_idx = i + 1
                break
        
        # Aggiungi nuovo campo
        new_field = {
            "fieldname": "calculation_mode",
            "fieldtype": "Select",
            "label": "Modalità Calcolo",
            "options": "\nPer Riga\nGlobale Preventivo",
            "default": "Per Riga",
            "in_list_view": 1,
            "columns": 2,
            "description": "Come applicare il minimo: per singola riga o globalmente sul preventivo",
            "idx": insert_idx + 1
        }
        
        doctype_doc.insert(insert_idx, "fields", new_field)
        doctype_doc.save()
        
        print("[iderp] ✓ Campo 'calculation_mode' aggiunto")
        return True
        
    except Exception as e:
        print(f"[iderp] ✗ Errore aggiunta campo: {e}")
        return False

def add_customer_group_minimums_table_to_item():
    """Aggiunge la tabella customer_group_minimums all'Item"""
    
    print("[iderp] Aggiungendo tabella Customer Group Minimums all'Item...")
    
    # Campi da aggiungere all'Item
    item_fields = [
        {
            "fieldname": "customer_group_minimums_section",
            "fieldtype": "Section Break",
            "label": "Minimi per Gruppo Cliente",
            "insert_after": "pricing_help",
            "collapsible": 1,
            "depends_on": "eval:doc.supports_custom_measurement && doc.tipo_vendita_default=='Metro Quadrato'",
            "description": "Configura minimi metri quadri per diversi gruppi cliente"
        },
        {
            "fieldname": "customer_group_minimums",
            "fieldtype": "Table",
            "label": "Minimi Gruppo Cliente",
            "insert_after": "customer_group_minimums_section",
            "options": "Customer Group Minimum",
            "depends_on": "eval:doc.supports_custom_measurement && doc.tipo_vendita_default=='Metro Quadrato'",
            "description": "Definisci minimi m² per diversi gruppi cliente"
        },
        {
            "fieldname": "customer_group_minimums_help",
            "fieldtype": "HTML",
            "label": "",
            "insert_after": "customer_group_minimums",
            "options": """
            <div class="alert alert-info">
                <strong>💡 Come funzionano i minimi per gruppo:</strong><br>
                • I minimi si applicano in base al <strong>gruppo del cliente</strong><br>
                • Esempio: Finale min 0.5m², Bronze min 0.25m², Gold min 0.1m², Diamond nessun minimo<br>
                • Se l'ordine è sotto il minimo, viene fatturato il minimo<br>
                • I minimi si sommano agli scaglioni prezzo sopra<br>
                • Utile per coprire costi fissi di setup/preparazione
            </div>
            """,
            "depends_on": "eval:doc.supports_custom_measurement && doc.tipo_vendita_default=='Metro Quadrato'"
        }
    ]
    
    # Installa i campi
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

def test_customer_group_minimums_setup():
    """Test che la Child Table sia correttamente installata"""
    print("[iderp] Testando setup Customer Group Minimums...")
    
    errors = []
    
    # 1. Verifica Child DocType
    if not frappe.db.exists("DocType", "Customer Group Minimum"):
        errors.append("Child DocType 'Customer Group Minimum' mancante")
    
    # 2. Verifica campo tabella su Item
    if not frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "customer_group_minimums"}):
        errors.append("Campo 'customer_group_minimums' mancante su Item")
    
    # 3. Verifica che il campo sia di tipo Table
    field_info = frappe.db.get_value("Custom Field", 
        {"dt": "Item", "fieldname": "customer_group_minimums"}, 
        ["fieldtype", "options"], as_dict=True
    )
    
    if field_info:
        if field_info.fieldtype != "Table":
            errors.append(f"Campo 'customer_group_minimums' è {field_info.fieldtype}, dovrebbe essere Table")
        if field_info.options != "Customer Group Minimum":
            errors.append(f"Campo 'customer_group_minimums' options è '{field_info.options}', dovrebbe essere 'Customer Group Minimum'")
    
    if errors:
        print("[iderp] ✗ Errori nel setup:")
        for error in errors:
            print(f"[iderp]   - {error}")
        return False
    else:
        print("[iderp] ✅ Setup Customer Group Minimums validato!")
        return True

def create_sample_customer_group_minimums_for_item(item_code):
    """Crea minimi di esempio per un item"""
    
    if not frappe.db.exists("Item", item_code):
        print(f"[iderp] ✗ Item {item_code} non trovato")
        return False
    
    print(f"[iderp] Creando minimi esempio per item {item_code}...")
    
    try:
        item_doc = frappe.get_doc("Item", item_code)
        
        # Abilita misure personalizzate se non abilitato
        if not getattr(item_doc, 'supports_custom_measurement', 0):
            item_doc.supports_custom_measurement = 1
            item_doc.tipo_vendita_default = "Metro Quadrato"
        
        # Minimi di esempio per stampa digitale
        sample_minimums = [
            {
                "customer_group": "Finale",
                "min_sqm": 0.5,
                "enabled": 1,
                "description": "Clienti finali - costi setup minimo",
                "priority": 10
            },
            {
                "customer_group": "Bronze", 
                "min_sqm": 0.25,
                "enabled": 1,
                "description": "Clienti Bronze - setup ridotto",
                "priority": 20
            },
            {
                "customer_group": "Gold",
                "min_sqm": 0.1,
                "enabled": 1, 
                "description": "Clienti Gold - setup minimo",
                "priority": 30
            },
            {
                "customer_group": "Diamond",
                "min_sqm": 0,
                "enabled": 1,
                "description": "Clienti Diamond - nessun minimo",
                "priority": 40
            }
        ]
        
        # Verifica che i gruppi esistano
        existing_groups = []
        for minimum in sample_minimums:
            if frappe.db.exists("Customer Group", minimum["customer_group"]):
                existing_groups.append(minimum)
            else:
                print(f"[iderp] - Gruppo {minimum['customer_group']} non esiste, saltato")
        
        if not existing_groups:
            print("[iderp] ✗ Nessun gruppo cliente configurato")
            return False
        
        # Pulisci e aggiungi minimi
        item_doc.customer_group_minimums = []
        for minimum_data in existing_groups:
            item_doc.append("customer_group_minimums", minimum_data)
        
        item_doc.save(ignore_permissions=True)
        
        print(f"[iderp] ✓ {len(existing_groups)} minimi gruppo cliente creati per {item_code}")
        for minimum in existing_groups:
            print(f"[iderp]   • {minimum['customer_group']}: min {minimum['min_sqm']} m²")
        
        return True
        
    except Exception as e:
        print(f"[iderp] ✗ Errore creazione minimi: {e}")
        return False

def migrate_existing_customer_group_rules_to_item_minimums():
    """
    Migra le regole esistenti da Customer Group Price Rule alle tabelle degli Item
    Questo mantiene compatibilità con dati esistenti
    """
    print("[iderp] Migrando regole esistenti a Item Minimums...")
    
    # Ottieni tutte le regole esistenti
    existing_rules = frappe.db.sql("""
        SELECT customer_group, item_code, min_sqm, notes, enabled
        FROM `tabCustomer Group Price Rule`
        WHERE min_sqm > 0
        ORDER BY item_code, customer_group
    """, as_dict=True)
    
    if not existing_rules:
        print("[iderp] - Nessuna regola esistente da migrare")
        return True
    
    migrated_items = {}
    
    for rule in existing_rules:
        item_code = rule.item_code
        
        if item_code not in migrated_items:
            migrated_items[item_code] = []
        
        # Aggiungi alla lista per questo item
        migrated_items[item_code].append({
            "customer_group": rule.customer_group,
            "min_sqm": rule.min_sqm,
            "enabled": rule.enabled or 1,
            "description": rule.notes or f"Migrato da regola {rule.customer_group}",
            "priority": 10
        })
    
    # Applica le migrazioni
    migrated_count = 0
    for item_code, minimums in migrated_items.items():
        try:
            if not frappe.db.exists("Item", item_code):
                print(f"[iderp] - Item {item_code} non trovato, saltato")
                continue
            
            item_doc = frappe.get_doc("Item", item_code)
            
            # Abilita misure personalizzate
            if not getattr(item_doc, 'supports_custom_measurement', 0):
                item_doc.supports_custom_measurement = 1
                item_doc.tipo_vendita_default = "Metro Quadrato"
            
            # Pulisci e aggiungi minimi migrati
            item_doc.customer_group_minimums = []
            for minimum_data in minimums:
                item_doc.append("customer_group_minimums", minimum_data)
            
            item_doc.save(ignore_permissions=True)
            migrated_count += 1
            
            print(f"[iderp] ✓ Migrato {item_code}: {len(minimums)} minimi")
            
        except Exception as e:
            print(f"[iderp] ✗ Errore migrazione {item_code}: {e}")
    
    print(f"[iderp] ✅ Migrazione completata: {migrated_count} item aggiornati")
    return migrated_count > 0

def show_customer_group_minimums_status():
    """Mostra stato del sistema Customer Group Minimums"""
    print("\n" + "="*60)
    print("📊 STATO CUSTOMER GROUP MINIMUMS")
    print("="*60)
    
    # Verifica installazione
    has_child_doctype = frappe.db.exists("DocType", "Customer Group Minimum")
    has_item_field = frappe.db.exists("Custom Field", {"dt": "Item", "fieldname": "customer_group_minimums"})
    
    print(f"\n🔧 INSTALLAZIONE:")
    print(f"   Child DocType: {'✅' if has_child_doctype else '❌'}")
    print(f"   Campo Item: {'✅' if has_item_field else '❌'}")
    
    if not (has_child_doctype and has_item_field):
        print("\n❌ Sistema non installato correttamente!")
        print("💡 Esegui: install_customer_group_minimums_child_table()")
        return False
    
    # Item configurati
    print(f"\n📦 ITEM CON MINIMI:")
    items_with_minimums = frappe.db.sql("""
        SELECT i.item_code, i.item_name,
               (SELECT COUNT(*) FROM `tabCustomer Group Minimum` 
                WHERE parent = i.name AND enabled = 1) as minimums_count
        FROM `tabItem` i
        WHERE i.supports_custom_measurement = 1
        AND EXISTS (SELECT 1 FROM `tabCustomer Group Minimum` WHERE parent = i.name)
        LIMIT 10
    """, as_dict=True)
    
    if items_with_minimums:
        for item in items_with_minimums:
            print(f"   • {item.item_code}: {item.minimums_count} minimi configurati")
    else:
        print("   ⚠️  Nessun item con minimi configurato")
    
    # Dettaglio minimi
    if items_with_minimums:
        print(f"\n📏 DETTAGLIO MINIMI:")
        minimums_detail = frappe.db.sql("""
            SELECT cgm.parent as item_code, cgm.customer_group, cgm.min_sqm, cgm.enabled
            FROM `tabCustomer Group Minimum` cgm
            JOIN `tabItem` i ON i.name = cgm.parent
            WHERE i.supports_custom_measurement = 1
            ORDER BY cgm.parent, cgm.customer_group
            LIMIT 20
        """, as_dict=True)
        
        current_item = None
        for minimum in minimums_detail:
            if minimum.item_code != current_item:
                print(f"\n   📦 {minimum.item_code}:")
                current_item = minimum.item_code
            
            status = "✅" if minimum.enabled else "❌"
            print(f"      {status} {minimum.customer_group}: {minimum.min_sqm} m²")
    
    print("="*60)
    return True

# Comandi rapidi per console
def fix_install():
    """Comando rapido: Installa fix Child Table"""
    install_customer_group_minimums_child_table()

def fix_test():
    """Comando rapido: Test setup"""
    return test_customer_group_minimums_setup()

def fix_status():
    """Comando rapido: Stato sistema"""
    show_customer_group_minimums_status()

def fix_migrate():
    """Comando rapido: Migra regole esistenti"""
    return migrate_existing_customer_group_rules_to_item_minimums()

def fix_sample(item_code=None):
    """Comando rapido: Crea minimi esempio"""
    if not item_code:
        # Prendi primo item disponibile
        item_code = frappe.db.get_value("Item", {"disabled": 0}, "item_code")
    
    if item_code:
        return create_sample_customer_group_minimums_for_item(item_code)
    else:
        print("❌ Nessun item disponibile")
        return False

def fix_complete_scenario():
    """Scenario completo: installa + migra + test"""
    print("\n" + "="*60)
    print("🔧 FIX COMPLETO CUSTOMER GROUP MINIMUMS")
    print("="*60)
    
    # 1. Installa Child Table
    install_customer_group_minimums_child_table()
    
    # 2. Migra dati esistenti
    migrate_existing_customer_group_rules_to_item_minimums()
    
    # 3. Test setup
    if test_customer_group_minimums_setup():
        print("\n✅ FIX COMPLETATO CON SUCCESSO!")
        print("💡 Ora il JavaScript può accedere a item_config.customer_group_minimums")
        print("🧪 Test: fix_status() per verificare")
        return True
    else:
        print("\n❌ Fix fallito")
        return False

# Help
def fix_help():
    """Mostra comandi disponibili per il fix"""
    print("\n" + "="*60)
    print("🔧 COMANDI FIX CUSTOMER GROUP MINIMUMS")
    print("="*60)
    print("\n🚀 INSTALLAZIONE:")
    print("   fix_install()           → Installa Child Table")
    print("   fix_complete_scenario() → Fix completo")
    print("\n🧪 TESTING:")
    print("   fix_test()    → Test setup")
    print("   fix_status()  → Stato sistema")
    print("\n📊 DATI:")
    print("   fix_migrate()      → Migra regole esistenti")
    print("   fix_sample('ABC')  → Crea minimi esempio per item")
    print("\n💡 ESEMPIO UTILIZZO:")
    print("   >>> from iderp.customer_group_minimums_fix import *")
    print("   >>> fix_complete_scenario()")
    print("="*60)

# Alias
fi = fix_install
ft = fix_test
fs = fix_status
fm = fix_migrate
fcs = fix_complete_scenario
fh = fix_help