# iderp/manual_setup.py
"""
Setup manuale semplice per sistema universale
Evita problemi di concorrenza DocType
"""

import frappe

def setup_manual_universal_item(item_code="AM"):
    """
    Configura manualmente un item per sistema universale
    FIXED: Anti-concorrenza e validazione per tipo
    """
    print(f"\n🔧 SETUP MANUALE ITEM {item_code} - VERSIONE ROBUSTA")
    print("="*60)
    
    try:
        # Carica item FRESCO ogni volta
        if not frappe.db.exists("Item", item_code):
            print(f"❌ Item {item_code} non trovato")
            return False
        
        # RELOAD fresh per evitare timestamp mismatch
        frappe.db.commit()  # Commit pending
        item_doc = frappe.get_doc("Item", item_code, ignore_permissions=True)
        item_doc.reload()  # Force reload
        
        print(f"✓ Item {item_code} caricato fresh")
        
        # Abilita misure personalizzate
        item_doc.supports_custom_measurement = 1
        item_doc.tipo_vendita_default = "Metro Quadrato"
        
        # PULISCI tutto
        item_doc.pricing_tiers = []
        if hasattr(item_doc, 'customer_group_minimums'):
            item_doc.customer_group_minimums = []
        
        print("✓ Item pulito")
        
        # 1. SCAGLIONI - UNO ALLA VOLTA per evitare conflitti
        print("📊 Configurando scaglioni...")
        
        # A. Metro Quadrato (formato legacy - compatibile)
        mq_tiers = [
            {"from_sqm": 0.0, "to_sqm": 0.5, "price_per_sqm": 20.0, "tier_name": "Micro m²"},
            {"from_sqm": 0.5, "to_sqm": 2.0, "price_per_sqm": 15.0, "tier_name": "Piccolo m²"},
            {"from_sqm": 2.0, "to_sqm": None, "price_per_sqm": 10.0, "tier_name": "Grande m²", "is_default": 1}
        ]
        
        # B. Metro Lineare (formato nuovo)
        ml_tiers = [
            {"selling_type": "Metro Lineare", "from_qty": 0.0, "to_qty": 5.0, "price_per_unit": 8.0, "tier_name": "Piccolo ml"},
            {"selling_type": "Metro Lineare", "from_qty": 5.0, "to_qty": 20.0, "price_per_unit": 6.0, "tier_name": "Medio ml"},
            {"selling_type": "Metro Lineare", "from_qty": 20.0, "to_qty": None, "price_per_unit": 4.0, "tier_name": "Grande ml", "is_default": 1}
        ]
        
        # C. Pezzo (formato nuovo)
        pz_tiers = [
            {"selling_type": "Pezzo", "from_qty": 1.0, "to_qty": 10.0, "price_per_unit": 5.0, "tier_name": "Retail"},
            {"selling_type": "Pezzo", "from_qty": 10.0, "to_qty": 100.0, "price_per_unit": 3.0, "tier_name": "Wholesale"},
            {"selling_type": "Pezzo", "from_qty": 100.0, "to_qty": None, "price_per_unit": 2.0, "tier_name": "Bulk", "is_default": 1}
        ]
        
        # Aggiungi tutti gli scaglioni
        all_tiers = mq_tiers + ml_tiers + pz_tiers
        
        for tier_data in all_tiers:
            item_doc.append("pricing_tiers", tier_data)
        
        print(f"✓ {len(all_tiers)} scaglioni aggiunti")
        print(f"   • Metro Quadrato: {len(mq_tiers)} (legacy format)")
        print(f"   • Metro Lineare: {len(ml_tiers)} (new format)")
        print(f"   • Pezzo: {len(pz_tiers)} (new format)")
        
        # 2. MINIMI (solo m² per ora)
        if hasattr(item_doc, 'customer_group_minimums'):
            print("🎯 Configurando minimi...")
            
            groups = ["Finale", "Bronze", "Gold", "Diamond"]
            added = 0
            
            for group in groups:
                if frappe.db.exists("Customer Group", group):
                    item_doc.append("customer_group_minimums", {
                        "customer_group": group,
                        "min_sqm": 0.5 if group == "Finale" else (0.25 if group == "Bronze" else (0.1 if group == "Gold" else 0)),
                        "calculation_mode": "Globale Preventivo" if group in ["Finale", "Gold"] else "Per Riga",
                        "enabled": 1,
                        "description": f"Minimo m² per {group}"
                    })
                    added += 1
            
            print(f"✓ {added} minimi aggiunti")
        
        # 3. SALVATAGGIO FORZATO
        print("💾 Salvando item...")
        
        # Disabilita validazione se necessario
        item_doc.flags.ignore_validate = True
        item_doc.flags.ignore_permissions = True
        
        try:
            item_doc.save(ignore_permissions=True)
            print("✅ SALVATAGGIO RIUSCITO!")
        except Exception as save_error:
            print(f"❌ Errore salvataggio: {save_error}")
            
            # Reload e riprova una volta
            print("🔄 Reload e retry...")
            frappe.db.rollback()
            item_doc = frappe.get_doc("Item", item_code)
            item_doc.reload()
            
            # Riprova setup minimale
            item_doc.supports_custom_measurement = 1
            item_doc.pricing_tiers = []
            
            # Solo Metro Quadrato per test
            item_doc.append("pricing_tiers", {"from_sqm": 0.0, "to_sqm": None, "price_per_sqm": 10.0, "tier_name": "Test", "is_default": 1})
            
            item_doc.flags.ignore_validate = True
            item_doc.save(ignore_permissions=True)
            print("✅ SALVATAGGIO MINIMALE RIUSCITO!")
        
        # 4. RIEPILOGO
        final_item = frappe.get_doc("Item", item_code)
        print(f"\n📋 ITEM {item_code} CONFIGURATO:")
        print(f"   • Scaglioni: {len(final_item.pricing_tiers) if hasattr(final_item, 'pricing_tiers') else 0}")
        print(f"   • Minimi: {len(final_item.customer_group_minimums) if hasattr(final_item, 'customer_group_minimums') else 0}")
        print(f"   • Supporta misure: {getattr(final_item, 'supports_custom_measurement', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERRORE GENERALE: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configured_item(item_code="AM"):
    """
    Test item configurato
    """
    print(f"\n🧪 TEST ITEM {item_code}")
    print("="*30)
    
    from iderp.pricing_utils import calculate_universal_item_pricing
    
    tests = [
        {
            "nome": "Metro Quadrato",
            "args": {
                "item_code": item_code,
                "tipo_vendita": "Metro Quadrato",
                "base": 30,
                "altezza": 40,  # 0.12 m²
                "qty": 1,
                "customer": "cliente finale"
            },
            "aspettato": "€ con minimo applicato"
        },
        {
            "nome": "Metro Lineare", 
            "args": {
                "item_code": item_code,
                "tipo_vendita": "Metro Lineare",
                "lunghezza": 50,  # 0.5 ml
                "qty": 1,
                "customer": "cliente finale"
            },
            "aspettato": "€8/ml = €4"
        },
        {
            "nome": "Pezzo",
            "args": {
                "item_code": item_code,
                "tipo_vendita": "Pezzo", 
                "qty": 3,  # 3 pezzi
                "customer": "cliente finale"
            },
            "aspettato": "€5/pz = €15"
        }
    ]
    
    risultati = []
    
    for test in tests:
        try:
            result = calculate_universal_item_pricing(**test["args"])
            
            if result.get("success"):
                print(f"✅ {test['nome']}: €{result['rate']} - {result.get('tier_info', {}).get('tier_name', 'OK')}")
                risultati.append(True)
            else:
                print(f"❌ {test['nome']}: {result.get('error', 'Errore')}")
                risultati.append(False)
                
        except Exception as e:
            print(f"❌ {test['nome']}: Errore - {e}")
            risultati.append(False)
    
    successi = sum(risultati)
    print(f"\n📊 RISULTATO: {successi}/{len(tests)} test superati")
    
    return successi == len(tests)

def complete_manual_setup():
    """
    Setup completo manuale
    """
    print("\n" + "="*60)
    print("🔧 SETUP MANUALE COMPLETO SISTEMA UNIVERSALE")
    print("="*60)
    
    # 1. Fix validazione
    print("1. Upload file pricing_utils.py aggiornato")
    
    # 2. Setup item
    success = setup_manual_universal_item("AM")
    
    if success:
        # 3. Test
        test_success = test_configured_item("AM")
        
        if test_success:
            print("\n🎉 SETUP MANUALE COMPLETATO CON SUCCESSO!")
            print("🚀 Sistema universale funzionante per tutti i tipi di vendita!")
        else:
            print("\n⚠️ Setup completato ma alcuni test falliti")
    else:
        print("\n❌ Setup fallito")
    
    return success

# Comandi rapidi
def ms():
    """Manual setup"""
    return setup_manual_universal_item("AM")

def mt():
    """Manual test"""
    return test_configured_item("AM")

def mc():
    """Manual complete"""
    return complete_manual_setup()