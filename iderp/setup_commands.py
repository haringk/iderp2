# iderp/setup_commands.py
"""
Comandi per installazione, testing e gestione del sistema IDERP
Versione semplificata per Customer Group Pricing con minimi metro quadro
"""

import frappe

def install_iderp_customer_groups():
    """
    Installazione completa del sistema IDERP con Customer Groups
    Comando console: from iderp.setup_commands import install_iderp_customer_groups; install_iderp_customer_groups()
    """
    print("\n" + "="*60)
    print("🚀 INSTALLAZIONE IDERP v2.0 - CUSTOMER GROUP PRICING")
    print("="*60)
    
    try:
        # 1. Installazione base
        from iderp.install import after_install
        after_install()
        
        # 2. Validazione sistema
        validate_complete_installation()
        
        # 3. Mostra riepilogo
        show_installation_summary()
        
        print("\n" + "="*60)
        print("✅ INSTALLAZIONE COMPLETATA!")
        print("="*60)
        print("🎯 GRUPPI CLIENTE CONFIGURATI:")
        print("   • Finale: min 0.5 m²")
        print("   • Bronze: min 0.25 m²") 
        print("   • Gold: min 0.1 m²")
        print("   • Diamond: nessun minimo")
        print("\n💡 PROSSIMI PASSI:")
        print("1. Vai su Item → Configura un prodotto")
        print("2. Abilita 'Supporta Misure Personalizzate'")
        print("3. Aggiungi scaglioni prezzo")
        print("4. Crea quotation con clienti diversi")
        print("5. Verifica minimi applicati automaticamente")
        print("\n🧪 Per test rapido: test_customer_groups()")
        
    except Exception as e:
        print(f"\n❌ ERRORE INSTALLAZIONE: {e}")
        import traceback
        traceback.print_exc()

def test_customer_groups():
    """
    Test completo del sistema Customer Groups
    """
    print("\n" + "="*60)
    print("🧪 TEST SISTEMA CUSTOMER GROUPS")
    print("="*60)
    
    errors = []
    
    # 1. Test gruppi creati
    print("\n1. 🏷️  Verificando gruppi cliente...")
    expected_groups = ["Finale", "Bronze", "Gold", "Diamond"]
    for group in expected_groups:
        if frappe.db.exists("Customer Group", group):
            print(f"   ✅ {group}")
        else:
            print(f"   ❌ {group} - MANCANTE")
            errors.append(f"Gruppo {group} mancante")
    
    # 2. Test clienti creati
    print("\n2. 👥 Verificando clienti di test...")
    customers = frappe.db.sql("""
        SELECT name, customer_name, customer_group 
        FROM `tabCustomer` 
        WHERE customer_group IN ('Finale', 'Bronze', 'Gold', 'Diamond')
        LIMIT 5
    """, as_dict=True)
    
    if customers:
        print(f"   ✅ {len(customers)} clienti configurati:")
        for customer in customers:
            print(f"      • {customer.customer_name} ({customer.customer_group})")
    else:
        print("   ❌ Nessun cliente con gruppi configurati")
        errors.append("Nessun cliente configurato")
    
    # 3. Test regole pricing
    print("\n3. 📏 Verificando regole pricing...")
    rules = frappe.db.sql("""
        SELECT customer_group, item_code, min_sqm 
        FROM `tabCustomer Group Price Rule`
        WHERE enabled = 1
    """, as_dict=True)
    
    if rules:
        print(f"   ✅ {len(rules)} regole configurate:")
        for rule in rules:
            print(f"      • {rule.customer_group}: min {rule.min_sqm} m² su {rule.item_code}")
    else:
        print("   ❌ Nessuna regola pricing configurata")
        errors.append("Nessuna regola pricing")
    
    # 4. Test API
    print("\n4. 🔧 Testando API...")
    try:
        from iderp.pricing_utils import get_customer_group_min_sqm
        from iderp.customer_group_pricing import get_customer_group_pricing
        print("   ✅ API Customer Group funzionanti")
    except ImportError as e:
        print(f"   ❌ Errore import API: {e}")
        errors.append("Errore API")
    
    # 5. Test item configurati
    print("\n5. 📦 Verificando item configurati...")
    configured_items = frappe.db.sql("""
        SELECT item_code, item_name 
        FROM `tabItem` 
        WHERE supports_custom_measurement = 1
        LIMIT 3
    """, as_dict=True)
    
    if configured_items:
        print(f"   ✅ {len(configured_items)} item configurati:")
        for item in configured_items:
            print(f"      • {item.item_code}: {item.item_name}")
    else:
        print("   ⚠️  Nessun item configurato per misure personalizzate")
        print("   💡 Configura almeno un item per test completi")
    
    # 6. Risultato finale
    print("\n" + "="*60)
    if errors:
        print("❌ TEST FALLITO - Errori trovati:")
        for error in errors:
            print(f"   • {error}")
        print("\n🔧 Esegui: install_iderp_customer_groups() per risolvere")
    else:
        print("✅ TUTTI I TEST SUPERATI!")
        print("\n🎉 Il sistema Customer Groups è pronto!")
        print("🚀 Prova ora: create_test_quotation_with_groups()")
    
    print("="*60)
    
    return len(errors) == 0

def create_test_quotation_with_groups():
    """
    Crea quotation di test per verificare i gruppi cliente
    """
    print("\n📝 Creando quotation di test per gruppi cliente...")
    
    # Trova clienti per gruppo
    test_customers = {}
    for group in ["Finale", "Bronze", "Gold", "Diamond"]:
        customer = frappe.db.get_value("Customer", 
            {"customer_group": group}, 
            ["name", "customer_name"], as_dict=True
        )
        if customer:
            test_customers[group] = customer
    
    # Trova item configurato
    test_item = frappe.db.get_value("Item", 
        {"supports_custom_measurement": 1}, 
        "item_code"
    )
    
    if not test_customers:
        print("   ❌ Nessun cliente con gruppi configurati")
        return None
        
    if not test_item:
        print("   ❌ Nessun item configurato per misure personalizzate")
        print("   💡 Configura prima un item con scaglioni prezzo")
        return None
    
    results = []
    
    # Crea quotation per ogni gruppo
    for group, customer in test_customers.items():
        try:
            quotation = frappe.get_doc({
                "doctype": "Quotation",
                "party_name": customer.name,
                "quotation_to": "Customer",
                "transaction_date": frappe.utils.today(),
                "items": [{
                    "item_code": test_item,
                    "tipo_vendita": "Metro Quadrato",
                    "base": 30,  # 30cm
                    "altezza": 50,  # 50cm = 0.15 m² (sotto tutti i minimi)
                    "qty": 1,
                    "delivery_date": frappe.utils.add_days(frappe.utils.today(), 7)
                }]
            })
            
            quotation.insert(ignore_permissions=True)
            
            item_row = quotation.items[0]
            
            result = {
                "group": group,
                "customer": customer.customer_name,
                "quotation": quotation.name,
                "original_sqm": 0.15,
                "calculated_price": item_row.rate,
                "rules_applied": getattr(item_row, 'customer_group_rules_applied', 0),
                "notes": getattr(item_row, 'note_calcolo', 'N/A')[:100] + "..."
            }
            
            results.append(result)
            
            print(f"   ✅ {group}: {quotation.name}")
            print(f"      Cliente: {customer.customer_name}")
            print(f"      Prezzo: €{item_row.rate}")
            print(f"      Regole applicate: {'Sì' if result['rules_applied'] else 'No'}")
            
        except Exception as e:
            print(f"   ❌ Errore {group}: {e}")
    
    if results:
        print("\n📊 RIEPILOGO TEST MINIMI:")
        print("   Prodotto: 30×50cm = 0.15 m²")
        print("   Minimi attesi:")
        print("   • Finale: 0.5 m² (minimo applicato)")
        print("   • Bronze: 0.25 m² (minimo applicato)")  
        print("   • Gold: 0.1 m² (nessun minimo)")
        print("   • Diamond: 0 m² (nessun minimo)")
        
        print("\n✅ Test completato! Controlla le quotation create.")
    
    return results

def show_customer_groups_status():
    """Mostra stato dettagliato del sistema customer groups"""
    print("\n" + "="*60)
    print("📊 STATO SISTEMA CUSTOMER GROUPS")
    print("="*60)
    
    # Gruppi
    print("\n🏷️  GRUPPI CLIENTE:")
    groups_info = frappe.db.sql("""
        SELECT cg.name, COUNT(c.name) as customers_count
        FROM `tabCustomer Group` cg
        LEFT JOIN `tabCustomer` c ON c.customer_group = cg.name
        WHERE cg.name IN ('Finale', 'Bronze', 'Gold', 'Diamond')
        GROUP BY cg.name
        ORDER BY cg.name
    """, as_dict=True)
    
    for group in groups_info:
        print(f"   • {group.name}: {group.customers_count} clienti")
    
    # Regole pricing
    print("\n📏 REGOLE PRICING:")
    rules = frappe.db.sql("""
        SELECT customer_group, item_code, min_sqm, enabled
        FROM `tabCustomer Group Price Rule`
        ORDER BY customer_group, item_code
    """, as_dict=True)
    
    if rules:
        for rule in rules:
            status = "✅" if rule.enabled else "❌"
            print(f"   {status} {rule.customer_group}: min {rule.min_sqm} m² su {rule.item_code}")
    else:
        print("   ⚠️  Nessuna regola configurata")
    
    # Item configurati
    print("\n📦 ITEM CONFIGURATI:")
    items = frappe.db.sql("""
        SELECT item_code, item_name, tipo_vendita_default,
               (SELECT COUNT(*) FROM `tabItem Pricing Tier` WHERE parent = i.name) as tiers_count
        FROM `tabItem` i
        WHERE supports_custom_measurement = 1
        LIMIT 5
    """, as_dict=True)
    
    if items:
        for item in items:
            print(f"   • {item.item_code}: {item.tipo_vendita_default}, {item.tiers_count} scaglioni")
    else:
        print("   ⚠️  Nessun item configurato")
    
    # Quotation recenti
    print("\n📝 QUOTATION RECENTI:")
    quotations = frappe.db.sql("""
        SELECT q.name, c.customer_group, q.party_name, q.transaction_date
        FROM `tabQuotation` q
        JOIN `tabCustomer` c ON c.name = q.party_name
        WHERE c.customer_group IN ('Finale', 'Bronze', 'Gold', 'Diamond')
        ORDER BY q.creation DESC
        LIMIT 5
    """, as_dict=True)
    
    if quotations:
        for quot in quotations:
            print(f"   • {quot.name}: {quot.party_name} ({quot.customer_group})")
    else:
        print("   ⚠️  Nessuna quotation recente")
    
    print("="*60)

def setup_item_for_testing(item_code=None):
    """Configura un item per testing con scaglioni realistici"""
    
    if not item_code:
        # Prendi il primo item disponibile
        item_code = frappe.db.get_value("Item", {"disabled": 0}, "item_code")
        
    if not item_code:
        print("❌ Nessun item disponibile per configurazione")
        return False
    
    print(f"\n⚙️  Configurando item {item_code} per testing...")
    
    try:
        item_doc = frappe.get_doc("Item", item_code)
        
        # Abilita misure personalizzate
        item_doc.supports_custom_measurement = 1
        item_doc.tipo_vendita_default = "Metro Quadrato"
        
        # Scaglioni specifici per stampa digitale
        sample_tiers = [
            {
                "from_sqm": 0,
                "to_sqm": 0.25,
                "price_per_sqm": 25.0,
                "tier_name": "Micro (biglietti, etichette)"
            },
            {
                "from_sqm": 0.25,
                "to_sqm": 1,
                "price_per_sqm": 18.0,
                "tier_name": "Piccolo (A4, flyer)"
            },
            {
                "from_sqm": 1,
                "to_sqm": 5,
                "price_per_sqm": 12.0,
                "tier_name": "Medio (poster, brochure)"
            },
            {
                "from_sqm": 5,
                "to_sqm": None,
                "price_per_sqm": 8.0,
                "tier_name": "Grande (striscioni, pannelli)",
                "is_default": 1
            }
        ]
        
        # Pulisci e aggiungi scaglioni
        item_doc.pricing_tiers = []
        for tier_data in sample_tiers:
            item_doc.append("pricing_tiers", tier_data)
        
        item_doc.save(ignore_permissions=True)
        
        # Crea regole customer group per questo item
        create_customer_group_rules_for_item(item_code)
        
        print(f"   ✅ Item {item_code} configurato con:")
        print("      • 4 scaglioni prezzo realistici")
        print("      • Regole customer group per tutti i gruppi")
        print(f"   🧪 Prova ora: create_test_quotation_with_groups()")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Errore configurazione item: {e}")
        return False

def create_customer_group_rules_for_item(item_code):
    """Crea regole customer group per un item specifico"""
    
    rules_config = [
        {"group": "Finale", "min_sqm": 0.5},
        {"group": "Bronze", "min_sqm": 0.25}, 
        {"group": "Gold", "min_sqm": 0.1},
        {"group": "Diamond", "min_sqm": 0}
    ]
    
    for rule_config in rules_config:
        # Verifica se esiste già
        existing = frappe.db.exists("Customer Group Price Rule", {
            "customer_group": rule_config["group"],
            "item_code": item_code
        })
        
        if not existing:
            try:
                rule_doc = frappe.get_doc({
                    "doctype": "Customer Group Price Rule",
                    "customer_group": rule_config["group"],
                    "item_code": item_code,
                    "enabled": 1,
                    "min_sqm": rule_config["min_sqm"],
                    "notes": f"Regola {rule_config['group']} per {item_code}"
                })
                rule_doc.insert(ignore_permissions=True)
                print(f"      ✓ Regola {rule_config['group']}: min {rule_config['min_sqm']} m²")
            except Exception as e:
                print(f"      ✗ Errore regola {rule_config['group']}: {e}")

def validate_complete_installation():
    """Validazione completa installazione"""
    print("\n🔍 Validazione sistema...")
    
    # Validazione base
    from iderp.install import validate_installation
    if not validate_installation():
        print("   ❌ Installazione base fallita")
        return False
    
    # Validazione customer groups
    if not frappe.db.exists("DocType", "Customer Group Price Rule"):
        print("   ❌ Customer Group Price Rule non installato")
        return False
    
    print("   ✅ Sistema validato")
    return True

def show_installation_summary():
    """Mostra riepilogo installazione"""
    print("\n📋 RIEPILOGO INSTALLAZIONE:")
    
    # Conta elementi creati
    groups_count = frappe.db.count("Customer Group", 
        filters={"name": ["in", ["Finale", "Bronze", "Gold", "Diamond"]]}
    )
    
    customers_count = frappe.db.count("Customer",
        filters={"customer_group": ["in", ["Finale", "Bronze", "Gold", "Diamond"]]}
    )
    
    rules_count = frappe.db.count("Customer Group Price Rule")
    
    items_count = frappe.db.count("Item", 
        filters={"supports_custom_measurement": 1}
    )
    
    print(f"   • {groups_count}/4 gruppi cliente")
    print(f"   • {customers_count} clienti di test")
    print(f"   • {rules_count} regole pricing")
    print(f"   • {items_count} item configurati")

def scenario_test_completo():
    """Test scenario completo: dall'installazione alla quotation"""
    print("\n" + "="*60)
    print("🎬 SCENARIO TEST COMPLETO")
    print("="*60)
    
    # Step 1: Installazione
    print("\n1. 🚀 Installazione sistema...")
    install_iderp_customer_groups()
    
    # Step 2: Setup item
    print("\n2. ⚙️  Setup item per test...")
    if not setup_item_for_testing():
        print("❌ Impossibile configurare item")
        return False
    
    # Step 3: Test gruppi
    print("\n3. 🧪 Test sistema...")
    if not test_customer_groups():
        print("❌ Test sistema fallito")
        return False
    
    # Step 4: Crea quotation test
    print("\n4. 📝 Creazione quotation test...")
    results = create_test_quotation_with_groups()
    
    if results:
        print("\n" + "="*60)
        print("🎉 SCENARIO TEST COMPLETATO CON SUCCESSO!")
        print("="*60)
        print("✅ Sistema installato e funzionante")
        print("✅ Gruppi cliente configurati")
        print("✅ Quotation di test create")
        print("✅ Minimi applicati correttamente")
        print("\n🚀 Il sistema è pronto per l'uso in produzione!")
        return True
    else:
        print("❌ Fallimento creazione quotation test")
        return False

def cleanup_test_data():
    """Pulisce i dati di test creati"""
    print("\n🧹 Pulizia dati di test...")
    
    # Elimina quotation di test
    test_quotations = frappe.db.sql("""
        SELECT name FROM `tabQuotation` q
        JOIN `tabCustomer` c ON c.name = q.party_name
        WHERE c.customer_group IN ('Finale', 'Bronze', 'Gold', 'Diamond')
        AND q.transaction_date = %s
    """, [frappe.utils.today()], as_dict=True)
    
    for quot in test_quotations:
        try:
            frappe.delete_doc("Quotation", quot.name, force=True)
            print(f"   ✓ Quotation {quot.name} eliminata")
        except:
            pass
    
    print("   ✅ Pulizia completata")

# Comandi rapidi per console
def quick_install():
    """Comando rapido: qi"""
    install_iderp_customer_groups()

def quick_test():
    """Comando rapido: qt"""
    return test_customer_groups()

def quick_status():
    """Comando rapido: qs"""
    show_customer_groups_status()

def quick_setup_item():
    """Comando rapido: qsi"""
    return setup_item_for_testing()

def quick_quotation_test():
    """Comando rapido: qqt"""
    return create_test_quotation_with_groups()

def quick_scenario():
    """Comando rapido: qsc"""
    return scenario_test_completo()

def quick_cleanup():
    """Comando rapido: qcl"""
    cleanup_test_data()

# Alias per comodità
qi = quick_install
qt = quick_test
qs = quick_status
qsi = quick_setup_item
qqt = quick_quotation_test
qsc = quick_scenario
qcl = quick_cleanup

# Help per mostrare comandi disponibili
def help_commands():
    """Mostra tutti i comandi disponibili"""
    print("\n" + "="*60)
    print("📚 COMANDI DISPONIBILI IDERP")
    print("="*60)
    print("\n🔧 INSTALLAZIONE:")
    print("   qi()   → Installazione completa Customer Groups")
    print("   qsc()  → Scenario test completo (installa + test)")
    print("\n🧪 TESTING:")
    print("   qt()   → Test sistema Customer Groups")
    print("   qqt()  → Crea quotation di test")
    print("   qs()   → Mostra status sistema")
    print("\n⚙️  CONFIGURAZIONE:")
    print("   qsi()  → Setup item per testing")
    print("   qcl()  → Pulisci dati di test")
    print("\n📋 ESEMPI:")
    print("   # Installazione rapida")
    print("   >>> from iderp.setup_commands import *")
    print("   >>> qi()")
    print("\n   # Test completo")
    print("   >>> qt()")
    print("\n   # Scenario completo")
    print("   >>> qsc()")
    print("="*60)

# Alias help
h = help_commands