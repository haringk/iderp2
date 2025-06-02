# iderp/pricing_utils.py
"""
Utility functions per gestione scaglioni prezzo
FIXED: Import circolari e funzioni mancanti
"""

import frappe
from frappe import _

@frappe.whitelist()
def get_item_pricing_tiers(item_code):
    """
    API per ottenere scaglioni prezzo di un item (chiamata da JavaScript)
    """
    try:
        if not frappe.db.exists("Item", item_code):
            return {"error": "Item non trovato"}
        
        item_doc = frappe.get_doc("Item", item_code)
        
        # Verifica se supporta misure personalizzate
        if not getattr(item_doc, 'supports_custom_measurement', 0):
            return {"error": "Item non supporta misure personalizzate"}
        
        if not hasattr(item_doc, 'pricing_tiers') or not item_doc.pricing_tiers:
            return {"tiers": [], "message": "Nessuno scaglione configurato"}
        
        tiers = []
        for tier in item_doc.pricing_tiers:
            tiers.append({
                "from_sqm": tier.from_sqm,
                "to_sqm": tier.to_sqm,
                "price_per_sqm": tier.price_per_sqm,
                "tier_name": tier.tier_name or "",
                "is_default": tier.is_default or 0
            })
        
        # Ordina per from_sqm
        tiers.sort(key=lambda x: x["from_sqm"])
        
        return {
            "tiers": tiers,
            "item_code": item_code,
            "supports_tiers": True
        }
        
    except Exception as e:
        frappe.log_error(f"Errore get_item_pricing_tiers per {item_code}: {str(e)}")
        return {"error": f"Errore caricamento scaglioni: {str(e)}"}

def get_price_for_sqm(item_code, total_sqm):
    """
    Ottieni prezzo per m² in base agli scaglioni di un item
    """
    try:
        result = get_item_pricing_tiers(item_code)
        
        if "error" in result:
            return None
        
        tiers = result.get("tiers", [])
        if not tiers:
            return None
        
        # Cerca scaglione appropriato
        for tier in tiers:
            if total_sqm >= tier["from_sqm"]:
                # Se to_sqm è None, significa "oltre X m²"
                if not tier["to_sqm"] or total_sqm <= tier["to_sqm"]:
                    return {
                        "price_per_sqm": tier["price_per_sqm"],
                        "tier_name": tier["tier_name"],
                        "from_sqm": tier["from_sqm"],
                        "to_sqm": tier["to_sqm"]
                    }
        
        # Se non trova scaglione, cerca prezzo default
        for tier in tiers:
            if tier["is_default"]:
                return {
                    "price_per_sqm": tier["price_per_sqm"],
                    "tier_name": tier["tier_name"] + " (Default)",
                    "from_sqm": tier["from_sqm"],
                    "to_sqm": tier["to_sqm"]
                }
        
        return None
        
    except Exception as e:
        frappe.log_error(f"Errore get_price_for_sqm: {str(e)}")
        return None

def get_customer_specific_price_for_sqm(customer, item_code, total_sqm):
    """
    Ottieni prezzo per m² considerando il gruppo cliente e i minimi
    """
    if not customer:
        # Se non c'è cliente, usa prezzi standard
        return get_price_for_sqm(item_code, total_sqm)
    
    try:
        # Ottieni gruppo cliente
        customer_group = frappe.db.get_value("Customer", customer, "customer_group")
        if not customer_group:
            return get_price_for_sqm(item_code, total_sqm)
        
        print(f"[PRICING] Cliente: {customer}, Gruppo: {customer_group}, m²: {total_sqm}")
        
        # Cerca minimi nella configurazione dell'item
        item_doc = frappe.get_doc("Item", item_code)
        minimum_applied = False
        effective_sqm = total_sqm
        min_sqm = 0
        
        if hasattr(item_doc, 'customer_group_minimums') and item_doc.customer_group_minimums:
            for min_rule in item_doc.customer_group_minimums:
                if min_rule.customer_group == customer_group and min_rule.enabled:
                    min_sqm = min_rule.min_sqm
                    if total_sqm < min_sqm:
                        effective_sqm = min_sqm
                        minimum_applied = True
                        print(f"[PRICING] Minimo applicato: {total_sqm:.3f} → {effective_sqm:.3f} m²")
                    break
        
        # Usa metri quadri effettivi per trovare lo scaglione
        standard_price = get_price_for_sqm(item_code, effective_sqm)
        
        if standard_price and minimum_applied:
            standard_price["min_applied"] = True
            standard_price["original_sqm"] = total_sqm
            standard_price["effective_sqm"] = effective_sqm
            standard_price["customer_group"] = customer_group
            standard_price["min_sqm"] = min_sqm
        
        return standard_price
        
    except Exception as e:
        print(f"[PRICING] Errore: {e}")
        frappe.log_error(f"Errore get_customer_specific_price_for_sqm: {str(e)}")
        return get_price_for_sqm(item_code, total_sqm)

@frappe.whitelist()
def calculate_item_pricing(item_code, base, altezza, qty=1, customer=None):
    """
    API per calcolare prezzo con scaglioni e minimi gruppo cliente
    FIXED: Rate corretto con minimi applicati
    """
    try:
        print(f"[API] ===== CALCOLO PREZZO =====")
        print(f"[API] Input: item={item_code}, base={base}, altezza={altezza}, qty={qty}, customer={customer}")
        
        base = float(base) if base else 0
        altezza = float(altezza) if altezza else 0
        qty = float(qty) if qty else 1
        
        if not base or not altezza or base <= 0 or altezza <= 0:
            return {"error": "Base e altezza devono essere maggiori di 0"}
        
        # Calcola m² originali
        mq_singolo = (base * altezza) / 10000
        mq_totali_originali = mq_singolo * qty
        
        print(f"[API] m² originali: singolo={mq_singolo:.4f}, totali={mq_totali_originali:.3f}")
        
        # Ottieni pricing info (con minimi se c'è customer)
        if customer:
            print(f"[API] Calcolo con customer group per: {customer}")
            pricing_info = get_customer_specific_price_for_sqm(customer, item_code, mq_totali_originali)
        else:
            print(f"[API] Calcolo standard senza customer")
            pricing_info = get_price_for_sqm(item_code, mq_totali_originali)
        
        if not pricing_info:
            return {
                "error": "Nessuno scaglione configurato per questo item",
                "mq_singolo": mq_singolo,
                "mq_totali": mq_totali_originali
            }
        
        # Ottieni m² effettivi (con minimi applicati se presenti)
        mq_effettivi = pricing_info.get("effective_sqm", mq_totali_originali)
        minimo_applicato = pricing_info.get("min_applied", False)
        
        print(f"[API] m² effettivi: {mq_effettivi:.3f} (minimo applicato: {minimo_applicato})")
        
        # CALCOLO RATE CORRETTO
        price_per_sqm = pricing_info["price_per_sqm"]
        
        if minimo_applicato:
            # Se c'è minimo: rate = (m² effettivi / quantità) * prezzo_mq
            rate_unitario = (mq_effettivi / qty) * price_per_sqm
            print(f"[API] Rate con minimo: ({mq_effettivi:.3f} / {qty}) * {price_per_sqm} = {rate_unitario:.2f}")
        else:
            # Calcolo normale: rate = m² singolo * prezzo_mq  
            rate_unitario = mq_singolo * price_per_sqm
            print(f"[API] Rate normale: {mq_singolo:.4f} * {price_per_sqm} = {rate_unitario:.2f}")
        
        totale_ordine = rate_unitario * qty
        
        print(f"[API] Risultato finale: rate={rate_unitario:.2f}, totale={totale_ordine:.2f}")
        
        # Note dettagliate
        range_text = f"{pricing_info['from_sqm']}-{pricing_info.get('to_sqm', '∞')}"
        note_calcolo = [
            f"Scaglione: {pricing_info.get('tier_name', 'Standard')} ({range_text} m²)",
            f"Prezzo: €{price_per_sqm}/m²",
            f"Dimensioni: {base}×{altezza}cm",
            f"m² singolo: {mq_singolo:.4f} m²",
            f"Quantità: {qty} pz",
            f"m² originali: {mq_totali_originali:.3f} m²"
        ]
        
        if minimo_applicato:
            customer_group = pricing_info.get("customer_group", "")
            min_sqm = pricing_info.get("min_sqm", 0)
            note_calcolo.extend([
                f"⚠️ MINIMO GRUPPO {customer_group.upper()}: {min_sqm} m²",
                f"📊 m² fatturati: {mq_effettivi:.3f} m²",
                f"💰 Prezzo calcolato su: {mq_effettivi:.3f} m² × €{price_per_sqm}/m²"
            ])
        else:
            note_calcolo.append(f"📊 m² fatturati: {mq_totali_originali:.3f} m²")
        
        note_calcolo.extend([
            f"💵 Prezzo unitario: €{rate_unitario:.2f}",
            f"💸 Totale riga: €{totale_ordine:.2f}"
        ])
        
        return {
            "success": True,
            "item_code": item_code,
            "customer": customer,
            "mq_singolo": round(mq_singolo, 4),
            "mq_totali": round(mq_totali_originali, 3),
            "mq_effettivi": round(mq_effettivi, 3),
            "price_per_sqm": price_per_sqm,
            "rate": round(rate_unitario, 2),
            "total_amount": round(totale_ordine, 2),
            "tier_info": pricing_info,
            "note_calcolo": "\n".join(note_calcolo),
            "group_info": {
                "min_applied": minimo_applicato,
                "customer_group": pricing_info.get("customer_group"),
                "effective_sqm": mq_effettivi,
                "original_sqm": mq_totali_originali
            }
        }
        
    except Exception as e:
        print(f"[API] ❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Errore calcolo: {str(e)}"}

@frappe.whitelist()
def get_customer_group_min_sqm(customer, item_code):
    """
    API per ottenere minimo m² per un cliente (chiamata da JavaScript)
    """
    try:
        if not customer or not item_code:
            return {"min_sqm": 0}
        
        customer_group = frappe.db.get_value("Customer", customer, "customer_group")
        
        return {
            "customer": customer,
            "customer_group": customer_group,
            "item_code": item_code,
            "min_sqm": 0  # Per ora semplificato
        }
        
    except Exception as e:
        frappe.log_error(f"Errore get_customer_group_min_sqm: {str(e)}")
        return {"min_sqm": 0, "error": str(e)}

def validate_pricing_tiers(doc, method=None):
    """
    Valida scaglioni prezzo quando si salva un Item
    FIXED: Permette scaglioni contigui e valore 0
    """
    if not getattr(doc, 'supports_custom_measurement', 0):
        return
    
    if not hasattr(doc, 'pricing_tiers') or not doc.pricing_tiers:
        return
    
    errors = []
    
    # Ordina per from_sqm per validazione
    tiers = sorted(doc.pricing_tiers, key=lambda x: x.from_sqm)
    
    for i, tier in enumerate(tiers):
        # Valida singolo scaglione
        if tier.from_sqm < 0:
            errors.append(f"Riga {i+1}: 'Da m²' non può essere negativo")
        
        if tier.to_sqm and tier.from_sqm >= tier.to_sqm:
            errors.append(f"Riga {i+1}: 'A m²' deve essere maggiore di 'Da m²'")
        
        if tier.price_per_sqm <= 0:
            errors.append(f"Riga {i+1}: 'Prezzo €/m²' deve essere maggiore di 0")
    
    if errors:
        frappe.throw(_("Errori negli scaglioni prezzo:\n" + "\n".join(errors)))

def get_item_price_info(item_code):
    """
    Ottieni informazioni complete sui prezzi di un item
    """
    try:
        item_doc = frappe.get_doc("Item", item_code)
        
        info = {
            "item_code": item_code,
            "item_name": item_doc.item_name,
            "supports_custom_measurement": getattr(item_doc, 'supports_custom_measurement', 0),
            "tipo_vendita_default": getattr(item_doc, 'tipo_vendita_default', ''),
            "has_pricing_tiers": False,
            "tiers": []
        }
        
        if hasattr(item_doc, 'pricing_tiers') and item_doc.pricing_tiers:
            info["has_pricing_tiers"] = True
            for tier in item_doc.pricing_tiers:
                info["tiers"].append({
                    "from_sqm": tier.from_sqm,
                    "to_sqm": tier.to_sqm,
                    "price_per_sqm": tier.price_per_sqm,
                    "tier_name": tier.tier_name,
                    "is_default": tier.is_default
                })
        
        return info
        
    except Exception as e:
        return {"error": str(e)}