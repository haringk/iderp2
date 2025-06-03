# iderp/field_diagnostics.py
"""
Diagnostica custom fields uno alla volta
"""

import frappe

def test_field_by_field():
    """Riabilita campi uno alla volta per trovare il problematico"""
    
    fields_to_test = [
        "measurement_config_section",
        "supports_custom_measurement",
        "tipo_vendita_default", 
        "pricing_section",
        "pricing_tiers",
        "customer_group_minimums_section",
        "customer_group_minimums"
    ]
    
    print("🧪 Test campi uno alla volta...")
    print("Dopo ogni campo, vai su Item e prova a salvare!")
    
    for i, fieldname in enumerate(fields_to_test, 1):
        try:
            cf_name = frappe.db.get_value("Custom Field", 
                {"dt": "Item", "fieldname": fieldname}, "name")
            
            if cf_name:
                # Riabilita questo campo
                frappe.db.set_value("Custom Field", cf_name, "hidden", 0)
                frappe.db.commit()
                
                print(f"\n{i}. ✓ Campo '{fieldname}' riabilitato")
                print(f"   👉 ORA VAI SU ITEM E PROVA A SALVARE")
                print(f"   💾 Se salva OK, continua")
                print(f"   🚨 Se non salva, questo campo è il problema!")
                
                input("   ⏸️  Premi INVIO quando hai testato...")
                
        except Exception as e:
            print(f"   ✗ Errore campo {fieldname}: {e}")

def hide_single_field(fieldname):
    """Nascondi un singolo campo problematico"""
    try:
        cf_name = frappe.db.get_value("Custom Field", 
            {"dt": "Item", "fieldname": fieldname}, "name")
        
        if cf_name:
            frappe.db.set_value("Custom Field", cf_name, "hidden", 1)
            frappe.db.commit()
            print(f"✓ Campo '{fieldname}' nascosto")
    except Exception as e:
        print(f"✗ Errore: {e}")

def restore_all_safe_fields():
    """Ripristina tutti tranne quelli problematici"""
    safe_fields = [
        "measurement_config_section",
        "supports_custom_measurement",
        "tipo_vendita_default"
    ]
    
    for fieldname in safe_fields:
        try:
            cf_name = frappe.db.get_value("Custom Field", 
                {"dt": "Item", "fieldname": fieldname}, "name")
            
            if cf_name:
                frappe.db.set_value("Custom Field", cf_name, "hidden", 0)
                print(f"✓ Campo sicuro '{fieldname}' ripristinato")
        except Exception as e:
            print(f"✗ Errore: {e}")
    
    frappe.db.commit()
    print("✅ Campi sicuri ripristinati")