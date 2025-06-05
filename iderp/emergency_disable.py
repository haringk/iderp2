# iderp/emergency_disable.py
"""
Script di emergenza per disabilitare custom fields problematici
"""

import frappe

def disable_iderp_custom_fields():
    """Disabilita temporaneamente tutti i custom fields IDERP"""
    
    # Custom fields che potrebbero causare problemi
    problematic_fields = [
        "measurement_config_section",
        "supports_custom_measurement", 
        "tipo_vendita_default",
        "pricing_section",
        "pricing_tiers",
        "customer_group_minimums_section",
        "customer_group_minimums"
    ]
    
    for fieldname in problematic_fields:
        try:
            # Cerca il custom field
            cf_name = frappe.db.get_value("Custom Field", 
                {"dt": "Item", "fieldname": fieldname}, "name")
            
            if cf_name:
                # Nascondi il field invece di eliminarlo
                frappe.db.set_value("Custom Field", cf_name, "hidden", 1)
                print(f"✓ Campo {fieldname} nascosto")
        except Exception as e:
            print(f"✗ Errore campo {fieldname}: {e}")
    
    frappe.db.commit()
    print("✅ Custom fields problematici nascosti")

def restore_iderp_custom_fields():
    """Ripristina i custom fields nascosti"""
    
    try:
        frappe.db.sql("""
            UPDATE `tabCustom Field` 
            SET hidden = 0 
            WHERE dt = 'Item' 
            AND fieldname LIKE '%measurement%' 
               OR fieldname LIKE '%pricing%' 
               OR fieldname LIKE '%customer_group%'
        """)
        
        frappe.db.commit()
        print("✅ Custom fields ripristinati")
        
    except Exception as e:
        print(f"✗ Errore ripristino: {e}")

# Comando rapido
def emergency_fix():
    """Fix di emergenza"""
    disable_iderp_custom_fields()

# Alias
ef = emergency_fix
