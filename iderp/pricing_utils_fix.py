# iderp/pricing_utils_fix.py
"""
FIX: Validazione Scaglioni Prezzo Corretta
Risolve l'errore di "sovrapposizione" per scaglioni contigui validi
"""

import frappe
from frappe import _

def validate_pricing_tiers_fixed(doc, method=None):
    """
    Valida scaglioni prezzo CORRETTO - scaglioni contigui sono validi
    """
    if not getattr(doc, 'supports_custom_measurement', 0):
        return
    
    if not hasattr(doc, 'pricing_tiers') or not doc.pricing_tiers:
        return
    
    errors = []
    warnings = []
    
    # Ordina per from_sqm per validazione
    tiers = sorted(doc.pricing_tiers, key=lambda x: x.from_sqm)
    
    for i, tier in enumerate(tiers):
        row_num = i + 1
        
        # 1. Validazioni base singolo scaglione
        if tier.from_sqm < 0:
            errors.append(f"Riga {row_num}: 'Da m²' non può essere negativo")
        
        if tier.to_sqm is not None and tier.to_sqm < 0:
            errors.append(f"Riga {row_num}: 'A m²' non può essere negativo")
        
        if tier.to_sqm and tier.from_sqm >= tier.to_sqm:
            errors.append(f"Riga {row_num}: 'A m²' ({tier.to_sqm}) deve essere maggiore di 'Da m²' ({tier.from_sqm})")
        
        if tier.price_per_sqm <= 0:
            errors.append(f"Riga {row_num}: 'Prezzo €/m²' deve essere maggiore di 0")
        
        # 2. Validazioni sovrapposizioni CORRETTE
        if i > 0:
            prev_tier = tiers[i-1]
            
            # VERA sovrapposizione: il nuovo inizia PRIMA che finisca il precedente
            if prev_tier.to_sqm and tier.from_sqm < prev_tier.to_sqm:
                errors.append(
                    f"Riga {row_num}: VERA sovrapposizione - inizia a {tier.from_sqm} m² "
                    f"ma il precedente finisce a {prev_tier.to_sqm} m²"
                )
            
            # Gap tra scaglioni (warning, non errore)
            elif prev_tier.to_sqm and tier.from_sqm > prev_tier.to_sqm:
                gap_size = tier.from_sqm - prev_tier.to_sqm
                warnings.append(
                    f"Riga {row_num}: Gap di {gap_size} m² tra {prev_tier.to_sqm} e {tier.from_sqm} m² "
                    f"(ordini in questo range useranno scaglione precedente)"
                )
            
            # Scaglioni contigui (OK, nessun errore)
            elif prev_tier.to_sqm and tier.from_sqm == prev_tier.to_sqm:
                # Questo è corretto! Scaglioni contigui
                pass
        
        # 3. Validazioni logiche aggiuntive
        if tier.to_sqm is None and i < len(tiers) - 1:
            warnings.append(
                f"Riga {row_num}: Scaglione 'illimitato' (senza 'A m²') non è l'ultimo. "
                f"Gli scaglioni successivi potrebbero non essere mai usati."
            )
    
    # 4. Validazioni globali
    if len(tiers) > 1:
        # Verifica che il primo scaglione inizi da 0
        if tiers[0].from_sqm > 0:
            warnings.append(
                f"Il primo scaglione inizia da {tiers[0].from_sqm} m². "
                f"Ordini sotto questa soglia potrebbero non avere prezzo."
            )
        
        # Verifica almeno uno scaglione default o illimitato
        has_unlimited = any(tier.to_sqm is None for tier in tiers)
        has_default = any(getattr(tier, 'is_default', False) for tier in tiers)
        
        if not has_unlimited and not has_default:
            warnings.append(
                "Nessuno scaglione 'illimitato' o 'default' configurato. "
                "Ordini sopra l'ultimo scaglione potrebbero non avere prezzo."
            )
    
    # 5. Mostra risultati
    if errors:
        error_message = "❌ ERRORI negli scaglioni prezzo:\n" + "\n".join(errors)
        if warnings:
            error_message += "\n\n⚠️ AVVISI:\n" + "\n".join(warnings)
        frappe.throw(_(error_message))
    
    elif warnings:
        # Solo avvisi, non bloccare il salvataggio
        warning_message = "⚠️ AVVISI scaglioni prezzo:\n" + "\n".join(warnings)
        frappe.msgprint(_(warning_message), title="Configurazione Scaglioni", indicator="orange")

def patch_pricing_tiers_validation():
    """
    Applica il fix alla validazione esistente
    """
    print("[iderp] Applicando fix validazione scaglioni prezzo...")
    
    try:
        # Sostituisce la funzione nel modulo esistente
        import iderp.pricing_utils
        
        # Backup della funzione originale
        iderp.pricing_utils.validate_pricing_tiers_original = iderp.pricing_utils.validate_pricing_tiers
        
        # Sostituisce con la versione corretta
        iderp.pricing_utils.validate_pricing_tiers = validate_pricing_tiers_fixed
        
        print("[iderp] ✅ Fix validazione scaglioni applicato")
        print("[iderp] 💡 Ora scaglioni contigui sono considerati validi")
        
        return True
        
    except Exception as e:
        print(f"[iderp] ❌ Errore applicazione fix: {e}")
        return False

def test_pricing_tiers_validation():
    """
    Test della nuova validazione con esempi pratici
    """
    print("[iderp] 🧪 Test validazione scaglioni...")
    
    # Simula oggetto Item con scaglioni
    class MockItem:
        def __init__(self):
            self.supports_custom_measurement = 1
            self.pricing_tiers = []
    
    # Test 1: Scaglioni contigui validi
    print("\nTest 1: Scaglioni contigui (dovrebbero essere VALIDI)")
    item1 = MockItem()
    item1.pricing_tiers = [
        type('Tier', (), {
            'from_sqm': 0, 'to_sqm': 1, 'price_per_sqm': 20, 'tier_name': 'Piccolo'
        })(),
        type('Tier', (), {
            'from_sqm': 1, 'to_sqm': 5, 'price_per_sqm': 15, 'tier_name': 'Medio'
        })(),
        type('Tier', (), {
            'from_sqm': 5, 'to_sqm': None, 'price_per_sqm': 10, 'tier_name': 'Grande'
        })()
    ]
    
    try:
        validate_pricing_tiers_fixed(item1)
        print("   ✅ Scaglioni contigui: VALIDAZIONE OK")
    except Exception as e:
        print(f"   ❌ Scaglioni contigui: {e}")
    
    # Test 2: Vera sovrapposizione (deve fallire)
    print("\nTest 2: Vera sovrapposizione (dovrebbe FALLIRE)")
    item2 = MockItem()
    item2.pricing_tiers = [
        type('Tier', (), {
            'from_sqm': 0, 'to_sqm': 2, 'price_per_sqm': 20, 'tier_name': 'Primo'
        })(),
        type('Tier', (), {
            'from_sqm': 1, 'to_sqm': 5, 'price_per_sqm': 15, 'tier_name': 'Secondo (overlap!)'
        })()
    ]
    
    try:
        validate_pricing_tiers_fixed(item2)
        print("   ❌ Sovrapposizione: DOVEVA fallire ma è passata!")
    except Exception as e:
        print("   ✅ Sovrapposizione: correttamente rilevata")
    
    # Test 3: Gap tra scaglioni (warning)
    print("\nTest 3: Gap tra scaglioni (dovrebbe dare WARNING)")
    item3 = MockItem()
    item3.pricing_tiers = [
        type('Tier', (), {
            'from_sqm': 0, 'to_sqm': 1, 'price_per_sqm': 20, 'tier_name': 'Primo'
        })(),
        type('Tier', (), {
            'from_sqm': 3, 'to_sqm': 5, 'price_per_sqm': 15, 'tier_name': 'Secondo (gap!)'
        })()
    ]
    
    try:
        validate_pricing_tiers_fixed(item3)
        print("   ✅ Gap: validazione con warning OK")
    except Exception as e:
        print(f"   ⚠️ Gap: {e}")
    
    print("\n✅ Test validazione completati")

def show_correct_pricing_tier_examples():
    """Mostra esempi di configurazioni corrette"""
    print("\n" + "="*60)
    print("📋 ESEMPI CONFIGURAZIONI SCAGLIONI CORRETTE")
    print("="*60)
    
    print("\n✅ CONFIGURAZIONE TIPO 1: Scaglioni Contigui")
    print("Da m²  | A m²  | €/m² | Nome")
    print("-------|-------|------|------------------")
    print("0      | 0.5   | 25   | Micro (biglietti)")
    print("0.5    | 2     | 18   | Piccolo (A4)")  
    print("2      | 10    | 12   | Medio (poster)")
    print("10     | (vuoto)| 8   | Grande (illimitato)")
    
    print("\n✅ CONFIGURAZIONE TIPO 2: Con Gap (warning ma valido)")
    print("Da m²  | A m²  | €/m² | Nome")
    print("-------|-------|------|------------------")
    print("0      | 1     | 20   | Piccolo")
    print("2      | 5     | 15   | Medio (gap 1-2 m²)")
    print("5      | (vuoto)| 10   | Grande")
    
    print("\n❌ CONFIGURAZIONI ERRATE:")
    print("\n❌ TIPO 1: Vera Sovrapposizione")
    print("0 - 2 m² = €20")
    print("1 - 5 m² = €15  ← ERRORE! Inizia prima che finisca il precedente")
    
    print("\n❌ TIPO 2: 'A m²' minore di 'Da m²'")
    print("5 - 3 m² = €10  ← ERRORE! 5 > 3")
    
    print("\n❌ TIPO 3: Prezzi negativi/zero")
    print("0 - 1 m² = €0   ← ERRORE! Prezzo deve essere > 0")
    
    print("\n💡 CONSIGLI:")
    print("• Inizia sempre da 0 m²")
    print("• Usa scaglioni contigui (fine precedente = inizio successivo)")
    print("• Ultimo scaglione senza 'A m²' per illimitato")
    print("• Prezzi decrescenti per incentivare quantità maggiori")
    print("="*60)

def apply_pricing_tiers_fix():
    """Applica il fix completo per gli scaglioni prezzo"""
    print("\n" + "="*60)
    print("🔧 APPLICAZIONE FIX SCAGLIONI PREZZO")
    print("="*60)
    
    # 1. Applica patch
    if patch_pricing_tiers_validation():
        
        # 2. Test validazione
        test_pricing_tiers_validation()
        
        # 3. Mostra esempi
        show_correct_pricing_tier_examples()
        
        print("\n✅ FIX SCAGLIONI PREZZO COMPLETATO!")
        print("💡 Ora puoi configurare scaglioni contigui senza errori")
        print("🧪 Prova a salvare un Item con scaglioni contigui")
        
        return True
    else:
        print("\n❌ Fix fallito")
        return False

# Comandi rapidi
def pricing_fix():
    """Comando rapido: applica fix"""
    return apply_pricing_tiers_fix()

def pricing_examples():
    """Comando rapido: mostra esempi"""
    show_correct_pricing_tier_examples()

def pricing_test():
    """Comando rapido: test validazione"""
    test_pricing_tiers_validation()

# Alias
pf = pricing_fix
pe = pricing_examples  
pt = pricing_test
