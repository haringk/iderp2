# iderp/pricing_utils.py
"""
Utility functions per gestione scaglioni prezzo
AGGIORNATO: Supporto gruppi cliente e minimi
FIXED: Validazione scaglioni contigui e valore 0
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

@frappe.whitelist()
def calculate_item_pricing(item_code, base, altezza, qty=1, customer=None):
    """
    API per calcolare prezzo con scaglioni (chiamata da JavaScript)
    AGGIORNATO: Supporta gruppi cliente e minimi
    """
    try:
        base = float(base) if base else 0
        altezza = float(altezza) if altezza else 0
        qty = float(qty) if qty else 1
        
        if not base or not altezza or base <= 0 or altezza <= 0:
            return {"error": "Base e altezza devono essere maggiori di 0"}
        
        # Calcola m²
        mq_singolo = (base * altezza) / 10000
        mq_totali = mq_singolo * qty
        
        # NUOVO: Considera gruppo cliente se specificato
        if customer:
            from iderp.customer_group_pricing import get_customer_specific_price_for_sqm
            pricing_info = get_customer_specific_price_for_sqm(customer, item_code, mq_totali)
        else:
            # Usa prezzi standard
            pricing_info = get_price_for_sqm(item_code, mq_totali)
        
        if not pricing_info:
            return {
                "error": "Nessuno scaglione configurato per questo item",
                "mq_singolo": mq_singolo,
                "mq_totali": mq_totali
            }
        
        # Calcola prezzi
        price_per_sqm = pricing_info["price_per_sqm"]
        rate_unitario = mq_singolo * price_per_sqm
        totale_ordine = rate_unitario * qty
        
        # Prepara note base
        range_text = f"{pricing_info['from_sqm']}-{pricing_info['to_sqm'] or '∞'}"
        note_calcolo = (
            f"Scaglione: {pricing_info['tier_name']} ({range_text} m²)\n"
            f"Prezzo: €{price_per_sqm}/m²\n"
            f"Dimensioni: {base}×{altezza}cm\n"
            f"m² singolo: {mq_singolo:.4f} m²\n"
            f"Prezzo unitario: €{rate_unitario:.2f}\n"
            f"Quantità: {qty} pz\n"
            f"m² totali: {mq_totali:.3f} m²\n"
            f"Totale ordine: €{totale_ordine:.2f}"
        )
        
        # NUOVO: Aggiungi info gruppo cliente se presente
        if pricing_info.get("min_applied"):
            note_calcolo += f"\n⚠️ MINIMO GRUPPO {pricing_info['customer_group'].upper()}: {pricing_info['min_sqm']} m²"
            note_calcolo += f"\n📊 Fatturato su {pricing_info['effective_sqm']} m² invece di {pricing_info['original_sqm']:.3f} m²"
        
        return {
            "success": True,
            "item_code": item_code,
            "customer": customer,
            "mq_singolo": round(mq_singolo, 4),
            "mq_totali": round(mq_totali, 3),
            "price_per_sqm": price_per_sqm,
            "rate": round(rate_unitario, 2),
            "total_amount": round(totale_ordine, 2),
            "tier_info": pricing_info,
            "note_calcolo": note_calcolo,
            # NUOVO: Info gruppo cliente
            "group_info": {
                "min_applied": pricing_info.get("min_applied", False),
                "customer_group": pricing_info.get("customer_group"),
                "effective_sqm": pricing_info.get("effective_sqm", mq_totali),
                "original_sqm": pricing_info.get("original_sqm", mq_totali)
            }
        }
        
    except Exception as e:
        frappe.log_error(f"Errore calculate_item_pricing: {str(e)}")
        return {"error": f"Errore calcolo: {str(e)}"}

@frappe.whitelist()
def get_customer_group_min_sqm(customer, item_code):
    """
    API per ottenere minimo m² per un cliente (chiamata da JavaScript)
    """
    try:
        if not customer or not item_code:
            return {"min_sqm": 0}
        
        from iderp.customer_group_pricing import get_customer_specific_min_sqm
        min_sqm = get_customer_specific_min_sqm(customer, item_code)
        
        customer_group = frappe.db.get_value("Customer", customer, "customer_group")
        
        return {
            "customer": customer,
            "customer_group": customer_group,
            "item_code": item_code,
            "min_sqm": min_sqm
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
        # FIXED: Permette valore 0
        if tier.from_sqm < 0:
            errors.append(f"Riga {i+1}: 'Da m²' non può essere negativo (0 è permesso)")
        
        if tier.to_sqm and tier.from_sqm >= tier.to_sqm:
            errors.append(f"Riga {i+1}: 'A m²' deve essere maggiore di 'Da m²'")
        
        if tier.price_per_sqm <= 0:
            errors.append(f"Riga {i+1}: 'Prezzo €/m²' deve essere maggiore di 0")
        
        # Valida sovrapposizioni
        # FIXED: Scaglioni contigui sono permessi
        if i > 0:
            prev_tier = tiers[i-1]
            # VERA sovrapposizione: inizia PRIMA che finisca il precedente
            if prev_tier.to_sqm and tier.from_sqm < prev_tier.to_sqm:
                errors.append(f"Riga {i+1}: Sovrapposizione - inizia a {tier.from_sqm} ma il precedente finisce a {prev_tier.to_sqm}")
    
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

# Hook per validazione automatica quando si salva Item
def setup_item_hooks():
    """Setup hook per validazione Item"""
    # Questo verrà chiamato dall'hooks.py
    pass