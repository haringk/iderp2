# iderp/customer_group_pricing.py
"""
Gestione prezzi differenziati per gruppo cliente
Versione corretta con verifica gruppo radice
"""

import frappe
from frappe import _
import random

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
        if not item.item_code or item.tipo_vendita != "Metro Quadrato":
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
        if rule.get("min_sqm") and rule["min_sqm"] > 0:
            if item.mq_calcolati < rule["min_sqm"]:
                # Calcola come se fossero i m² minimi
                old_mq = item.mq_calcolati
                effective_mq = rule["min_sqm"]
                
                # Ricalcola prezzo con m² minimi
                if item.prezzo_mq:
                    # Mantieni la quantità originale ma calcola su m² minimi
                    new_rate = (effective_mq / item.qty) * item.prezzo_mq if item.qty > 0 else 0
                    item.rate = new_rate
                    
                    item.note_calcolo += f"\n⚠️ MINIMO GRUPPO {rule['customer_group'].upper()}: {rule['min_sqm']} m²"
                    item.note_calcolo += f"\n📊 Fatturato su {effective_mq} m² invece di {old_mq:.3f} m²"

def get_root_customer_group():
    """
    Trova il gruppo cliente radice in ERPNext
    """
    # Prova diversi nomi possibili per il gruppo radice
    possible_roots = [
        "All Customer Groups",
        "All Customer Groups", 
        "",  # Gruppo vuoto
        None
    ]
    
    # Cerca il gruppo con is_group=1 e parent_customer_group vuoto o None
    root_groups = frappe.get_all("Customer Group", 
        filters={"is_group": 1}, 
        fields=["name", "parent_customer_group"],
        order_by="creation"
    )
    
    for group in root_groups:
        if not group.parent_customer_group or group.parent_customer_group == "":
            print(f"[iderp] Gruppo radice trovato: '{group.name}'")
            return group.name
    
    # Se non trova nessun gruppo radice, usa il primo gruppo disponibile
    if root_groups:
        print(f"[iderp] Usando primo gruppo disponibile: '{root_groups[0].name}'")
        return root_groups[0].name
    
    # Se non ci sono gruppi, crea quello di default
    print("[iderp] Creando gruppo radice di default...")
    try:
        root_doc = frappe.get_doc({
            "doctype": "Customer Group",
            "customer_group_name": "All Customer Groups",
            "is_group": 1
        })
        root_doc.insert(ignore_permissions=True)
        print("[iderp] ✓ Gruppo radice 'All Customer Groups' creato")
        return "All Customer Groups"
    except Exception as e:
        print(f"[iderp] ✗ Errore creazione gruppo radice: {e}")
        return None

def create_customer_group_price_rule_doctype():
    """Crea il DocType per le regole gruppo cliente"""
    
    if frappe.db.exists("DocType", "Customer Group Price Rule"):
        print("[iderp] - DocType 'Customer Group Price Rule' già esistente")
        return True
    
    # Crea il DocType principale
    doc = frappe.get_doc({
        "doctype": "DocType",
        "name": "Customer Group Price Rule",
        "module": "Custom",
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
                "label": "Minimi Metro Quadro"
            },
            {
                "fieldname": "min_sqm",
                "fieldtype": "Float",
                "label": "m² Minimi",
                "precision": 3,
                "description": "Metri quadri minimi fatturabili (0 = nessun minimo)"
            },
            {
                "fieldname": "section_break_2",
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
    
    try:
        doc.insert(ignore_permissions=True)
        print("[iderp] ✓ DocType 'Customer Group Price Rule' creato")
        return True
    except Exception as e:
        print(f"[iderp] ✗ Errore creazione DocType: {e}")
        return False

def install_customer_group_fields():
    """Installa campi per supporto gruppi cliente"""
    
    from iderp_module.install import create_custom_field
    
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

def create_customer_groups():
    """
    Crea i 4 gruppi cliente: finale, bronze, gold, diamond
    CORRETTO: Usa il gruppo radice corretto
    """
    
    # Trova il gruppo radice corretto
    root_group = get_root_customer_group()
    if not root_group:
        print("[iderp] ✗ Impossibile determinare gruppo cliente radice")
        return []
    
    print(f"[iderp] Usando gruppo padre: '{root_group}'")
    
    groups = [
        {
            "customer_group_name": "Finale",
            "parent_customer_group": root_group,
            "is_group": 0
        },
        {
            "customer_group_name": "Bronze", 
            "parent_customer_group": root_group,
            "is_group": 0
        },
        {
            "customer_group_name": "Gold",
            "parent_customer_group": root_group, 
            "is_group": 0
        },
        {
            "customer_group_name": "Diamond",
            "parent_customer_group": root_group,
            "is_group": 0
        }
    ]
    
    created_groups = []
    
    for group_data in groups:
        if not frappe.db.exists("Customer Group", group_data["customer_group_name"]):
            try:
                group_doc = frappe.get_doc({
                    "doctype": "Customer Group",
                    **group_data
                })
                group_doc.insert(ignore_permissions=True)
                created_groups.append(group_data["customer_group_name"])
                print(f"[iderp] ✓ Gruppo cliente '{group_data['customer_group_name']}' creato")
            except Exception as e:
                print(f"[iderp] ✗ Errore creazione gruppo {group_data['customer_group_name']}: {e}")
        else:
            created_groups.append(group_data["customer_group_name"])
            print(f"[iderp] - Gruppo '{group_data['customer_group_name']}' già esistente")
    
    return created_groups

def create_test_customers():
    """Crea 10 clienti di prova assegnati casualmente ai gruppi"""
    
    # Verifica che i gruppi esistano
    existing_groups = []
    for group in ["Finale", "Bronze", "Gold", "Diamond"]:
        if frappe.db.exists("Customer Group", group):
            existing_groups.append(group)
    
    if not existing_groups:
        print("[iderp] ✗ Nessun gruppo cliente disponibile per creare clienti")
        return []
    
    # Trova territorio di default
    default_territory = frappe.db.get_value("Territory", {"is_group": 0}, "name")
    if not default_territory:
        default_territory = "All Territories"
        # Crea territorio se non esiste
        if not frappe.db.exists("Territory", default_territory):
            try:
                territory_doc = frappe.get_doc({
                    "doctype": "Territory",
                    "territory_name": default_territory,
                    "is_group": 1
                })
                territory_doc.insert(ignore_permissions=True)
                print(f"[iderp] ✓ Territorio '{default_territory}' creato")
            except Exception as e:
                print(f"[iderp] ✗ Errore creazione territorio: {e}")
                default_territory = "Rest Of The World"  # Fallback ERPNext
    
    # Nomi di clienti di esempio per stampa digitale
    customer_names = [
        "Studio Grafico Pixel", "Tipografia Moderna SRL", "Print & Design Co.",
        "Agenzia Creativa Blue", "Marketing Solutions", "Ufficio Comunicazione",
        "Visual Impact Studio", "Brand Identity Lab", "Digital Art Works",
        "Creative Print House"
    ]
    
    created_customers = []
    
    for i, name in enumerate(customer_names):
        customer_code = f"CUST-{i+1:03d}"
        
        if not frappe.db.exists("Customer", customer_code):
            try:
                # Assegna gruppo casualmente tra quelli esistenti
                assigned_group = random.choice(existing_groups)
                
                customer_doc = frappe.get_doc({
                    "doctype": "Customer",
                    "customer_name": name,
                    "customer_code": customer_code,
                    "customer_group": assigned_group,
                    "territory": default_territory,
                    "customer_type": "Company"
                })
                customer_doc.insert(ignore_permissions=True)
                
                created_customers.append({
                    "code": customer_code,
                    "name": name,
                    "group": assigned_group
                })
                
                print(f"[iderp] ✓ Cliente '{name}' ({customer_code}) creato - Gruppo: {assigned_group}")
                
            except Exception as e:
                print(f"[iderp] ✗ Errore creazione cliente {name}: {e}")
        else:
            # Cliente già esistente, ottieni info
            existing_customer = frappe.get_doc("Customer", customer_code)
            created_customers.append({
                "code": customer_code,
                "name": name,
                "group": existing_customer.customer_group
            })
            print(f"[iderp] - Cliente {customer_code} già esistente")
    
    return created_customers

def create_sample_customer_group_rules():
    """Crea regole di esempio per i 4 gruppi con minimi diversi"""
    
    # Verifica che i gruppi esistano
    existing_groups = []
    for group in ["Finale", "Bronze", "Gold", "Diamond"]:
        if frappe.db.exists("Customer Group", group):
            existing_groups.append(group)
    
    if not existing_groups:
        print("[iderp] ✗ Nessun gruppo cliente disponibile per creare regole")
        return []
    
    # Trova un item di esempio per le regole
    sample_item = frappe.db.get_value("Item", 
        {"supports_custom_measurement": 1, "tipo_vendita_default": "Metro Quadrato"}, 
        "item_code"
    )
    
    if not sample_item:
        print("[iderp] ✗ Nessun item configurato per metri quadri")
        print("[iderp] Configura prima un item con 'Supporta Misure Personalizzate' = Sì")
        return []
    
    # Regole specifiche per tipografia/stampa digitale
    rules_config = [
        {
            "group": "Finale",
            "min_sqm": 0.5,  # Minimo 0.5 m² per clienti finali
            "description": "Clienti finali - Minimo 0.5 m²"
        },
        {
            "group": "Bronze", 
            "min_sqm": 0.25, # Minimo 0.25 m² per bronze
            "description": "Clienti Bronze - Minimo 0.25 m²"
        },
        {
            "group": "Gold",
            "min_sqm": 0.1,  # Minimo 0.1 m² per gold  
            "description": "Clienti Gold - Minimo 0.1 m²"
        },
        {
            "group": "Diamond",
            "min_sqm": 0,    # Nessun minimo per diamond
            "description": "Clienti Diamond - Nessun minimo"
        }
    ]
    
    created_rules = []
    
    for rule_config in rules_config:
        # Salta se il gruppo non esiste
        if rule_config["group"] not in existing_groups:
            print(f"[iderp] - Saltando regola per gruppo inesistente: {rule_config['group']}")
            continue
            
        if not frappe.db.exists("Customer Group Price Rule", 
                              {"customer_group": rule_config["group"], "item_code": sample_item}):
            try:
                rule_doc = frappe.get_doc({
                    "doctype": "Customer Group Price Rule",
                    "customer_group": rule_config["group"],
                    "item_code": sample_item,
                    "enabled": 1,
                    "priority": 10,
                    "min_sqm": rule_config["min_sqm"],
                    "notes": rule_config["description"]
                })
                rule_doc.insert(ignore_permissions=True)
                
                created_rules.append({
                    "group": rule_config["group"],
                    "item": sample_item,
                    "min_sqm": rule_config["min_sqm"]
                })
                
                print(f"[iderp] ✓ Regola creata: {rule_config['group']} min {rule_config['min_sqm']} m²")
                
            except Exception as e:
                print(f"[iderp] ✗ Errore creazione regola {rule_config['group']}: {e}")
        else:
            created_rules.append({
                "group": rule_config["group"], 
                "item": sample_item,
                "min_sqm": rule_config["min_sqm"]
            })
            print(f"[iderp] - Regola per {rule_config['group']} già esistente")
    
    return created_rules

def get_customer_specific_min_sqm(customer, item_code):
    """
    Ottieni minimo m² per un cliente specifico
    """
    rule = get_customer_group_pricing(customer, item_code)
    return rule.get("min_sqm", 0) if rule else 0

# Integrazione con calcolo prezzi esistente
def get_customer_specific_price_for_sqm(customer, item_code, total_sqm):
    """
    Ottieni prezzo per m² considerando il gruppo cliente e i minimi
    """
    if not customer:
        # Se non c'è cliente, usa prezzi standard
        from iderp_module.pricing_utils import get_price_for_sqm
        return get_price_for_sqm(item_code, total_sqm)
    
    # Ottieni regole gruppo cliente
    rule = get_customer_group_pricing(customer, item_code)
    
    # Calcola m² effettivi considerando il minimo
    effective_sqm = total_sqm
    min_applied = False
    
    if rule and rule.get("min_sqm") and total_sqm < rule["min_sqm"]:
        effective_sqm = rule["min_sqm"]
        min_applied = True
    
    # Usa prezzi standard dell'item con m² effettivi
    from iderp_module.pricing_utils import get_price_for_sqm
    standard_price = get_price_for_sqm(item_code, effective_sqm)
    
    if standard_price and min_applied:
        standard_price["min_applied"] = True
        standard_price["original_sqm"] = total_sqm
        standard_price["effective_sqm"] = effective_sqm
        standard_price["customer_group"] = rule.get("customer_group")
        standard_price["min_sqm"] = rule.get("min_sqm")
    
    return standard_price

def setup_complete_customer_groups():
    """Setup completo: gruppi, clienti, regole"""
    print("[iderp] === Setup Completo Gruppi Cliente ===")
    
    # 1. Crea DocType
    if create_customer_group_price_rule_doctype():
        # 2. Crea gruppi
        groups = create_customer_groups()
        
        # 3. Crea clienti  
        customers = create_test_customers()
        
        # 4. Installa campi
        install_customer_group_fields()
        
        # 5. Crea regole esempio
        rules = create_sample_customer_group_rules()
        
        print("\n[iderp] === RIEPILOGO SETUP ===")
        print(f"[iderp] 📋 Gruppi creati: {len(groups)}")
        print(f"[iderp] 👥 Clienti creati: {len(customers)}")
        print(f"[iderp] ⚙️ Regole create: {len(rules)}")
        
        if customers:
            print("\n[iderp] === CLIENTI DI TEST ===")
            for customer in customers:
                print(f"[iderp] {customer['code']}: {customer['name']} ({customer['group']})")
        
        if rules:
            print("\n[iderp] === REGOLE MINIMI ===")
            for rule in rules:
                print(f"[iderp] {rule['group']}: min {rule['min_sqm']} m² su {rule['item']}")
        
        print("\n[iderp] ✅ Setup gruppi cliente completato!")
        print("[iderp] 🧪 Prova ora a creare un preventivo con uno dei clienti")
        
        return True
    else:
        print("[iderp] ✗ Setup fallito")
        return False
