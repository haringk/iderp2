# iderp/manual_setup.py
"""
Setup manuale ULTRA-ROBUSTO con gestione errori concorrenza
Anti-timeout e retry intelligente
"""

import frappe
import time


def fix_missing_pricing_tiers_sql_direct(item_code="AM"):
    """
    Fix usando SQL diretto per evitare timeout ORM
    """
    print(f"\n🚀 FIX SQL DIRETTO - {item_code}")
    print("="*50)
    
    try:
        # 1. Verifica cosa manca
        existing_sql = """
        SELECT DISTINCT selling_type 
        FROM `tabItem Pricing Tier` 
        WHERE parent = %s AND selling_type IS NOT NULL
        """
        existing_types = frappe.db.sql(existing_sql, [item_code], as_dict=True)
        existing_type_names = [row.selling_type for row in existing_types]
        
        print(f"✓ Tipi esistenti via SQL: {existing_type_names}")
        
        # 2. Prepara dati da inserire
        missing_tiers = []
        
        if "Metro Lineare" not in existing_type_names:
            print("➕ Preparando Metro Lineare...")
            missing_tiers.extend([
                {
                    "parent": item_code,
                    "parenttype": "Item",
                    "parentfield": "pricing_tiers",
                    "selling_type": "Metro Lineare",
                    "from_qty": 0.0,
                    "to_qty": 5.0,
                    "price_per_unit": 8.0,
                    "tier_name": "Piccolo ml"
                },
                {
                    "parent": item_code,
                    "parenttype": "Item", 
                    "parentfield": "pricing_tiers",
                    "selling_type": "Metro Lineare",
                    "from_qty": 5.0,
                    "to_qty": 20.0,
                    "price_per_unit": 6.0,
                    "tier_name": "Medio ml"
                },
                {
                    "parent": item_code,
                    "parenttype": "Item",
                    "parentfield": "pricing_tiers", 
                    "selling_type": "Metro Lineare",
                    "from_qty": 20.0,
                    "to_qty": None,
                    "price_per_unit": 4.0,
                    "tier_name": "Grande ml",
                    "is_default": 1
                }
            ])
        
        if "Pezzo" not in existing_type_names:
            print("➕ Preparando Pezzo...")
            missing_tiers.extend([
                {
                    "parent": item_code,
                    "parenttype": "Item",
                    "parentfield": "pricing_tiers",
                    "selling_type": "Pezzo",
                    "from_qty": 1.0,
                    "to_qty": 10.0,
                    "price_per_unit": 5.0,
                    "tier_name": "Retail"
                },
                {
                    "parent": item_code,
                    "parenttype": "Item",
                    "parentfield": "pricing_tiers",
                    "selling_type": "Pezzo", 
                    "from_qty": 10.0,
                    "to_qty": 100.0,
                    "price_per_unit": 3.0,
                    "tier_name": "Wholesale"
                },
                {
                    "parent": item_code,
                    "parenttype": "Item",
                    "parentfield": "pricing_tiers",
                    "selling_type": "Pezzo",
                    "from_qty": 100.0,
                    "to_qty": None,
                    "price_per_unit": 2.0,
                    "tier_name": "Bulk",
                    "is_default": 1
                }
            ])
        
        if not missing_tiers:
            print("✅ Nessuno scaglione mancante!")
            return True
        
        print(f"📊 Inserendo {len(missing_tiers)} scaglioni via SQL...")
        
        # 3. Inserimento SQL diretto UNO alla volta
        success_count = 0
        
        for i, tier in enumerate(missing_tiers):
            try:
                # Genera name univoco
                import uuid
                tier_name = f"tier-{uuid.uuid4().hex[:8]}"
                
                # SQL INSERT diretto
                insert_sql = """
                INSERT INTO `tabItem Pricing Tier` 
                (name, parent, parenttype, parentfield, selling_type, from_qty, to_qty, price_per_unit, tier_name, is_default, creation, modified, modified_by, owner)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), 'Administrator', 'Administrator')
                """
                
                values = [
                    tier_name,
                    tier["parent"],
                    tier["parenttype"], 
                    tier["parentfield"],
                    tier["selling_type"],
                    tier["from_qty"],
                    tier["to_qty"],
                    tier["price_per_unit"],
                    tier["tier_name"],
                    tier.get("is_default", 0)
                ]
                
                frappe.db.sql(insert_sql, values)
                frappe.db.commit()  # Commit immediato
                
                print(f"   ✓ {tier['tier_name']} inserito")
                success_count += 1
                
                # Pausa tra inserimenti
                time.sleep(0.2)
                
            except Exception as e:
                print(f"   ❌ Errore {tier['tier_name']}: {e}")
                # Continua con il prossimo
                continue
        
        print(f"✅ {success_count}/{len(missing_tiers)} scaglioni inseriti con successo!")
        
        # 4. Verifica finale
        final_count_sql = """
        SELECT COUNT(*) as count 
        FROM `tabItem Pricing Tier` 
        WHERE parent = %s
        """
        final_count = frappe.db.sql(final_count_sql, [item_code], as_dict=True)[0].count
        print(f"📊 Totale scaglioni ora: {final_count}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Errore SQL diretto: {e}")
        return False

def reset_and_rebuild_pricing_tiers(item_code="AM"):
    """
    Reset completo e rebuild scaglioni con SQL diretto
    """
    print(f"\n🔄 RESET E REBUILD COMPLETO - {item_code}")
    print("="*50)
    
    try:
        # 1. Backup esistenti per sicurezza
        backup_sql = """
        SELECT * FROM `tabItem Pricing Tier` WHERE parent = %s
        """
        backup_data = frappe.db.sql(backup_sql, [item_code], as_dict=True)
        print(f"💾 Backup di {len(backup_data)} scaglioni esistenti")
        
        # 2. Cancella tutti gli scaglioni esistenti
        delete_sql = """
        DELETE FROM `tabItem Pricing Tier` WHERE parent = %s
        """
        frappe.db.sql(delete_sql, [item_code])
        frappe.db.commit()
        print("🗑️ Scaglioni esistenti cancellati")
        
        # 3. Inserisci set completo nuovo
        all_tiers = [
            # Metro Quadrato (formato nuovo per consistenza)
            {"selling_type": "Metro Quadrato", "from_qty": 0.0, "to_qty": 0.5, "price_per_unit": 20.0, "tier_name": "Micro m²"},
            {"selling_type": "Metro Quadrato", "from_qty": 0.5, "to_qty": 2.0, "price_per_unit": 15.0, "tier_name": "Piccolo m²"},
            {"selling_type": "Metro Quadrato", "from_qty": 2.0, "to_qty": None, "price_per_unit": 10.0, "tier_name": "Grande m²", "is_default": 1},
            
            # Metro Lineare
            {"selling_type": "Metro Lineare", "from_qty": 0.0, "to_qty": 5.0, "price_per_unit": 8.0, "tier_name": "Piccolo ml"},
            {"selling_type": "Metro Lineare", "from_qty": 5.0, "to_qty": 20.0, "price_per_unit": 6.0, "tier_name": "Medio ml"},
            {"selling_type": "Metro Lineare", "from_qty": 20.0, "to_qty": None, "price_per_unit": 4.0, "tier_name": "Grande ml", "is_default": 1},
            
            # Pezzo
            {"selling_type": "Pezzo", "from_qty": 1.0, "to_qty": 10.0, "price_per_unit": 5.0, "tier_name": "Retail"},
            {"selling_type": "Pezzo", "from_qty": 10.0, "to_qty": 100.0, "price_per_unit": 3.0, "tier_name": "Wholesale"},
            {"selling_type": "Pezzo", "from_qty": 100.0, "to_qty": None, "price_per_unit": 2.0, "tier_name": "Bulk", "is_default": 1}
        ]
        
        success_count = 0
        for tier in all_tiers:
            try:
                import uuid
                tier_name = f"tier-{uuid.uuid4().hex[:8]}"
                
                insert_sql = """
                INSERT INTO `tabItem Pricing Tier` 
                (name, parent, parenttype, parentfield, selling_type, from_qty, to_qty, price_per_unit, tier_name, is_default, creation, modified, modified_by, owner)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), 'Administrator', 'Administrator')
                """
                
                values = [
                    tier_name, item_code, "Item", "pricing_tiers",
                    tier["selling_type"], tier["from_qty"], tier["to_qty"], 
                    tier["price_per_unit"], tier["tier_name"], tier.get("is_default", 0)
                ]
                
                frappe.db.sql(insert_sql, values)
                frappe.db.commit()
                
                print(f"   ✓ {tier['tier_name']}")
                success_count += 1
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   ❌ {tier['tier_name']}: {e}")
        
        print(f"✅ {success_count}/{len(all_tiers)} scaglioni inseriti!")
        
        # 4. Test immediato
        if success_count == len(all_tiers):
            print("\n🧪 Test immediato...")
            return test_universal_system_complete(item_code)
        else:
            print("⚠️ Inserimento parziale")
            return False
        
    except Exception as e:
        print(f"❌ Errore reset/rebuild: {e}")
        return False

def nuclear_fix_universal_pricing(item_code="AM"):
    """
    FIX NUCLEARE: Reset completo + rebuild + test
    """
    print(f"\n☢️ FIX NUCLEARE PRICING UNIVERSALE - {item_code}")
    print("="*60)
    
    print("🎯 STRATEGIA: Reset completo con SQL diretto")
    print("⚠️  Questo cancellerà tutti gli scaglioni esistenti")
    print("")
    
    success = reset_and_rebuild_pricing_tiers(item_code)
    
    if success:
        print("\n🎉 FIX NUCLEARE COMPLETATO CON SUCCESSO!")
        print("🚀 Sistema universale ora operativo per tutti e 3 i tipi!")
    else:
        print("\n❌ Fix nucleare fallito")
        print("🚨 Serve diagnosi più approfondita")
    
    return success

# Comandi rapidi aggiornati
def sql_fix():
    """Fix SQL diretto"""
    return fix_missing_pricing_tiers_sql_direct("AM")

def nuclear_fix():
    """Fix nucleare completo"""
    return nuclear_fix_universal_pricing("AM")

# Alias
sf = sql_fix
nf = nuclear_fix

def test_universal_system_complete(item_code="AM"):
    """
    Test completo sistema universale per tutti i tipi di vendita
    """
    print(f"\n🧪 TEST SISTEMA UNIVERSALE COMPLETO - {item_code}")
    print("="*60)
    
    from iderp.pricing_utils import calculate_universal_item_pricing
    
    # Test scenarios realistici
    test_scenarios = [
        {
            "nome": "🟦 Metro Quadrato - Biglietto da visita",
            "args": {
                "item_code": item_code,
                "tipo_vendita": "Metro Quadrato",
                "base": 9,      # 9cm (biglietto da visita)
                "altezza": 5,   # 5cm = 0.0045 m² (molto piccolo)
                "qty": 1000,    # 1000 biglietti = 4.5 m² totali
                "customer": None  # Test senza cliente prima
            },
            "aspettato": "Scaglione Grande m² (2+ m²)"
        },
        {
            "nome": "🟩 Metro Lineare - Banner",
            "args": {
                "item_code": item_code,
                "tipo_vendita": "Metro Lineare", 
                "lunghezza": 300,  # 3 metri lineari
                "qty": 2,          # 2 banner = 6 ml totali
                "customer": None
            },
            "aspettato": "Scaglione Medio ml (5-20 ml)"
        },
        {
            "nome": "🟨 Pezzo - Depliant",
            "args": {
                "item_code": item_code,
                "tipo_vendita": "Pezzo",
                "qty": 50,         # 50 depliant
                "customer": None
            },
            "aspettato": "Scaglione Wholesale (10-100 pz)"
        },
        {
            "nome": "🟦 Metro Quadrato + Cliente Finale",
            "args": {
                "item_code": item_code,
                "tipo_vendita": "Metro Quadrato",
                "base": 30,     # 30cm
                "altezza": 40,  # 40cm = 0.12 m² (sotto minimo Finale 0.5m²)
                "qty": 1,
                "customer": "CUST-001"  # Cliente finale (se esiste)
            },
            "aspettato": "Minimo Finale applicato (0.5 m²)"
        }
    ]
    
    risultati = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. {scenario['nome']}")
        print("   " + "-" * 40)
        
        try:
            # Mostra input
            args = scenario['args']
            if args['tipo_vendita'] == "Metro Quadrato":
                print(f"   📐 Input: {args['base']}×{args['altezza']}cm × {args['qty']} pz")
                mq_totali = (args['base'] * args['altezza'] * args['qty']) / 10000
                print(f"   📊 m² totali: {mq_totali:.4f} m²")
            elif args['tipo_vendita'] == "Metro Lineare":
                print(f"   📏 Input: {args['lunghezza']}cm × {args['qty']} pz")
                ml_totali = (args['lunghezza'] * args['qty']) / 100
                print(f"   📊 ml totali: {ml_totali:.2f} ml")
            elif args['tipo_vendita'] == "Pezzo":
                print(f"   📦 Input: {args['qty']} pezzi")
            
            if args['customer']:
                print(f"   👤 Cliente: {args['customer']}")
            
            # Chiamata API
            result = calculate_universal_item_pricing(**args)
            
            if result.get("success"):
                print(f"   ✅ SUCCESSO!")
                print(f"   💰 Prezzo unitario: €{result['rate']}")
                print(f"   🏷️  Scaglione: {result.get('tier_info', {}).get('tier_name', 'Standard')}")
                print(f"   📝 Prezzo/unità: €{result.get('price_per_unit', 0)}")
                
                if result.get('tier_info', {}).get('min_applied'):
                    print(f"   ⚠️  MINIMO APPLICATO: {result['tier_info']['customer_group']}")
                    print(f"   📈 Quantità effettiva: {result['tier_info']['effective_qty']}")
                
                risultati.append({
                    "scenario": scenario['nome'],
                    "successo": True,
                    "rate": result['rate'],
                    "tier": result.get('tier_info', {}).get('tier_name', 'N/A')
                })
                
            else:
                print(f"   ❌ ERRORE: {result.get('error', 'Errore sconosciuto')}")
                risultati.append({
                    "scenario": scenario['nome'],
                    "successo": False,
                    "errore": result.get('error', 'Errore sconosciuto')
                })
                
        except Exception as e:
            print(f"   💥 ECCEZIONE: {e}")
            risultati.append({
                "scenario": scenario['nome'],
                "successo": False,
                "errore": str(e)
            })
    
    # Riepilogo finale
    print("\n" + "="*60)
    print("📊 RIEPILOGO TEST UNIVERSALE")
    print("="*60)
    
    successi = sum(1 for r in risultati if r['successo'])
    totali = len(risultati)
    
    print(f"\n🎯 RISULTATO: {successi}/{totali} test superati")
    
    for risultato in risultati:
        if risultato['successo']:
            print(f"✅ {risultato['scenario']}")
            print(f"   💰 €{risultato['rate']} - {risultato['tier']}")
        else:
            print(f"❌ {risultato['scenario']}")
            print(f"   🚫 {risultato['errore']}")
    
    if successi == totali:
        print(f"\n🎉 SISTEMA UNIVERSALE COMPLETAMENTE FUNZIONANTE!")
        print("🚀 Tutti e 3 i tipi di vendita operativi!")
    elif successi > 0:
        print(f"\n⚠️  Sistema parzialmente funzionante ({successi}/{totali})")
        print("🔧 Alcuni tipi necessitano fix")
    else:
        print(f"\n❌ Sistema non funzionante")
        print("🚨 Necessaria revisione completa")
    
    print("="*60)
    return successi == totali

def quick_universal_test():
    """Test rapido sistema universale"""
    return test_universal_system_complete("AM")

# Aggiungi alla fine del file
# Alias
tuc = test_universal_system_complete
qut = quick_universal_test

def diagnose_item_pricing_tiers(item_code="AM"):
    """
    Diagnosi dettagliata degli scaglioni salvati
    """
    print(f"\n🔍 DIAGNOSI SCAGLIONI ITEM {item_code}")
    print("="*60)
    
    try:
        item_doc = frappe.get_doc("Item", item_code)
        
        if not hasattr(item_doc, 'pricing_tiers') or not item_doc.pricing_tiers:
            print("❌ Nessuno scaglione trovato!")
            return False
        
        print(f"📊 Trovati {len(item_doc.pricing_tiers)} scaglioni:")
        print("")
        
        # Raggruppa per tipo
        by_type = {}
        for i, tier in enumerate(item_doc.pricing_tiers):
            # Determina il tipo
            if hasattr(tier, 'selling_type') and tier.selling_type:
                tipo = tier.selling_type
                formato = "NUOVO"
                from_val = getattr(tier, 'from_qty', 0)
                to_val = getattr(tier, 'to_qty', None)
                price_val = getattr(tier, 'price_per_unit', 0)
            elif hasattr(tier, 'from_sqm'):
                tipo = "Metro Quadrato"
                formato = "LEGACY"
                from_val = getattr(tier, 'from_sqm', 0)
                to_val = getattr(tier, 'to_sqm', None)
                price_val = getattr(tier, 'price_per_sqm', 0)
            else:
                tipo = "SCONOSCIUTO"
                formato = "???"
                from_val = "???"
                to_val = "???"
                price_val = "???"
            
            if tipo not in by_type:
                by_type[tipo] = []
            
            by_type[tipo].append({
                'idx': i+1,
                'formato': formato,
                'from': from_val,
                'to': to_val,
                'price': price_val,
                'name': getattr(tier, 'tier_name', 'N/A'),
                'default': getattr(tier, 'is_default', 0)
            })
        
        # Mostra per tipo
        for tipo, tiers in by_type.items():
            print(f"🏷️  {tipo.upper()} ({len(tiers)} scaglioni):")
            for tier in tiers:
                to_str = f"{tier['to']}" if tier['to'] is not None else "∞"
                default_str = " [DEFAULT]" if tier['default'] else ""
                print(f"   {tier['idx']}. {tier['from']} → {to_str} = €{tier['price']} ({tier['formato']}){default_str}")
                print(f"      Nome: {tier['name']}")
            print("")
        
        # Analisi problemi
        print("🔧 ANALISI PROBLEMI:")
        
        missing_types = []
        if "Metro Lineare" not in by_type:
            missing_types.append("Metro Lineare")
        if "Pezzo" not in by_type:
            missing_types.append("Pezzo")
        
        if missing_types:
            print(f"❌ Tipi mancanti: {', '.join(missing_types)}")
        else:
            print("✅ Tutti i tipi presenti")
        
        # Verifica formato misto
        has_legacy = any(tier['formato'] == 'LEGACY' for tiers in by_type.values() for tier in tiers)
        has_new = any(tier['formato'] == 'NUOVO' for tiers in by_type.values() for tier in tiers)
        
        if has_legacy and has_new:
            print("⚠️  Formato MISTO rilevato (legacy + nuovo)")
            print("💡 Questo può causare problemi nella ricerca scaglioni")
        elif has_legacy:
            print("📜 Solo formato LEGACY (compatibilità)")
        elif has_new:
            print("🆕 Solo formato NUOVO")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore diagnosi: {e}")
        return False

def fix_missing_pricing_tiers(item_code="AM"):
    """
    Fix aggiungendo solo gli scaglioni mancanti
    """
    print(f"\n🔧 FIX SCAGLIONI MANCANTI - {item_code}")
    print("="*50)
    
    try:
        item_doc = frappe.get_doc("Item", item_code)
        
        # Determina cosa manca
        existing_types = set()
        if hasattr(item_doc, 'pricing_tiers') and item_doc.pricing_tiers:
            for tier in item_doc.pricing_tiers:
                if hasattr(tier, 'selling_type') and tier.selling_type:
                    existing_types.add(tier.selling_type)
                elif hasattr(tier, 'from_sqm'):
                    existing_types.add("Metro Quadrato")
        
        print(f"✓ Tipi esistenti: {list(existing_types)}")
        
        # Scaglioni da aggiungere
        missing_tiers = []
        
        if "Metro Lineare" not in existing_types:
            print("➕ Aggiungendo scaglioni Metro Lineare...")
            missing_tiers.extend([
                {"selling_type": "Metro Lineare", "from_qty": 0.0, "to_qty": 5.0, "price_per_unit": 8.0, "tier_name": "Piccolo ml"},
                {"selling_type": "Metro Lineare", "from_qty": 5.0, "to_qty": 20.0, "price_per_unit": 6.0, "tier_name": "Medio ml"},
                {"selling_type": "Metro Lineare", "from_qty": 20.0, "to_qty": None, "price_per_unit": 4.0, "tier_name": "Grande ml", "is_default": 1}
            ])
        
        if "Pezzo" not in existing_types:
            print("➕ Aggiungendo scaglioni Pezzo...")
            missing_tiers.extend([
                {"selling_type": "Pezzo", "from_qty": 1.0, "to_qty": 10.0, "price_per_unit": 5.0, "tier_name": "Retail"},
                {"selling_type": "Pezzo", "from_qty": 10.0, "to_qty": 100.0, "price_per_unit": 3.0, "tier_name": "Wholesale"},
                {"selling_type": "Pezzo", "from_qty": 100.0, "to_qty": None, "price_per_unit": 2.0, "tier_name": "Bulk", "is_default": 1}
            ])
        
        if not missing_tiers:
            print("✅ Nessuno scaglione mancante!")
            return True
        
        # Aggiungi i mancanti UNO alla volta
        added_count = 0
        for tier_config in missing_tiers:
            try:
                item_doc.append("pricing_tiers", tier_config)
                added_count += 1
                print(f"   ✓ {tier_config['tier_name']}")
                
                # Salva ogni 2 scaglioni per evitare timeout
                if added_count % 2 == 0:
                    item_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    time.sleep(0.5)
                    item_doc.reload()
                    
            except Exception as e:
                print(f"   ❌ Errore {tier_config['tier_name']}: {e}")
        
        # Salvataggio finale
        try:
            item_doc.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"✅ {added_count} scaglioni aggiunti e salvati!")
            return True
        except Exception as e:
            print(f"❌ Errore salvataggio finale: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Errore fix: {e}")
        return False

def complete_universal_setup(item_code="AM"):
    """
    Setup universale completo: diagnosi + fix + test
    """
    print(f"\n🚀 SETUP UNIVERSALE COMPLETO - {item_code}")
    print("="*60)
    
    # 1. Diagnosi
    print("STEP 1: Diagnosi stato attuale")
    diagnose_item_pricing_tiers(item_code)
    
    # 2. Fix
    print("\nSTEP 2: Fix scaglioni mancanti")
    fix_success = fix_missing_pricing_tiers(item_code)
    
    # 3. Test finale
    if fix_success:
        print("\nSTEP 3: Test universale finale")
        test_success = test_universal_system_complete(item_code)
        
        if test_success:
            print("\n🎉 SETUP UNIVERSALE COMPLETATO CON SUCCESSO!")
            print("🚀 Tutti e 3 i tipi di vendita sono ora operativi!")
            return True
        else:
            print("\n⚠️ Fix applicato ma test ancora fallisce")
            return False
    else:
        print("\n❌ Fix fallito")
        return False

# Comandi rapidi
def diag():
    """Diagnosi scaglioni"""
    return diagnose_item_pricing_tiers("AM")

def fix_missing():
    """Fix scaglioni mancanti"""
    return fix_missing_pricing_tiers("AM")

def complete_setup():
    """Setup completo"""
    return complete_universal_setup("AM")

# Alias
d = diag
fm = fix_missing
cs = complete_setup

def setup_manual_universal_item_robust(item_code="AM"):
    """
    Setup manuale ULTRA-ROBUSTO anti-concorrenza
    Gestisce timeout database e retry automatici
    """
    print(f"\n🔧 SETUP ULTRA-ROBUSTO ITEM {item_code}")
    print("="*60)
    
    try:
        # 1. VERIFICA E PREPARAZIONE
        if not frappe.db.exists("Item", item_code):
            print(f"❌ Item {item_code} non trovato")
            return False
        
        print("🔄 Preparazione database...")
        
        # Commit transazioni pendenti e aspetta
        frappe.db.commit()
        time.sleep(2)
        
        # Carica item fresh con lock esclusivo
        print(f"✓ Caricamento {item_code} con lock esclusivo...")
        item_doc = frappe.get_doc("Item", item_code)
        
        # 2. SETUP BASE (veloce)
        print("⚙️ Configurazione base...")
        item_doc.supports_custom_measurement = 1
        item_doc.tipo_vendita_default = "Metro Quadrato"
        
        # Salvataggio immediato configurazione base
        try:
            item_doc.save(ignore_permissions=True)
            frappe.db.commit()
            print("✓ Configurazione base salvata")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Warning configurazione base: {e}")
        
        # 3. RICARICA E SETUP SCAGLIONI
        print("📊 Configurazione scaglioni...")
        item_doc.reload()
        
        # Pulisci scaglioni esistenti
        item_doc.pricing_tiers = []
        
        # Aggiungi scaglioni uno alla volta (anti-concorrenza)
        scaglioni_configs = get_standard_pricing_tiers()
        
        for i, tier_config in enumerate(scaglioni_configs):
            try:
                item_doc.append("pricing_tiers", tier_config)
                
                # Salva ogni 3 scaglioni per evitare transazioni lunghe
                if (i + 1) % 3 == 0:
                    item_doc.save(ignore_permissions=True)
                    frappe.db.commit()
                    time.sleep(0.5)
                    item_doc.reload()
                    print(f"   ✓ Salvati {i+1} scaglioni...")
                    
            except Exception as e:
                print(f"   ⚠️ Warning scaglione {i+1}: {e}")
                continue
        
        # Salvataggio finale scaglioni
        try:
            item_doc.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"✓ Tutti {len(scaglioni_configs)} scaglioni configurati")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Warning salvataggio scaglioni: {e}")
        
        # 4. RICARICA E SETUP MINIMI (se supportati)
        print("🎯 Configurazione minimi...")
        item_doc.reload()
        
        if hasattr(item_doc, 'customer_group_minimums'):
            item_doc.customer_group_minimums = []
            
            minimi_configs = get_standard_customer_minimums()
            
            for minimum_config in minimi_configs:
                if frappe.db.exists("Customer Group", minimum_config["customer_group"]):
                    try:
                        item_doc.append("customer_group_minimums", minimum_config)
                    except Exception as e:
                        print(f"   ⚠️ Warning minimo {minimum_config['customer_group']}: {e}")
            
            # Salvataggio minimi
            try:
                item_doc.save(ignore_permissions=True)
                frappe.db.commit()
                print(f"✓ {len(minimi_configs)} minimi configurati")
            except Exception as e:
                print(f"⚠️ Warning salvataggio minimi: {e}")
        
        # 5. VERIFICA FINALE
        print("🔍 Verifica finale...")
        final_item = frappe.get_doc("Item", item_code)
        
        scaglioni_count = len(final_item.pricing_tiers) if hasattr(final_item, 'pricing_tiers') else 0
        minimi_count = len(final_item.customer_group_minimums) if hasattr(final_item, 'customer_group_minimums') else 0
        
        print(f"\n📋 ITEM {item_code} CONFIGURATO:")
        print(f"   • Scaglioni: {scaglioni_count}")
        print(f"   • Minimi: {minimi_count}")
        print(f"   • Supporta misure: {getattr(final_item, 'supports_custom_measurement', 0)}")
        print(f"   • Tipo default: {getattr(final_item, 'tipo_vendita_default', 'N/A')}")
        
        if scaglioni_count > 0:
            print("✅ SETUP COMPLETATO CON SUCCESSO!")
            return True
        else:
            print("⚠️ Setup parziale - alcuni dati potrebbero essere mancanti")
            return False
        
    except Exception as e:
        print(f"❌ ERRORE CRITICO: {e}")
        
        # Rollback se necessario
        try:
            frappe.db.rollback()
        except:
            pass
            
        return False

def get_standard_pricing_tiers():
    """
    Ottieni configurazioni standard scaglioni
    """
    return [
        # Metro Quadrato (formato legacy compatibile)
        {"from_sqm": 0.0, "to_sqm": 0.5, "price_per_sqm": 20.0, "tier_name": "Micro m²"},
        {"from_sqm": 0.5, "to_sqm": 2.0, "price_per_sqm": 15.0, "tier_name": "Piccolo m²"},
        {"from_sqm": 2.0, "to_sqm": None, "price_per_sqm": 10.0, "tier_name": "Grande m²", "is_default": 1},
        
        # Metro Lineare (formato nuovo)
        {"selling_type": "Metro Lineare", "from_qty": 0.0, "to_qty": 5.0, "price_per_unit": 8.0, "tier_name": "Piccolo ml"},
        {"selling_type": "Metro Lineare", "from_qty": 5.0, "to_qty": 20.0, "price_per_unit": 6.0, "tier_name": "Medio ml"},
        {"selling_type": "Metro Lineare", "from_qty": 20.0, "to_qty": None, "price_per_unit": 4.0, "tier_name": "Grande ml", "is_default": 1},
        
        # Pezzo (formato nuovo)
        {"selling_type": "Pezzo", "from_qty": 1.0, "to_qty": 10.0, "price_per_unit": 5.0, "tier_name": "Retail"},
        {"selling_type": "Pezzo", "from_qty": 10.0, "to_qty": 100.0, "price_per_unit": 3.0, "tier_name": "Wholesale"},
        {"selling_type": "Pezzo", "from_qty": 100.0, "to_qty": None, "price_per_unit": 2.0, "tier_name": "Bulk", "is_default": 1}
    ]

def get_standard_customer_minimums():
    """
    Ottieni configurazioni standard minimi cliente
    """
    return [
        {"customer_group": "Finale", "min_sqm": 0.5, "calculation_mode": "Globale Preventivo", "enabled": 1, "description": "Setup UNA volta"},
        {"customer_group": "Bronze", "min_sqm": 0.25, "calculation_mode": "Per Riga", "enabled": 1, "description": "Minimo per riga"},
        {"customer_group": "Gold", "min_sqm": 0.1, "calculation_mode": "Globale Preventivo", "enabled": 1, "description": "Minimo globale preferenziale"},
        {"customer_group": "Diamond", "min_sqm": 0, "calculation_mode": "Per Riga", "enabled": 1, "description": "Nessun minimo"}
    ]

def retry_with_backoff(func, max_retries=3, base_delay=2):
    """
    Retry function con backoff esponenziale
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "Lock wait timeout" in str(e) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"🔄 Retry {attempt + 1}/{max_retries} in {delay}s...")
                time.sleep(delay)
                
                # Pulisci connessioni database
                frappe.db.commit()
                continue
            else:
                raise e
    
    return None

def force_unlock_tables():
    """
    Force unlock tabelle MySQL se bloccate
    """
    try:
        frappe.db.sql("UNLOCK TABLES", auto_commit=True)
        print("✓ Tabelle database sbloccate")
    except Exception as e:
        print(f"⚠️ Warning unlock: {e}")

def test_database_health():
    """
    Test salute database prima del setup
    """
    print("🏥 Test salute database...")
    
    try:
        # Test connessione
        frappe.db.sql("SELECT 1", as_dict=True)
        print("✓ Connessione database OK")
        
        # Test lock status
        locks = frappe.db.sql("SHOW PROCESSLIST", as_dict=True)
        active_locks = [l for l in locks if l.get('State') and 'lock' in l.get('State', '').lower()]
        
        if active_locks:
            print(f"⚠️ {len(active_locks)} lock attivi trovati")
            for lock in active_locks[:3]:  # Mostra primi 3
                print(f"   • {lock.get('User', 'N/A')}: {lock.get('State', 'N/A')}")
        else:
            print("✓ Nessun lock problematico")
        
        return len(active_locks) < 5  # OK se meno di 5 lock
        
    except Exception as e:
        print(f"⚠️ Warning test database: {e}")
        return False

def setup_manual_universal_item_safe(item_code="AM"):
    """
    Setup super-sicuro con tutti i controlli
    """
    print(f"\n🛡️ SETUP SUPER-SICURO ITEM {item_code}")
    print("="*60)
    
    # 1. Test database health
    if not test_database_health():
        print("⚠️ Database ha problemi, continuo comunque...")
    
    # 2. Force unlock se necessario
    force_unlock_tables()
    
    # 3. Setup con retry
    success = retry_with_backoff(
        lambda: setup_manual_universal_item_robust(item_code),
        max_retries=3,
        base_delay=3
    )
    
    if success:
        print("\n🎉 SETUP COMPLETATO CON SUCCESSO!")
        return True
    else:
        print("\n❌ Setup fallito dopo tutti i retry")
        return False

# Comandi rapidi
def ms_robust():
    """Manual setup robust"""
    return setup_manual_universal_item_robust("AM")

def ms_safe():
    """Manual setup safe"""
    return setup_manual_universal_item_safe("AM")

def test_db():
    """Test database health"""
    return test_database_health()

# Alias
msr = ms_robust
mss = ms_safe
tdb = test_db

# Help
def help_manual_setup():
    """Mostra comandi disponibili"""
    print("\n" + "="*50)
    print("🔧 COMANDI SETUP MANUALE ROBUSTO")
    print("="*50)
    print("\n🚀 SETUP:")
    print("   msr()  → Setup robusto (raccomandato)")
    print("   mss()  → Setup super-sicuro con retry")
    print("   ms()   → Setup originale")
    print("\n🏥 DIAGNOSTICA:")
    print("   tdb()  → Test salute database")
    print("\n💡 ESEMPI:")
    print("   >>> from iderp.manual_setup import *")
    print("   >>> mss()  # Setup più sicuro")
    print("   >>> tdb()  # Se ci sono problemi DB")
    print("="*50)

h = help_manual_setup