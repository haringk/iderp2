# iderp/universal_setup_fix.py
"""
Fix per setup sistema universale
Installa campi e configura demo in modo più robusto
"""

import frappe

def fix_universal_setup_complete():
    """
    Fix completo per sistema universale
    """
    print("\n" + "="*60)
    print("🔧 FIX SETUP UNIVERSALE COMPLETO")
    print("="*60)
    
    # 1. Fix struttura DocType
    fix_doctype_fields()
    
    # 2. Setup demo robusto
    setup_demo_robust()
    
    # 3. Test finale
    test_all_types()
    
    print("\n✅ FIX UNIVERSALE COMPLETATO!")

def fix_doctype_fields():
    """
    Fix campi DocType per sistema universale
    """
    print("\n1. 🏗️ Fix struttura DocType...")
    
    # Fix Item Pricing Tier
    try:
        if frappe.db.exists("DocType", "Item Pricing Tier"):
            doctype_doc = frappe.get_doc("DocType", "Item Pricing Tier")
            
            # Verifica se ha selling_type
            has_selling_type = any(field.fieldname == "selling_type" for field in doctype_doc.fields)
            
            if not has_selling_type:
                print("   Aggiungendo campo selling_type...")
                
                # Aggiungi selling_type all'inizio
                new_field = {
                    "fieldname": "selling_type",
                    "fieldtype": "Select",
                    "label": "Tipo Vendita",
                    "options": "\nMetro Quadrato\nMetro Lineare\nPezzo",
                    "reqd": 1,
                    "in_list_view": 1,
                    "columns": 2,
                    "idx": 1
                }
                doctype_doc.insert(0, "fields", new_field)
                
                # Rinomina campi esistenti se necessario
                for field in doctype_doc.fields:
                    if field.fieldname == "from_sqm":
                        field.fieldname = "from_qty"
                        field.label = "Da Quantità"
                    elif field.fieldname == "to_sqm":
                        field.fieldname = "to_qty"  
                        field.label = "A Quantità"
                    elif field.fieldname == "price_per_sqm":
                        field.fieldname = "price_per_unit"
                        field.label = "Prezzo/Unità"
                
                doctype_doc.save()
                print("   ✓ Item Pricing Tier aggiornato")
            else:
                print("   ✓ Item Pricing Tier già aggiornato")
        
        # Fix Customer Group Minimum
        if frappe.db.exists("DocType", "Customer Group Minimum"):
            doctype_doc = frappe.get_doc("DocType", "Customer Group Minimum")
            
            has_selling_type = any(field.fieldname == "selling_type" for field in doctype_doc.fields)
            
            if not has_selling_type:
                print("   Aggiungendo campi universali a Customer Group Minimum...")
                
                # Trova posizione dopo customer_group
                insert_idx = 1
                for i, field in enumerate(doctype_doc.fields):
                    if field.fieldname == "customer_group":
                        insert_idx = i + 1
                        break
                
                # Aggiungi selling_type
                new_field = {
                    "fieldname": "selling_type",
                    "fieldtype": "Select",
                    "label": "Tipo Vendita",
                    "options": "\nMetro Quadrato\nMetro Lineare\nPezzo",
                    "reqd": 1,
                    "in_list_view": 1,
                    "columns": 2,
                    "idx": insert_idx + 1
                }
                doctype_doc.insert(insert_idx, "fields", new_field)
                
                # Rinomina min_sqm in min_qty se esiste
                for field in doctype_doc.fields:
                    if field.fieldname == "min_sqm":
                        field.fieldname = "min_qty"
                        field.label = "Quantità Minima"
                        field.description = "m², ml, o pezzi minimi fatturabili"
                
                doctype_doc.save()
                print("   ✓ Customer Group Minimum aggiornato")
            else:
                print("   ✓ Customer Group Minimum già aggiornato")
                
    except Exception as e:
        print(f"   ❌ Errore fix DocType: {e}")

def setup_demo_robust():
    """
    Setup demo robusto passo per passo
    """
    print("\n2. 📋 Setup demo robusto...")
    
    # Trova item di test
    test_item = frappe.db.get_value("Item", {"supports_custom_measurement": 1}, "item_code")
    
    if not test_item:
        print("   ❌ Nessun item configurato per misure personalizzate")
        return False
    
    print(f"   Configurando item: {test_item}")
    
    try:
        item_doc = frappe.get_doc("Item", test_item)
        
        # 1. PRIMA pulisci tutto
        item_doc.pricing_tiers = []
        item_doc.customer_group_minimums = []
        
        # 2. Aggiungi scaglioni UNO per volta per evitare errori
        print("   Aggiungendo scaglioni Metro Quadrato...")
        
        # Metro Quadrato (compatibile con esistente)
        mq_tiers = [
            {
                "selling_type": "Metro Quadrato",
                "from_qty": 0.0,
                "to_qty": 0.5,
                "price_per_unit": 20.0,
                "tier_name": "Micro m²"
            },
            {
                "selling_type": "Metro Quadrato", 
                "from_qty": 0.5,
                "to_qty": 2.0,
                "price_per_unit": 15.0,
                "tier_name": "Piccolo m²"
            },
            {
                "selling_type": "Metro Quadrato",
                "from_qty": 2.0,
                "to_qty": None,
                "price_per_unit": 10.0,
                "tier_name": "Grande m²",
                "is_default": 1
            }
        ]
        
        for tier in mq_tiers:
            item_doc.append("pricing_tiers", tier)
        
        print("   Aggiungendo scaglioni Metro Lineare...")
        
        # Metro Lineare
        ml_tiers = [
            {
                "selling_type": "Metro Lineare",
                "from_qty": 0.0,
                "to_qty": 5.0,
                "price_per_unit": 8.0,
                "tier_name": "Piccolo ml"
            },
            {
                "selling_type": "Metro Lineare",
                "from_qty": 5.0,
                "to_qty": 20.0,
                "price_per_unit": 6.0,
                "tier_name": "Medio ml"
            },
            {
                "selling_type": "Metro Lineare",
                "from_qty": 20.0,
                "to_qty": None,
                "price_per_unit": 4.0,
                "tier_name": "Grande ml",
                "is_default": 1
            }
        ]
        
        for tier in ml_tiers:
            item_doc.append("pricing_tiers", tier)
        
        print("   Aggiungendo scaglioni Pezzo...")
        
        # Pezzo
        pz_tiers = [
            {
                "selling_type": "Pezzo",
                "from_qty": 1.0,
                "to_qty": 10.0,
                "price_per_unit": 5.0,
                "tier_name": "Retail"
            },
            {
                "selling_type": "Pezzo",
                "from_qty": 10.0,
                "to_qty": 100.0,
                "price_per_unit": 3.0,
                "tier_name": "Wholesale"
            },
            {
                "selling_type": "Pezzo",
                "from_qty": 100.0,
                "to_qty": None,
                "price_per_unit": 2.0,
                "tier_name": "Bulk",
                "is_default": 1
            }
        ]
        
        for tier in pz_tiers:
            item_doc.append("pricing_tiers", tier)
        
        print("   Aggiungendo minimi customer group...")
        
        # 3. Aggiungi minimi solo per gruppi esistenti
        existing_groups = ["Finale", "Bronze", "Gold", "Diamond"]
        for group in existing_groups:
            if frappe.db.exists("Customer Group", group):
                
                # Metro Quadrato
                item_doc.append("customer_group_minimums", {
                    "customer_group": group,
                    "selling_type": "Metro Quadrato",
                    "min_qty": 0.5 if group == "Finale" else (0.25 if group == "Bronze" else (0.1 if group == "Gold" else 0)),
                    "calculation_mode": "Globale Preventivo" if group in ["Finale", "Gold"] else "Per Riga",
                    "fixed_cost": 5.0 if group == "Finale" else 0,
                    "fixed_cost_mode": "Per Preventivo",
                    "enabled": 1,
                    "description": f"Minimo m² per {group}"
                })
                
                # Metro Lineare  
                item_doc.append("customer_group_minimums", {
                    "customer_group": group,
                    "selling_type": "Metro Lineare",
                    "min_qty": 2.0 if group == "Finale" else (1.0 if group == "Bronze" else (0.5 if group == "Gold" else 0)),
                    "calculation_mode": "Per Riga",
                    "fixed_cost": 3.0 if group == "Finale" else 0,
                    "fixed_cost_mode": "Per Riga",
                    "enabled": 1,
                    "description": f"Minimo ml per {group}"
                })
                
                # Pezzo
                item_doc.append("customer_group_minimums", {
                    "customer_group": group,
                    "selling_type": "Pezzo", 
                    "min_qty": 5 if group == "Finale" else (3 if group == "Bronze" else (1 if group == "Gold" else 0)),
                    "calculation_mode": "Per Riga",
                    "fixed_cost": 0,
                    "fixed_cost_mode": "Per Riga",
                    "enabled": 1,
                    "description": f"Minimo pezzi per {group}"
                })
        
        # 4. Salva tutto
        item_doc.save(ignore_permissions=True)
        
        print(f"   ✅ Item {test_item} configurato con:")
        print(f"      • {len([t for t in item_doc.pricing_tiers if t.selling_type == 'Metro Quadrato'])} scaglioni Metro Quadrato")
        print(f"      • {len([t for t in item_doc.pricing_tiers if t.selling_type == 'Metro Lineare'])} scaglioni Metro Lineare")
        print(f"      • {len([t for t in item_doc.pricing_tiers if t.selling_type == 'Pezzo'])} scaglioni Pezzo")
        print(f"      • {len(item_doc.customer_group_minimums)} minimi gruppo cliente")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Errore setup demo: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_types():
    """
    Test tutti i tipi di vendita
    """
    print("\n3. 🧪 Test tutti i tipi...")
    
    from iderp.pricing_utils import calculate_universal_item_pricing
    
    tests = [
        {
            "nome": "Metro Quadrato",
            "args": {
                "item_code": "AM",
                "tipo_vendita": "Metro Quadrato", 
                "base": 30,
                "altezza": 40,
                "qty": 1,
                "customer": "cliente finale"
            }
        },
        {
            "nome": "Metro Lineare",
            "args": {
                "item_code": "AM",
                "tipo_vendita": "Metro Lineare",
                "lunghezza": 50,
                "qty": 1,
                "customer": "cliente finale"  
            }
        },
        {
            "nome": "Pezzo",
            "args": {
                "item_code": "AM",
                "tipo_vendita": "Pezzo",
                "qty": 3,
                "customer": "cliente finale"
            }
        }
    ]
    
    for test in tests:
        try:
            result = calculate_universal_item_pricing(**test["args"])
            
            if result.get("success"):
                print(f"   ✅ {test['nome']}: €{result['rate']} - {result.get('tier_info', {}).get('tier_name', 'OK')}")
            else:
                print(f"   ❌ {test['nome']}: {result.get('error', 'Errore sconosciuto')}")
                
        except Exception as e:
            print(f"   ❌ {test['nome']}: Errore test - {e}")

# Comandi rapidi
def quick_fix():
    """Comando rapido: fix completo"""
    fix_universal_setup_complete()

def quick_demo():
    """Comando rapido: solo demo"""
    setup_demo_robust()

def quick_test():
    """Comando rapido: solo test"""
    test_all_types()

# Alias
qf = quick_fix
qd = quick_demo
qt = quick_test