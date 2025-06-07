# iderp/copy_fields.py
"""
Sistema di copia campi e calcolo automatico prezzi
ERPNext 15 Compatible - Integrato con sistema universale
"""

import frappe
from frappe import _

def copy_custom_fields(doc, method=None):
    """
    Copia i campi custom tra documenti e applica calcoli automatici
    ERPNext 15 Compatible - Supporta tutti i tipi vendita
    """
    if not hasattr(doc, "items"):
        return
    
    try:
        frappe.logger().info(f"[iderp] copy_custom_fields attivato per {doc.doctype}: {doc.name}")
        
        # Processa ogni item
        for item in doc.items:
            try:
                # 1. Copia campi da documento precedente se collegato
                copy_fields_from_previous_document(item)
                
                # 2. Applica calcoli automatici universali
                apply_universal_calculations(doc, item)
                
            except Exception as e:
                frappe.logger().error(f"[iderp] Errore processing item {item.item_code}: {str(e)}")
                continue
        
        frappe.logger().info(f"[iderp] copy_custom_fields completato per {doc.name}")
        
    except Exception as e:
        frappe.logger().error(f"[iderp] Errore copy_custom_fields: {str(e)}")

def copy_fields_from_previous_document(item):
    """
    Copia campi custom da documento precedente se collegato
    """
    # Lista completa dei campi da copiare
    fields_to_copy = [
        # Tipo vendita e configurazione
        "tipo_vendita",
        
        # Metro Quadrato
        "base", "altezza", "mq_singolo", "mq_calcolati", "prezzo_mq",
        
        # Metro Lineare  
        "larghezza_materiale", "lunghezza", "ml_calcolati", "prezzo_ml",
        
        # Pezzo
        "pz_totali",
        
        # Note e controlli
        "note_calcolo", "auto_calculated", "manual_rate_override", "price_locked"
    ]
    
    try:
        # Verifica se ha riferimento a documento precedente
        linked_doc_type = getattr(item, "linked_document_type", None)
        linked_doc_name = getattr(item, "linked_document_name", None)
        
        if not linked_doc_type or not linked_doc_name:
            return
        
        if not frappe.db.exists(linked_doc_type, linked_doc_name):
            return
        
        # Carica documento precedente
        prev_doc = frappe.get_doc(linked_doc_type, linked_doc_name)
        
        # Trova item corrispondente nel documento precedente
        prev_item = None
        if hasattr(prev_doc, 'items') and prev_doc.items:
            for pi in prev_doc.items:
                if pi.item_code == item.item_code:
                    prev_item = pi
                    break
        
        if not prev_item:
            return
        
        # Copia campi disponibili
        copied_count = 0
        for field in fields_to_copy:
            if hasattr(prev_item, field) and hasattr(item, field):
                prev_value = getattr(prev_item, field, None)
                if prev_value is not None:
                    setattr(item, field, prev_value)
                    copied_count += 1
        
        if copied_count > 0:
            frappe.logger().info(f"[iderp] Copiati {copied_count} campi da {linked_doc_type} per {item.item_code}")
            
    except Exception as e:
        frappe.logger().error(f"[iderp] Errore copia campi: {str(e)}")

def apply_universal_calculations(doc, item):
    """
    Applica calcoli automatici universali per tutti i tipi vendita
    """
    try:
        # Skip se prezzo è bloccato manualmente
        if getattr(item, 'price_locked', 0):
            frappe.logger().info(f"[iderp] Skip calcolo {item.item_code} - prezzo bloccato")
            return
        
        # Skip se già calcolato automaticamente per evitare loop
        if getattr(item, 'auto_calculated', 0) and not getattr(item, 'manual_rate_override', 0):
            return
        
        tipo_vendita = getattr(item, 'tipo_vendita', 'Pezzo')
        
        if not item.item_code:
            return
        
        # Calcola quantità base per tipo
        qty_info = calculate_item_quantities(item, tipo_vendita)
        if not qty_info:
            return
        
        # Aggiorna campi calcolati
        update_calculated_fields(item, qty_info, tipo_vendita)
        
        # Calcola prezzo se ha senso farlo
        if should_calculate_price(doc, item, qty_info):
            calculate_item_price_server_side(doc, item, tipo_vendita, qty_info)
        
    except Exception as e:
        frappe.logger().error(f"[iderp] Errore calcolo universale: {str(e)}")

def calculate_item_quantities(item, tipo_vendita):
    """
    Calcola quantità per tutti i tipi vendita
    """
    try:
        qty = float(getattr(item, 'qty', 1) or 1)
        
        if tipo_vendita == "Metro Quadrato":
            base = float(getattr(item, 'base', 0) or 0)
            altezza = float(getattr(item, 'altezza', 0) or 0)
            
            if not base or not altezza:
                return None
            
            mq_singolo = (base * altezza) / 10000
            mq_totali = mq_singolo * qty
            
            return {
                'type': 'Metro Quadrato',
                'unit_qty': mq_singolo,
                'total_qty': mq_totali,
                'qty_label': 'm²',
                'dimensions': f"{base}×{altezza}cm"
            }
            
        elif tipo_vendita == "Metro Lineare":
            lunghezza = float(getattr(item, 'lunghezza', 0) or 0)
            
            if not lunghezza:
                return None
            
            ml_singolo = lunghezza / 100  # da cm a metri
            ml_totali = ml_singolo * qty
            
            return {
                'type': 'Metro Lineare',
                'unit_qty': ml_singolo,
                'total_qty': ml_totali,
                'qty_label': 'ml',
                'dimensions': f"{lunghezza}cm"
            }
            
        elif tipo_vendita == "Pezzo":
            return {
                'type': 'Pezzo',
                'unit_qty': 1,
                'total_qty': qty,
                'qty_label': 'pz',
                'dimensions': f"{qty} pezzi"
            }
        
        return None
        
    except Exception as e:
        frappe.logger().error(f"[iderp] Errore calcolo quantità: {str(e)}")
        return None

def update_calculated_fields(item, qty_info, tipo_vendita):
    """
    Aggiorna campi calcolati in base al tipo vendita
    """
    try:
        if tipo_vendita == "Metro Quadrato":
            item.mq_singolo = round(qty_info['unit_qty'], 4)
            item.mq_calcolati = round(qty_info['total_qty'], 3)
            
        elif tipo_vendita == "Metro Lineare":
            item.ml_calcolati = round(qty_info['total_qty'], 2)
            
        elif tipo_vendita == "Pezzo":
            item.pz_totali = int(qty_info['total_qty'])
        
        frappe.logger().debug(f"[iderp] Campi aggiornati per {tipo_vendita}: {qty_info['total_qty']:.3f} {qty_info['qty_label']}")
        
    except Exception as e:
        frappe.logger().error(f"[iderp] Errore update campi: {str(e)}")

def should_calculate_price(doc, item, qty_info):
    """
    Determina se dovrebbe calcolare il prezzo automaticamente
    """
    try:
        # Non calcolare se non ci sono quantità valide
        if not qty_info or qty_info['total_qty'] <= 0:
            return False
        
        # Non calcolare se manca il cliente (per documenti che lo richiedono)
        customer = getattr(doc, 'customer', None) or getattr(doc, 'party_name', None)
        if not customer and doc.doctype in ['Quotation', 'Sales Order', 'Sales Invoice']:
            return False
        
        # Non calcolare se l'item non supporta misure personalizzate
        if not item_supports_custom_measurement(item.item_code):
            return False
        
        # Non calcolare se prezzo già inserito manualmente e non modificato
        if (getattr(item, 'manual_rate_override', 0) and 
            not getattr(item, 'auto_calculated', 0) and 
            float(getattr(item, 'rate', 0) or 0) > 0):
            return False
        
        return True
        
    except Exception as e:
        frappe.logger().error(f"[iderp] Errore should_calculate_price: {str(e)}")
        return False

def calculate_item_price_server_side(doc, item, tipo_vendita, qty_info):
    """
    Calcola prezzo server-side usando sistema universale
    """
    try:
        customer = getattr(doc, 'customer', None) or getattr(doc, 'party_name', None)
        
        # Usa il sistema pricing utils per calcolo
        from iderp_module.pricing_utils import get_customer_specific_pricing_for_type, get_item_pricing_for_type
        
        if customer:
            pricing_info = get_customer_specific_pricing_for_type(
                customer, item.item_code, tipo_vendita, qty_info['total_qty']
            )
        else:
            pricing_info = get_item_pricing_for_type(
                item.item_code, tipo_vendita, qty_info['total_qty']
            )
        
        if not pricing_info:
            # Nessun prezzo trovato
            item.note_calcolo = f"📊 {qty_info['dimensions']}\n⚠️ Nessuno scaglione configurato per {tipo_vendita}"
            return
        
        # Calcola rate
        price_per_unit = pricing_info["price_per_unit"]
        rate_unitario = qty_info['unit_qty'] * price_per_unit
        
        # Applica minimi se configurati
        if pricing_info.get("min_applied"):
            effective_qty = pricing_info.get("effective_qty", qty_info['total_qty'])
            rate_unitario = (effective_qty / float(item.qty or 1)) * price_per_unit
        
        # Aggiorna item
        item.rate = round(rate_unitario, 2)
        item.amount = round(rate_unitario * float(item.qty or 1), 2)
        
        # Aggiorna prezzo specifico per tipo
        if tipo_vendita == "Metro Quadrato":
            item.prezzo_mq = price_per_unit
        elif tipo_vendita == "Metro Lineare":
            item.prezzo_ml = price_per_unit
        
        # Flags di controllo
        item.auto_calculated = 1
        item.manual_rate_override = 0
        item.price_locked = 0
        
        # Note dettagliate
        item.note_calcolo = build_server_calculation_notes(
            tipo_vendita, qty_info, pricing_info, price_per_unit, rate_unitario, customer
        )
        
        frappe.logger().info(f"[iderp] Prezzo calcolato server-side: {item.item_code} = €{rate_unitario:.2f}")
        
    except Exception as e:
        frappe.logger().error(f"[iderp] Errore calcolo prezzo server-side: {str(e)}")
        item.note_calcolo = f"📊 {qty_info.get('dimensions', '')}\n❌ Errore calcolo prezzo: {str(e)}"

def build_server_calculation_notes(tipo_vendita, qty_info, pricing_info, price_per_unit, rate_unitario, customer):
    """
    Costruisce note dettagliate per calcolo server-side
    """
    note_parts = [
        f"🖥️ CALCOLO SERVER-SIDE",
        f"🎯 Tipo: {tipo_vendita}",
        f"📊 Scaglione: {pricing_info.get('tier_name', 'Standard')}"
    ]
    
    # Dettagli misure
    if qty_info.get('dimensions'):
        note_parts.append(f"📐 Misure: {qty_info['dimensions']}")
    
    note_parts.append(f"📏 Quantità: {qty_info['total_qty']:.3f} {qty_info['qty_label']}")
    
    # Minimi applicati
    if pricing_info.get("min_applied"):
        note_parts.extend([
            f"⚠️ MINIMO {pricing_info.get('customer_group', '')}: {pricing_info.get('min_qty', 0)} {qty_info['qty_label']}",
            f"📈 Quantità effettiva: {pricing_info.get('effective_qty', qty_info['total_qty']):.3f} {qty_info['qty_label']}"
        ])
    
    # Cliente
    if customer:
        note_parts.append(f"👤 Cliente: {customer}")
        if pricing_info.get('customer_group'):
            note_parts.append(f"🏷️ Gruppo: {pricing_info['customer_group']}")
    
    # Prezzo e calcolo
    note_parts.extend([
        f"💰 Prezzo: €{price_per_unit}/{qty_info['qty_label'].rstrip('z')}",
        f"💵 Rate unitario: €{rate_unitario:.2f}"
    ])
    
    # Timestamp
    note_parts.append(f"🕒 Calcolato: {frappe.utils.now()}")
    
    return "\n".join(note_parts)

def item_supports_custom_measurement(item_code):
    """
    Verifica se un item supporta misure personalizzate
    """
    try:
        return bool(frappe.db.get_value("Item", item_code, "supports_custom_measurement"))
    except:
        return False

# ================================
# FUNZIONI LEGACY PER COMPATIBILITÀ
# ================================

def recalculate_item_price(item):
    """
    Funzione legacy per compatibilità - ora usa sistema universale
    """
    try:
        tipo_vendita = getattr(item, "tipo_vendita", "Metro Quadrato")
        
        if tipo_vendita == "Metro Quadrato":
            calculate_square_meter_price(item)
        elif tipo_vendita == "Metro Lineare":
            calculate_linear_meter_price(item)
        elif tipo_vendita == "Pezzo":
            calculate_piece_price(item)
            
    except Exception as e:
        frappe.logger().error(f"[iderp Legacy] Errore ricalcolo prezzo: {str(e)}")

def calculate_square_meter_price(item):
    """Calcola prezzo per vendita al metro quadrato - Legacy"""
    try:
        base = float(getattr(item, "base", 0) or 0)
        altezza = float(getattr(item, "altezza", 0) or 0)
        prezzo_mq = float(getattr(item, "prezzo_mq", 0) or 0)
        qty = float(getattr(item, "qty", 1) or 1)
        
        if not base or not altezza:
            item.mq_singolo = 0
            item.mq_calcolati = 0
            item.note_calcolo = "Inserire base e altezza"
            return
        
        # Calcola m²
        mq_singolo = (base * altezza) / 10000
        mq_totali = mq_singolo * qty
        
        item.mq_singolo = round(mq_singolo, 4)
        item.mq_calcolati = round(mq_totali, 3)
        
        if prezzo_mq > 0:
            calculated_rate = mq_singolo * prezzo_mq
            item.rate = round(calculated_rate, 2)
            
            item.note_calcolo = (
                f"📐 Dimensioni: {base}×{altezza}cm\n"
                f"🔢 m² singolo: {mq_singolo:.4f} m²\n" 
                f"💰 Prezzo: €{prezzo_mq}/m²\n"
                f"💵 Prezzo unitario: €{calculated_rate:.2f}\n"
                f"📦 Quantità: {qty} pz\n"
                f"📊 m² totali: {mq_totali:.3f} m²\n"
                f"💸 Totale riga: €{calculated_rate * qty:.2f}\n"
                f"🏷️ Calcolo legacy"
            )
        else:
            item.note_calcolo = f"{mq_totali:.3f} m² (manca prezzo al m²)"
            
    except Exception as e:
        frappe.logger().error(f"[iderp Legacy] Errore calcolo m²: {str(e)}")

def calculate_linear_meter_price(item):
    """Calcola prezzo per vendita al metro lineare - Legacy"""
    try:
        lunghezza = float(getattr(item, "lunghezza", 0) or 0)
        prezzo_ml = float(getattr(item, "prezzo_ml", 0) or 0)
        larghezza_materiale = float(getattr(item, "larghezza_materiale", 0) or 0)
        qty = float(getattr(item, "qty", 1) or 1)
        
        if not lunghezza:
            item.ml_calcolati = 0
            item.note_calcolo = "Inserire lunghezza"
            return
        
        # Calcola metri lineari
        ml_singolo = lunghezza / 100
        ml_totali = ml_singolo * qty
        
        item.ml_calcolati = round(ml_totali, 2)
        
        if prezzo_ml > 0:
            calculated_rate = ml_singolo * prezzo_ml
            item.rate = round(calculated_rate, 2)
            
            note = f"📏 Lunghezza: {lunghezza}cm\n💰 Prezzo: €{prezzo_ml}/ml"
            if larghezza_materiale:
                note += f"\n📐 Larghezza materiale: {larghezza_materiale}cm"
            note += f"\n💵 Prezzo unitario: €{calculated_rate:.2f}\n🏷️ Calcolo legacy"
            
            item.note_calcolo = note
        else:
            item.note_calcolo = f"{ml_totali:.2f} ml (manca prezzo al ml)"
            
    except Exception as e:
        frappe.logger().error(f"[iderp Legacy] Errore calcolo ml: {str(e)}")

def calculate_piece_price(item):
    """Gestisce vendita al pezzo - Legacy"""
    try:
        rate = float(getattr(item, "rate", 0) or 0)
        qty = float(getattr(item, "qty", 1) or 1)
        
        item.pz_totali = int(qty)
        
        if rate and qty:
            totale = rate * qty
            item.note_calcolo = f"📦 {qty} pz × €{rate} = €{totale:.2f}\n🏷️ Calcolo legacy"
        else:
            item.note_calcolo = "Vendita al pezzo - inserire prezzo unitario"
            
    except Exception as e:
        frappe.logger().error(f"[iderp Legacy] Errore calcolo pezzi: {str(e)}")

# ================================
# FUNZIONI UTILITY
# ================================

def get_square_meters(base_cm, altezza_cm):
    """Calcola metri quadrati da misure in cm"""
    try:
        return (float(base_cm) * float(altezza_cm)) / 10000
    except:
        return 0

def get_linear_meters(lunghezza_cm):
    """Calcola metri lineari da misure in cm"""
    try:
        return float(lunghezza_cm) / 100
    except:
        return 0

def validate_measurements(item):
    """Valida che le misure siano corrette per il tipo di vendita"""
    try:
        tipo_vendita = getattr(item, "tipo_vendita", "Pezzo")
        
        if tipo_vendita == "Metro Quadrato":
            base = getattr(item, "base", 0)
            altezza = getattr(item, "altezza", 0)
            if not base or not altezza:
                frappe.throw("Per vendita al metro quadrato sono richiesti Base e Altezza")
        
        elif tipo_vendita == "Metro Lineare":
            lunghezza = getattr(item, "lunghezza", 0)
            if not lunghezza:
                frappe.throw("Per vendita al metro lineare è richiesta la Lunghezza")
                
    except Exception as e:
        frappe.logger().error(f"[iderp] Errore validazione misure: {str(e)}")

# ================================
# DEBUG E TESTING
# ================================

def test_copy_fields_system():
    """
    Test del sistema copy_fields per debugging
    """
    print("\n🧪 TEST SISTEMA COPY_FIELDS")
    print("="*50)
    
    try:
        # Simula un documento con item
        class MockDoc:
            def __init__(self):
                self.doctype = "Quotation"
                self.name = "TEST-001"
                self.customer = "Cliente Test"
                self.items = []
        
        class MockItem:
            def __init__(self):
                self.item_code = "TEST-ITEM"
                self.tipo_vendita = "Metro Quadrato"
                self.base = 30
                self.altezza = 40
                self.qty = 1
                self.rate = 0
                self.amount = 0
        
        doc = MockDoc()
        item = MockItem()
        doc.items = [item]
        
        print("📋 Item di test creato")
        print(f"   • {item.item_code}: {item.tipo_vendita}")
        print(f"   • Dimensioni: {item.base}×{item.altezza}cm")
        
        # Test calcolo quantità
        qty_info = calculate_item_quantities(item, item.tipo_vendita)
        print(f"📊 Quantità calcolate: {qty_info}")
        
        # Test aggiornamento campi
        if qty_info:
            update_calculated_fields(item, qty_info, item.tipo_vendita)
            print(f"📏 m² calcolati: {item.mq_calcolati}")
        
        # Test copy_fields completo
        copy_custom_fields(doc)
        print("✅ Test copy_fields completato")
        
        if hasattr(item, 'note_calcolo') and item.note_calcolo:
            print(f"📝 Note: {item.note_calcolo[:100]}...")
        
    except Exception as e:
        print(f"❌ Errore test: {e}")

def get_copy_fields_status():
    """
    Ritorna stato del sistema copy_fields
    """
    try:
        # Verifica funzioni principali
        functions_available = {
            "copy_custom_fields": callable(copy_custom_fields),
            "apply_universal_calculations": callable(apply_universal_calculations),
            "calculate_item_quantities": callable(calculate_item_quantities),
            "calculate_item_price_server_side": callable(calculate_item_price_server_side)
        }
        
        # Verifica moduli dipendenti
        try:
            from iderp_module.pricing_utils import get_customer_specific_pricing_for_type
            pricing_utils_available = True
        except ImportError:
            pricing_utils_available = False
        
        return {
            "functions_available": functions_available,
            "pricing_utils_available": pricing_utils_available,
            "system_ready": all(functions_available.values()) and pricing_utils_available
        }
        
    except Exception as e:
        return {"error": str(e)}

# Comandi rapidi per debugging
def test_cf():
    """Test rapido copy_fields"""
    test_copy_fields_system()

def status_cf():
    """Status copy_fields"""
    return get_copy_fields_status()

# Alias
tcf = test_cf
scf = status_cf
