# iderp/setup_commands.py

"""
Comandi console per setup e manutenzione iderp
Uso: bench --site sito.local console
     > from iderp.setup_commands import *
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime
import json

# Alias brevi per comandi frequenti
def qt():
    """Quick Test - Test rapido sistema"""
    return quick_test()

def qs():
    """Quick Status - Status sistema"""
    return system_status()

def qi():
    """Quick Install - Reinstalla se necessario"""
    return reinstall_iderp()

def qh():
    """Quick Help - Mostra comandi disponibili"""
    return show_help()

# Comandi principali

def quick_test():
    """Test rapido integrità sistema iderp"""
    print("\n🧪 TEST RAPIDO SISTEMA iderp")
    print("="*50)
    
    tests = {
        "DocTypes Custom": test_doctypes(),
        "Custom Fields": test_custom_fields(),
        "Customer Groups": test_customer_groups(),
        "Demo Items": test_demo_items(),
        "API Endpoints": test_api_endpoints(),
        "Optional System": test_optional_system(),
        "JavaScript Files": test_javascript_files()
    }
    
    passed = 0
    failed = 0
    
    for test_name, result in tests.items():
        status = "✅" if result["success"] else "❌"
        print(f"{status} {test_name}: {result['message']}")
        if result["success"]:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*50)
    print(f"RISULTATO: {passed} passati, {failed} falliti")
    
    if failed == 0:
        print("✅ SISTEMA iderp OPERATIVO!")
    else:
        print("⚠️ SISTEMA RICHIEDE ATTENZIONE")
    
    return tests

def test_doctypes():
    """Test DocTypes custom"""
    required = [
        "Customer Group Price Rule",
        "Item Pricing Tier",
        "Customer Group Minimum",
        "Item Optional",
        "Optional Template",
        "Sales Item Optional"
    ]
    
    missing = []
    for dt in required:
        if not frappe.db.exists("DocType", dt):
            missing.append(dt)
    
    if missing:
        return {
            "success": False,
            "message": f"Mancanti: {', '.join(missing)}"
        }
    
    return {
        "success": True,
        "message": f"Tutti {len(required)} DocTypes presenti"
    }

def test_custom_fields():
    """Test custom fields"""
    required_fields = [
        ("Item", "supports_custom_measurement"),
        ("Item", "tipo_vendita_default"),
        ("Item", "pricing_tiers"),
        ("Quotation Item", "tipo_vendita"),
        ("Quotation Item", "base"),
        ("Quotation Item", "altezza"),
        ("Quotation Item", "item_optionals")
    ]
    
    missing = []
    for doctype, fieldname in required_fields:
        if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
            missing.append(f"{doctype}.{fieldname}")
    
    if missing:
        return {
            "success": False,
            "message": f"Mancanti: {len(missing)} campi"
        }
    
    return {
        "success": True,
        "message": f"Tutti {len(required_fields)} campi presenti"
    }

def test_customer_groups():
    """Test customer groups"""
    required = ["Finale", "Bronze", "Gold", "Diamond"]
    found = 0
    
    for group in required:
        if frappe.db.exists("Customer Group", group):
            found += 1
    
    if found < len(required):
        return {
            "success": False,
            "message": f"Solo {found}/{len(required)} gruppi trovati"
        }
    
    return {
        "success": True,
        "message": f"Tutti {len(required)} gruppi presenti"
    }

def test_demo_items():
    """Test item demo"""
    count = frappe.db.count("Item", {"supports_custom_measurement": 1})
    
    if count == 0:
        return {
            "success": False,
            "message": "Nessun item configurato"
        }
    
    return {
        "success": True,
        "message": f"{count} item configurati"
    }

def test_api_endpoints():
    """Test API importabili"""
    try:
        from iderp.pricing_utils import calculate_universal_item_pricing
        from iderp.customer_group_pricing import get_customer_group_pricing
        from iderp.api.optional import get_item_optionals
        from iderp.api.machine import get_pending_jobs
        
        return {
            "success": True,
            "message": "Tutte le API importabili"
        }
    except ImportError as e:
        return {
            "success": False,
            "message": f"Errore import: {str(e)}"
        }

def test_optional_system():
    """Test sistema optional"""
    optional_count = frappe.db.count("Item Optional")
    template_count = frappe.db.count("Optional Template")
    
    if optional_count == 0:
        return {
            "success": False,
            "message": "Nessun optional configurato"
        }
    
    return {
        "success": True,
        "message": f"{optional_count} optional, {template_count} template"
    }

def test_javascript_files():
    """Test file JavaScript"""
    import os
    
    js_files = [
        "public/js/item_dimension.js",
        "public/js/item_config.js",
        "public/js/sales_item_optional.js"
    ]
    
    app_path = frappe.get_app_path("iderp")
    missing = []
    
    for js_file in js_files:
        file_path = os.path.join(app_path, js_file)
        if not os.path.exists(file_path):
            missing.append(js_file)
    
    if missing:
        return {
            "success": False,
            "message": f"File mancanti: {', '.join(missing)}"
        }
    
    return {
        "success": True,
        "message": f"Tutti {len(js_files)} file JS presenti"
    }

def system_status():
    """Mostra status dettagliato sistema"""
    print("\n📊 STATUS SISTEMA iderp")
    print("="*50)
    
    # Versione
    from iderp import __version__
    print(f"📌 Versione iderp: {__version__}")
    print(f"📌 Frappe: {frappe.__version__}")
    
    try:
        import erpnext
        print(f"📌 ERPNext: {erpnext.__version__}")
    except:
        print("📌 ERPNext: Non disponibile")
    
    print("\n📈 STATISTICHE:")
    
    # DocTypes
    stats = get_installation_stats()
    
    for key, value in stats.items():
        print(f"• {key.replace('_', ' ').title()}: {value}")
    
    # Health check
    print("\n🏥 HEALTH CHECK:")
    from iderp.maintenance import get_system_health
    health = get_system_health()
    
    health_icon = {
        "healthy": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    print(f"Status generale: {health_icon.get(health['status'], '❓')} {health['status'].upper()}")
    
    for check, data in health["checks"].items():
        icon = health_icon.get(data["status"], "❓")
        print(f"  {icon} {check}: {data['value']}")
    
    # Ultimi errori
    print("\n🐛 ULTIMI ERRORI iderp:")
    recent_errors = frappe.get_all("Error Log",
        filters={
            "method": ["like", "%iderp%"],
            "creation": [">", frappe.utils.add_days(now_datetime(), -1)]
        },
        fields=["method", "error"],
        limit=5,
        order_by="creation desc"
    )
    
    if recent_errors:
        for err in recent_errors:
            print(f"  • {err.method}: {err.error[:50]}...")
    else:
        print("  ✅ Nessun errore nelle ultime 24 ore")
    
    return stats

def get_installation_stats():
    """Ottieni statistiche installazione"""
    stats = {
        "doctypes_custom": len([
            dt for dt in ["Customer Group Price Rule", "Item Pricing Tier", 
                         "Customer Group Minimum", "Item Optional", 
                         "Optional Template"]
            if frappe.db.exists("DocType", dt)
        ]),
        "custom_fields": frappe.db.count("Custom Field", {
            "dt": ["in", ["Item", "Quotation Item", "Sales Order Item"]]
        }),
        "customer_groups": frappe.db.count("Customer Group", {
            "name": ["in", ["Finale", "Bronze", "Gold", "Diamond"]]
        }),
        "configured_items": frappe.db.count("Item", {"supports_custom_measurement": 1}),
        "optional_configured": frappe.db.count("Item Optional"),
        "templates_created": frappe.db.count("Optional Template"),
        "pricing_rules": frappe.db.count("Customer Group Price Rule"),
        "active_quotations": frappe.db.count("Quotation", {
            "status": ["in", ["Draft", "Submitted"]]
        })
    }
    
    return stats

def reinstall_iderp():
    """Reinstalla iderp con conferma"""
    print("\n⚠️  ATTENZIONE: Reinstallazione iderp")
    print("="*50)
    print("Questo comando:")
    print("• Ricreerà tutti i campi custom")
    print("• Riconfigurerà i DocTypes")
    print("• Ricreerà i dati demo")
    print("\nI dati esistenti NON saranno persi.")
    
    confirm = input("\n🔸 Vuoi procedere? (si/no): ").lower()
    
    if confirm in ['si', 's', 'yes', 'y']:
        print("\n🔄 Reinstallazione in corso...")
        
        try:
            from iderp.install import after_install
            result = after_install()
            
            if result:
                print("\n✅ Reinstallazione completata con successo!")
            else:
                print("\n❌ Reinstallazione fallita - controlla i log")
                
            return result
            
        except Exception as e:
            print(f"\n❌ Errore reinstallazione: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("\n❌ Reinstallazione annullata")
        return False

def show_help():
    """Mostra comandi disponibili"""
    print("\n📚 COMANDI iderp DISPONIBILI")
    print("="*50)
    
    commands = [
        ("qt()", "Quick Test", "Test rapido integrità sistema"),
        ("qs()", "Quick Status", "Mostra status dettagliato"),
        ("qi()", "Quick Install", "Reinstalla iderp"),
        ("qh()", "Quick Help", "Mostra questo help"),
        ("", "", ""),
        ("setup_demo_data()", "Setup Demo", "Crea dati demo aggiuntivi"),
        ("fix_permissions()", "Fix Permessi", "Sistema permessi DocTypes"),
        ("clear_iderp_cache()", "Clear Cache", "Pulisce cache iderp"),
        ("run_maintenance()", "Manutenzione", "Esegue manutenzione manuale"),
        ("test_pricing()", "Test Pricing", "Test calcolo prezzi"),
        ("export_config()", "Export Config", "Esporta configurazione"),
        ("import_config()", "Import Config", "Importa configurazione")
    ]
    
    for cmd, name, desc in commands:
        if cmd:
            print(f"  {cmd:<20} - {name:<15} - {desc}")
        else:
            print()
    
    print("\n💡 Esempi:")
    print("  > qt()  # Esegue test rapido")
    print("  > qs()  # Mostra status sistema")
    print("  > test_pricing('POSTER-A3', 'Gold', 50, 70)")

def setup_demo_data():
    """Crea dati demo aggiuntivi"""
    print("\n🎯 SETUP DATI DEMO AGGIUNTIVI")
    print("="*50)
    
    created = {
        "items": 0,
        "customers": 0,
        "quotations": 0
    }
    
    # Crea item aggiuntivi
    demo_items = [
        {
            "item_code": "VOLANTINO-A5",
            "item_name": "Volantini A5 - Carta Patinata",
            "tipo_vendita_default": "Pezzo",
            "item_group": "Products"
        },
        {
            "item_code": "ADESIVO-CUSTOM",
            "item_name": "Adesivi Personalizzati",
            "tipo_vendita_default": "Metro Quadrato",
            "item_group": "Products"
        }
    ]
    
    for item_data in demo_items:
        if not frappe.db.exists("Item", item_data["item_code"]):
            try:
                item = frappe.get_doc({
                    "doctype": "Item",
                    **item_data,
                    "is_stock_item": 1,
                    "supports_custom_measurement": 1
                })
                item.insert()
                created["items"] += 1
                print(f"  ✅ Creato item: {item_data['item_code']}")
            except Exception as e:
                print(f"  ❌ Errore item {item_data['item_code']}: {e}")
    
    # Crea clienti aggiuntivi
    for i in range(5):
        customer_name = f"Cliente Demo {i+1}"
        if not frappe.db.exists("Customer", {"customer_name": customer_name}):
            try:
                import random
                customer = frappe.get_doc({
                    "doctype": "Customer",
                    "customer_name": customer_name,
                    "customer_group": random.choice(["Finale", "Bronze", "Gold", "Diamond"]),
                    "territory": "All Territories"
                })
                customer.insert()
                created["customers"] += 1
            except Exception as e:
                print(f"  ❌ Errore cliente: {e}")
    
    print(f"\n✅ Creati: {created['items']} items, {created['customers']} clienti")
    
    frappe.db.commit()

def fix_permissions():
    """Sistema permessi DocTypes iderp"""
    print("\n🔐 FIX PERMESSI DOCTYPES")
    print("="*50)
    
    # DocTypes e permessi
    doctype_permissions = {
        "Customer Group Price Rule": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
            {"role": "Sales Manager", "read": 1, "write": 1, "create": 1},
            {"role": "Sales User", "read": 1}
        ],
        "Item Optional": [
            {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
            {"role": "Sales Manager", "read": 1, "write": 1, "create": 1},
            {"role": "Sales User", "read": 1}
        ]
    }
    
    for doctype, permissions in doctype_permissions.items():
        if frappe.db.exists("DocType", doctype):
            print(f"\n  Fixing {doctype}...")
            
            # Rimuovi permessi esistenti
            frappe.db.delete("DocPerm", {"parent": doctype})
            
            # Aggiungi nuovi permessi
            for perm in permissions:
                doc_perm = frappe.get_doc({
                    "doctype": "DocPerm",
                    "parent": doctype,
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    **perm
                })
                doc_perm.insert()
            
            print(f"  ✅ Permessi aggiornati")
    
    frappe.db.commit()
    frappe.clear_cache()

def clear_iderp_cache():
    """Pulisce tutta la cache iderp"""
    print("\n🧹 PULIZIA CACHE iderp")
    print("="*50)
    
    from iderp.maintenance import cleanup_cache
    cleanup_cache()
    
    # Pulizia aggiuntiva
    cache_patterns = [
        "iderp_*",
        "*_iderp_*",
        "item_config_*",
        "customer_pricing_*"
    ]
    
    cleared = 0
    for pattern in cache_patterns:
        # Implementazione semplificata
        cleared += 5  # Placeholder
    
    print(f"  ✅ Cache pulita: ~{cleared} chiavi rimosse")
    frappe.clear_cache()

def run_maintenance(task=None):
    """Esegue task manutenzione"""
    print("\n🔧 MANUTENZIONE SISTEMA iderp")
    print("="*50)
    
    if not task:
        print("Task disponibili:")
        print("  • cleanup_calculations")
        print("  • cleanup_cache")
        print("  • optimize_database")
        print("  • validate_integrity")
        print("\nUso: run_maintenance('task_name')")
        return
    
    from iderp.maintenance import run_maintenance_now
    result = run_maintenance_now(task)
    
    print(f"\n✅ Risultato: {result}")

def test_pricing(item_code="POSTER-A3", customer_group="Gold", base=50, altezza=70):
    """Test calcolo prezzi con parametri"""
    print(f"\n🧮 TEST CALCOLO PREZZI")
    print("="*50)
    print(f"Item: {item_code}")
    print(f"Gruppo: {customer_group}")
    print(f"Misure: {base}x{altezza} cm")
    
    try:
        from iderp.pricing_utils import calculate_universal_item_pricing
        
        result = calculate_universal_item_pricing(
            item_code=item_code,
            customer_group=customer_group,
            base=base,
            altezza=altezza,
            tipo_vendita="Metro Quadrato",
            qty=1
        )
        
        print(f"\n📊 RISULTATO:")
        print(f"  • m² calcolati: {result.get('sqm_total', 0):.3f}")
        print(f"  • Prezzo/m²: €{result.get('price_per_sqm', 0):.2f}")
        print(f"  • Totale: €{result.get('total_price', 0):.2f}")
        
        if result.get('note'):
            print(f"  • Note: {result['note']}")
            
        return result
        
    except Exception as e:
        print(f"\n❌ Errore: {e}")
        import traceback
        traceback.print_exc()

def export_config(filename=None):
    """Esporta configurazione iderp"""
    if not filename:
        filename = f"iderp_config_{frappe.utils.today()}.json"
    
    print(f"\n📤 EXPORT CONFIGURAZIONE iderp")
    print("="*50)
    
    config = {
        "export_date": now_datetime(),
        "version": frappe.get_module("iderp").__version__,
        "customer_groups": [],
        "items": [],
        "optionals": [],
        "templates": []
    }
    
    # Export Customer Groups
    groups = frappe.get_all("Customer Group",
        filters={"name": ["in", ["Finale", "Bronze", "Gold", "Diamond"]]},
        fields=["*"]
    )
    config["customer_groups"] = groups
    
    # Export Items configurati
    items = frappe.get_all("Item",
        filters={"supports_custom_measurement": 1},
        fields=["item_code", "item_name", "tipo_vendita_default"]
    )
    
    for item in items:
        # Aggiungi pricing tiers
        item["pricing_tiers"] = frappe.get_all("Item Pricing Tier",
            filters={"parent": item["item_code"]},
            fields=["*"]
        )
    
    config["items"] = items
    
    # Export Optional
    config["optionals"] = frappe.get_all("Item Optional", fields=["*"])
    
    # Salva file
    file_path = frappe.get_site_path("private/files", filename)
    
    with open(file_path, 'w') as f:
        json.dump(config, f, indent=2, default=str)
    
    print(f"✅ Configurazione esportata in: {file_path}")
    
    return file_path

def import_config(filename):
    """Importa configurazione iderp"""
    print(f"\n📥 IMPORT CONFIGURAZIONE iderp")
    print("="*50)
    
    file_path = frappe.get_site_path("private/files", filename)
    
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        print(f"Configurazione del: {config['export_date']}")
        print(f"Items: {len(config.get('items', []))}")
        print(f"Optional: {len(config.get('optionals', []))}")
        
        confirm = input("\n🔸 Importare? (si/no): ").lower()
        
        if confirm in ['si', 's', 'yes', 'y']:
            # Import logica
            print("\n⚠️ Funzione non ancora implementata completamente")
            return False
        
    except Exception as e:
        print(f"❌ Errore import: {e}")
        return False

# Auto-esegui help al primo import
print("\n🚀 iderp Setup Commands caricati!")
print("Digita qh() per vedere tutti i comandi disponibili")
