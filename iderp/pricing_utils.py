# iderp/pricing_utils.py
"""
Utility functions per gestione scaglioni prezzo IDERP
ERPNext 15 Compatible - Sistema Universale Metro Quadrato/Lineare/Pezzo
"""

import frappe
from frappe import _
import json

# ================================
# API PRINCIPALI WHITELISTED
# ================================

@frappe.whitelist()
def calculate_universal_item_pricing(item_code, tipo_vendita, base=0, altezza=0, lunghezza=0, qty=1, customer=None):
    """
    API universale per calcolare prezzo per tutti i tipi di vendita
    Compatibile ERPNext 15 - Chiamata da JavaScript
    """
    try:
        # Log della chiamata per debug
        frappe.logger().info(f"[IDERP API] calculate_universal_item_pricing: {item_code}, {tipo_vendita}, customer={customer}")
        
        # Validazione parametri base
        if not item_code:
            return {"error": "Item code richiesto", "success": False}
        
        if not frappe.db.exists("Item", item_code):
            return {"error": f"Item '{item_code}' non trovato", "success": False}
        
        qty = float(qty) if qty else 1
        
        # Calcola quantità base per tipo vendita
        qty_result = calculate_base_quantities_for_type(tipo_vendita, base, altezza, lunghezza, qty)
        if not qty_result["success"]:
            return qty_result
        
        unit_qty = qty_result["unit_qty"]
        total_qty = qty_result["total_qty"]
        qty_label = qty_result["qty_label"]
        
        # Ottieni pricing considerando customer group se disponibile
        if customer:
            pricing_info = get_customer_specific_pricing_for_type(customer, item_code, tipo_vendita, total_qty)
        else:
            pricing_info = get_item_pricing_for_type(item_code, tipo_vendita, total_qty)
        
        if not pricing_info:
            return {
                "error": f"Nessuno scaglione configurato per {tipo_vendita}",
                "success": False,
                "unit_qty": unit_qty,
                "total_qty": total_qty,
                "qty_label": qty_label
            }
        
        # Calcola rate unitario
        price_per_unit = pricing_info["price_per_unit"]
        rate_unitario = unit_qty * price_per_unit
        
        # Applica minimi se configurati
        if pricing_info.get("min_applied"):
            effective_qty = pricing_info.get("effective_qty", total_qty)
            rate_unitario = (effective_qty / qty) * price_per_unit
        
        # Costruisci note dettagliate
        note_parts = build_calculation_notes(tipo_vendita, qty_result, pricing_info, price_per_unit, rate_unitario)
        
        return {
            "success": True,
            "item_code": item_code,
            "tipo_vendita": tipo_vendita,
            "customer": customer,
            "unit_qty": round(unit_qty, 4),
            "total_qty": round(total_qty, 3),
            "price_per_unit": price_per_unit,
            "rate": round(rate_unitario, 2),
            "tier_info": pricing_info,
            "note_calcolo": "\n".join(note_parts),
            "qty_label": qty_label
        }
        
    except Exception as e:
        frappe.logger().error(f"[IDERP API] Errore calculate_universal_item_pricing: {str(e)}")
        return {
            "error": f"Errore interno: {str(e)}",
            "success": False
        }

@frappe.whitelist()
def calculate_universal_item_pricing_with_fallback(item_code, tipo_vendita, base=0, altezza=0, lunghezza=0, qty=1, customer=None):
    """
    API con fallback hard-coded per garantire sempre un risultato
    Usata quando il database non ha scaglioni configurati
    """
    try:
        # Prima prova con sistema database normale
        result = calculate_universal_item_pricing(item_code, tipo_vendita, base, altezza, lunghezza, qty, customer)
        
        if result.get("success"):
            return result
        
        # Se fallisce, usa fallback hard-coded
        frappe.logger().info(f"[IDERP FALLBACK] Usando prezzi hard-coded per {tipo_vendita}")
        
        # Calcola quantità
        qty_result = calculate_base_quantities_for_type(tipo_vendita, base, altezza, lunghezza, qty)
        if not qty_result["success"]:
            return qty_result
        
        # Prezzi fallback realistici per stampa digitale
        fallback_pricing = get_hardcoded_fallback_pricing(tipo_vendita, qty_result["total_qty"])
        
        if not fallback_pricing:
            return {"error": f"Nessun fallback disponibile per {tipo_vendita}", "success": False}
        
        rate_unitario = qty_result["unit_qty"] * fallback_pricing["price_per_unit"]
        
        return {
            "success": True,
            "item_code": item_code,
            "tipo_vendita": tipo_vendita,
            "customer": customer,
            "unit_qty": round(qty_result["unit_qty"], 4),
            "total_qty": round(qty_result["total_qty"], 3),
            "price_per_unit": fallback_pricing["price_per_unit"],
            "rate": round(rate_unitario, 2),
            "tier_info": {
                "tier_name": f"{fallback_pricing['tier_name']} (fallback)",
                "source": "hardcoded"
            },
            "note_calcolo": f"💾 FALLBACK HARD-CODED\n{tipo_vendita}: {qty_result['total_qty']:.3f} {qty_result['qty_label']}\nPrezzo: €{fallback_pricing['price_per_unit']}/{qty_result['qty_label'].rstrip('z')}\nRate: €{rate_unitario:.2f}",
            "qty_label": qty_result["qty_label"]
        }
        
    except Exception as e:
        frappe.logger().error(f"[IDERP FALLBACK] Errore: {str(e)}")
        return {"error": f"Errore fallback: {str(e)}", "success": False}

@frappe.whitelist()
def get_item_pricing_tiers(item_code):
    """
    API per ottenere scaglioni prezzo di un item (chiamata da JavaScript)
    ERPNext 15 Compatible
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
        
        # Raggruppa scaglioni per tipo vendita
        tiers_by_type = {}
        
        for tier in item_doc.pricing_tiers:
            # Compatibilità con formato nuovo e legacy
            selling_type = getattr(tier, 'selling_type', None)
            if not selling_type:
                # Formato legacy - assume Metro Quadrato se ha campi sqm
                if hasattr(tier, 'from_sqm') or hasattr(tier, 'price_per_sqm'):
                    selling_type = "Metro Quadrato"
                else:
                    selling_type = "Pezzo"
            
            if selling_type not in tiers_by_type:
                tiers_by_type[selling_type] = []
            
            # Costruisci tier info compatibile
            tier_info = {
                "selling_type": selling_type,
                "from_qty": getattr(tier, 'from_qty', getattr(tier, 'from_sqm', 0)),
                "to_qty": getattr(tier, 'to_qty', getattr(tier, 'to_sqm', None)),
                "price_per_unit": getattr(tier, 'price_per_unit', getattr(tier, 'price_per_sqm', 0)),
                "tier_name": getattr(tier, 'tier_name', ''),
                "is_default": getattr(tier, 'is_default', 0)
            }
            
            tiers_by_type[selling_type].append(tier_info)
        
        # Ordina ogni tipo per from_qty
        for selling_type in tiers_by_type:
            tiers_by_type[selling_type].sort(key=lambda x: x["from_qty"])
        
        return {
            "tiers_by_type": tiers_by_type,
            "item_code": item_code,
            "supports_tiers": True,
            "total_tiers": len(item_doc.pricing_tiers)
        }
        
    except Exception as e:
        frappe.logger().error(f"[IDERP API] Errore get_item_pricing_tiers: {str(e)}")
        return {"error": f"Errore caricamento scaglioni: {str(e)}"}

@frappe.whitelist()
def get_customer_group_min_sqm(customer, item_code):
    """
    API per ottenere minimo m² per un cliente (chiamata da JavaScript)
    ERPNext 15 Compatible
    """
    try:
        if not customer or not item_code:
            return {"min_sqm": 0}
        
        customer_group = frappe.db.get_value("Customer", customer, "customer_group")
        if not customer_group:
            return {"min_sqm": 0, "customer_group": None}
        
        # Cerca minimo nella configurazione item
        item_doc = frappe.get_doc("Item", item_code)
        
        if hasattr(item_doc, 'customer_group_minimums') and item_doc.customer_group_minimums:
            for min_rule in item_doc.customer_group_minimums:
                if (min_rule.customer_group == customer_group and 
                    getattr(min_rule, 'selling_type', 'Metro Quadrato') == 'Metro Quadrato' and
                    min_rule.enabled):
                    
                    min_qty = getattr(min_rule, 'min_qty', getattr(min_rule, 'min_sqm', 0))
                    
                    return {
                        "customer": customer,
                        "customer_group": customer_group,
                        "item_code": item_code,
                        "min_sqm": min_qty,
                        "calculation_mode": getattr(min_rule, 'calculation_mode', 'Per Riga'),
                        "description": getattr(min_rule, 'description', '')
                    }
        
        return {
            "customer": customer,
            "customer_group": customer_group,
            "item_code": item_code,
            "min_sqm": 0
        }
        
    except Exception as e:
        frappe.logger().error(f"[IDERP API] Errore get_customer_group_min_sqm: {str(e)}")
        return {"min_sqm": 0, "error": str(e)}

# ================================
# FUNZIONI CORE INTERNE
# ================================

def calculate_base_quantities_for_type(tipo_vendita, base=0, altezza=0, lunghezza=0, qty=1):
    """
    Calcola quantità base per ogni tipo di vendita
    Utilizzata internamente dalle API
    """
    try:
        qty = float(qty) if qty else 1
        
        if tipo_vendita == "Metro Quadrato":
            base = float(base) if base else 0
            altezza = float(altezza) if altezza else 0
            
            if not base or not altezza or base <= 0 or altezza <= 0:
                return {
                    "success": False,
                    "error": "Base e altezza devono essere maggiori di 0"
                }
            
            unit_qty = (base * altezza) / 10000  # da cm² a m²
            total_qty = unit_qty * qty
            
            return {
                "success": True,
                "unit_qty": unit_qty,
                "total_qty": total_qty,
                "qty_label": "m²",
                "dimensions": f"{base}×{altezza}cm"
            }
            
        elif tipo_vendita == "Metro Lineare":
            lunghezza = float(lunghezza) if lunghezza else 0
            
            if not lunghezza or lunghezza <= 0:
                return {
                    "success": False,
                    "error": "Lunghezza deve essere maggiore di 0"
                }
            
            unit_qty = lunghezza / 100  # da cm a metri
            total_qty = unit_qty * qty
            
            return {
                "success": True,
                "unit_qty": unit_qty,
                "total_qty": total_qty,
                "qty_label": "ml",
                "dimensions": f"{lunghezza}cm"
            }
            
        elif tipo_vendita == "Pezzo":
            return {
                "success": True,
                "unit_qty": 1,
                "total_qty": qty,
                "qty_label": "pz",
                "dimensions": f"{qty} pezzi"
            }
        
        else:
            return {
                "success": False,
                "error": f"Tipo vendita non supportato: {tipo_vendita}"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Errore calcolo quantità: {str(e)}"
        }

def get_item_pricing_for_type(item_code, tipo_vendita, quantity):
    """
    Ottieni prezzo per tipo vendita senza customer group
    Cerca negli scaglioni dell'item
    """
    try:
        item_doc = frappe.get_doc("Item", item_code)
        
        if not hasattr(item_doc, 'pricing_tiers') or not item_doc.pricing_tiers:
            return None
        
        # Cerca scaglioni per questo tipo
        matching_tiers = []
        for tier in item_doc.pricing_tiers:
            # Compatibilità formato nuovo e legacy
            tier_type = getattr(tier, 'selling_type', None)
            if not tier_type:
                # Formato legacy
                if hasattr(tier, 'from_sqm') or hasattr(tier, 'price_per_sqm'):
                    tier_type = "Metro Quadrato"
                else:
                    tier_type = "Pezzo"
            
            if tier_type == tipo_vendita:
                matching_tiers.append(tier)
        
        if not matching_tiers:
            return None
        
        # Cerca scaglione appropriato
        for tier in matching_tiers:
            from_qty = getattr(tier, 'from_qty', getattr(tier, 'from_sqm', 0))
            to_qty = getattr(tier, 'to_qty', getattr(tier, 'to_sqm', None))
            
            if quantity >= from_qty:
                if not to_qty or quantity <= to_qty:
                    return {
                        "price_per_unit": getattr(tier, 'price_per_unit', getattr(tier, 'price_per_sqm', 0)),
                        "tier_name": getattr(tier, 'tier_name', 'Standard'),
                        "from_qty": from_qty,
                        "to_qty": to_qty,
                        "source": "database"
                    }
        
        # Cerca default per questo tipo
        for tier in matching_tiers:
            if getattr(tier, 'is_default', 0):
                return {
                    "price_per_unit": getattr(tier, 'price_per_unit', getattr(tier, 'price_per_sqm', 0)),
                    "tier_name": f"{getattr(tier, 'tier_name', 'Standard')} (Default)",
                    "from_qty": 0,
                    "to_qty": None,
                    "source": "database"
                }
        
        return None
        
    except Exception as e:
        frappe.logger().error(f"[IDERP] Errore get_item_pricing_for_type: {str(e)}")
        return None

def get_customer_specific_pricing_for_type(customer, item_code, tipo_vendita, quantity):
    """
    Ottieni prezzo considerando customer group e minimi
    """
    if not customer:
        return get_item_pricing_for_type(item_code, tipo_vendita, quantity)
    
    try:
        # Ottieni gruppo cliente
        customer_group = frappe.db.get_value("Customer", customer, "customer_group")
        if not customer_group:
            return get_item_pricing_for_type(item_code, tipo_vendita, quantity)
        
        # Carica item e cerca minimi
        item_doc = frappe.get_doc("Item", item_code)
        minimum_applied = False
        effective_qty = quantity
        minimum_config = None
        
        if hasattr(item_doc, 'customer_group_minimums') and item_doc.customer_group_minimums:
            for min_rule in item_doc.customer_group_minimums:
                if (min_rule.customer_group == customer_group and 
                    getattr(min_rule, 'selling_type', 'Metro Quadrato') == tipo_vendita and 
                    min_rule.enabled):
                    
                    min_qty = getattr(min_rule, 'min_qty', getattr(min_rule, 'min_sqm', 0))
                    if quantity < min_qty:
                        effective_qty = min_qty
                        minimum_applied = True
                        minimum_config = min_rule
                        frappe.logger().info(f"[IDERP] Minimo applicato {tipo_vendita}: {quantity:.3f} → {effective_qty:.3f}")
                    break
        
        # Usa quantità effettiva per trovare prezzo
        standard_price = get_item_pricing_for_type(item_code, tipo_vendita, effective_qty)
        
        if standard_price and minimum_applied:
            standard_price.update({
                "min_applied": True,
                "original_qty": quantity,
                "effective_qty": effective_qty,
                "customer_group": customer_group,
                "min_qty": effective_qty,
                "minimum_config": minimum_config
            })
        
        return standard_price
        
    except Exception as e:
        frappe.logger().error(f"[IDERP] Errore customer specific pricing: {str(e)}")
        return get_item_pricing_for_type(item_code, tipo_vendita, quantity)

def get_hardcoded_fallback_pricing(tipo_vendita, quantity):
    """
    Prezzi fallback hard-coded quando il database è vuoto
    Prezzi realistici per stampa digitale
    """
    try:
        if tipo_vendita == "Metro Quadrato":
            # Scaglioni m² per stampa digitale
            if quantity <= 0.5:
                return {"price_per_unit": 25.0, "tier_name": "Micro tirature"}
            elif quantity <= 2.0:
                return {"price_per_unit": 18.0, "tier_name": "Piccole tirature"}
            elif quantity <= 10.0:
                return {"price_per_unit": 12.0, "tier_name": "Tirature medie"}
            else:
                return {"price_per_unit": 8.0, "tier_name": "Tirature grandi"}
                
        elif tipo_vendita == "Metro Lineare":
            # Scaglioni ml per banner/striscioni
            if quantity <= 5.0:
                return {"price_per_unit": 8.0, "tier_name": "Piccoli formati"}
            elif quantity <= 20.0:
                return {"price_per_unit": 6.0, "tier_name": "Formati medi"}
            else:
                return {"price_per_unit": 4.0, "tier_name": "Grandi formati"}
                
        elif tipo_vendita == "Pezzo":
            # Scaglioni pezzi per prodotti vari
            if quantity <= 10:
                return {"price_per_unit": 5.0, "tier_name": "Retail"}
            elif quantity <= 100:
                return {"price_per_unit": 3.0, "tier_name": "Wholesale"}
            else:
                return {"price_per_unit": 2.0, "tier_name": "Bulk"}
        
        return None
        
    except Exception as e:
        frappe.logger().error(f"[IDERP] Errore fallback pricing: {str(e)}")
        return None

def build_calculation_notes(tipo_vendita, qty_result, pricing_info, price_per_unit, rate_unitario):
    """
    Costruisce note dettagliate per il calcolo
    """
    note_parts = [
        f"🎯 Tipo: {tipo_vendita}",
        f"📊 Scaglione: {pricing_info.get('tier_name', 'Standard')}"
    ]
    
    # Dettagli specifici per tipo
    if tipo_vendita == "Metro Quadrato" and "dimensions" in qty_result:
        note_parts.extend([
            f"📐 Dimensioni: {qty_result['dimensions']}",
            f"🔢 m² singolo: {qty_result['unit_qty']:.4f} m²",
            f"📊 m² totali: {qty_result['total_qty']:.3f} m²"
        ])
    elif tipo_vendita == "Metro Lineare" and "dimensions" in qty_result:
        note_parts.extend([
            f"📏 Lunghezza: {qty_result['dimensions']}",
            f"📊 ml totali: {qty_result['total_qty']:.2f} ml"
        ])
    elif tipo_vendita == "Pezzo":
        note_parts.append(f"📦 Quantità: {qty_result['total_qty']:.0f} pezzi")
    
    # Minimi applicati
    if pricing_info.get("min_applied"):
        note_parts.extend([
            f"⚠️ MINIMO {pricing_info.get('customer_group', '')}: {pricing_info.get('min_qty', 0)} {qty_result['qty_label']}",
            f"📈 Quantità effettiva: {pricing_info.get('effective_qty', qty_result['total_qty']):.3f} {qty_result['qty_label']}"
        ])
    
    # Prezzo e calcolo
    note_parts.extend([
        f"💰 Prezzo: €{price_per_unit}/{qty_result['qty_label'].rstrip('z')}",
        f"💵 Prezzo unitario: €{rate_unitario:.2f}"
    ])
    
    # Fonte del prezzo
    if pricing_info.get("source") == "hardcoded":
        note_parts.append("💾 Fonte: Fallback hard-coded")
    else:
        note_parts.append("🗄️ Fonte: Scaglioni configurati")
    
    return note_parts

# ================================
# VALIDAZIONE SCAGLIONI
# ================================

def validate_pricing_tiers(doc, method=None):
    """
    Valida scaglioni prezzo quando si salva un Item
    ERPNext 15 Compatible - Fix per scaglioni contigui
    """
    if not getattr(doc, 'supports_custom_measurement', 0):
        return
    
    if not hasattr(doc, 'pricing_tiers') or not doc.pricing_tiers:
        return
    
    errors = []
    warnings = []
    
    # Raggruppa per tipo vendita
    tiers_by_type = {}
    for i, tier in enumerate(doc.pricing_tiers):
        # Determina tipo vendita
        selling_type = getattr(tier, 'selling_type', None)
        if not selling_type:
            # Formato legacy
            if hasattr(tier, 'from_sqm') or hasattr(tier, 'price_per_sqm'):
                selling_type = "Metro Quadrato"
            else:
                selling_type = "Pezzo"
        
        if selling_type not in tiers_by_type:
            tiers_by_type[selling_type] = []
        
        tiers_by_type[selling_type].append((i + 1, tier))  # (row_number, tier)
    
    # Valida ogni tipo separatamente
    for selling_type, tier_list in tiers_by_type.items():
        validate_tiers_for_type(selling_type, tier_list, errors, warnings)
    
    # Mostra risultati
    if errors:
        error_message = "❌ ERRORI negli scaglioni prezzo:\n" + "\n".join(errors)
        if warnings:
            error_message += "\n\n⚠️ AVVISI:\n" + "\n".join(warnings)
        frappe.throw(_(error_message))
    elif warnings:
        warning_message = "⚠️ AVVISI scaglioni prezzo:\n" + "\n".join(warnings)
        frappe.msgprint(_(warning_message), title="Configurazione Scaglioni", indicator="orange")

def validate_tiers_for_type(selling_type, tier_list, errors, warnings):
    """
    Valida scaglioni per un tipo vendita specifico
    """
    if not tier_list:
        return
    
    # Funzioni helper per compatibilità formato
    def get_from_value(tier):
        return getattr(tier, 'from_qty', getattr(tier, 'from_sqm', 0))
    
    def get_to_value(tier):
        return getattr(tier, 'to_qty', getattr(tier, 'to_sqm', None))
    
    def get_price_value(tier):
        return getattr(tier, 'price_per_unit', getattr(tier, 'price_per_sqm', 0))
    
    # Ordina per from_value
    try:
        tier_list.sort(key=lambda x: get_from_value(x[1]))
    except Exception as e:
        errors.append(f"Errore ordinamento {selling_type}: {str(e)}")
        return
    
    # Valida ogni scaglione
    for j, (row_num, tier) in enumerate(tier_list):
        from_value = get_from_value(tier)
        to_value = get_to_value(tier)
        price_value = get_price_value(tier)
        
        # Validazioni base
        if from_value < 0:
            errors.append(f"Riga {row_num} ({selling_type}): 'Da Quantità' non può essere negativo")
        
        if to_value is not None and to_value < 0:
            errors.append(f"Riga {row_num} ({selling_type}): 'A Quantità' non può essere negativo")
        
        if to_value is not None and from_value >= to_value:
            errors.append(f"Riga {row_num} ({selling_type}): 'A Quantità' ({to_value}) deve essere maggiore di 'Da Quantità' ({from_value})")
        
        if price_value <= 0:
            errors.append(f"Riga {row_num} ({selling_type}): 'Prezzo/Unità' deve essere maggiore di 0")
        
        # Validazioni sovrapposizioni
        if j > 0:
            prev_row_num, prev_tier = tier_list[j-1]
            prev_to_value = get_to_value(prev_tier)
            
            # VERA sovrapposizione (non scaglioni contigui)
            if prev_to_value is not None and from_value < prev_to_value:
                errors.append(
                    f"Riga {row_num} ({selling_type}): Sovrapposizione - inizia a {from_value} "
                    f"ma il precedente (riga {prev_row_num}) finisce a {prev_to_value}"
                )
            
            # Gap tra scaglioni (warning)
            elif prev_to_value is not None and from_value > prev_to_value:
                gap_size = from_value - prev_to_value
                warnings.append(
                    f"Riga {row_num} ({selling_type}): Gap di {gap_size} tra riga {prev_row_num} e {row_num} "
                    f"- ordini in questo range useranno scaglione precedente"
                )

# ================================
# UTILITY E COMPATIBILITY
# ================================

def get_price_for_sqm(item_code, total_sqm):
    """
    Funzione legacy per compatibilità - ora usa sistema universale
    """
    result = get_item_pricing_for_type(item_code, "Metro Quadrato", total_sqm)
    if result:
        return {
            "price_per_sqm": result["price_per_unit"],
            "tier_name": result["tier_name"],
            "from_sqm": result["from_qty"],
            "to_sqm": result["to_qty"]
        }
    return None

def get_customer_specific_price_for_sqm(customer, item_code, total_sqm):
    """
    Funzione legacy per compatibilità - ora usa sistema universale
    """
    result = get_customer_specific_pricing_for_type(customer, item_code, "Metro Quadrato", total_sqm)
    if result:
        return {
            "price_per_sqm": result["price_per_unit"],
            "tier_name": result["tier_name"],
            "from_sqm": result["from_qty"],
            "to_sqm": result["to_qty"],
            "min_applied": result.get("min_applied", False),
            "original_sqm": result.get("original_qty", total_sqm),
            "effective_sqm": result.get("effective_qty", total_sqm),
            "customer_group": result.get("customer_group"),
            "min_sqm": result.get("min_qty", 0)
        }
    return None

@frappe.whitelist()
def calculate_item_pricing(item_code, base, altezza, qty=1, customer=None):
    """
    API legacy per compatibilità - ora usa sistema universale
    """
    return calculate_universal_item_pricing(
        item_code=item_code,
        tipo_vendita="Metro Quadrato",
        base=base,
        altezza=altezza,
        qty=qty,
        customer=customer
    )

# ================================
# DEBUG E TESTING
# ================================

def debug_pricing_calculation(item_code, tipo_vendita, **kwargs):
    """
    Funzione di debug per troubleshooting calcoli
    """
    print(f"\n🔍 DEBUG PRICING: {item_code} - {tipo_vendita}")
    print("="*50)
    
    try:
        # Test calcolo quantità
        qty_result = calculate_base_quantities_for_type(tipo_vendita, **kwargs)
        print(f"1. Quantità: {qty_result}")
        
        if qty_result.get("success"):
            # Test pricing
            pricing_result = get_item_pricing_for_type(item_code, tipo_vendita, qty_result["total_qty"])
            print(f"2. Pricing: {pricing_result}")
            
            # Test API completa
            api_result = calculate_universal_item_pricing(item_code, tipo_vendita, **kwargs)
            print(f"3. API Result: {api_result}")
        
    except Exception as e:
        print(f"❌ Errore debug: {e}")

def get_pricing_system_status():
    """
    Ritorna stato del sistema pricing per diagnostica
    """
    try:
        # Item configurati
        configured_items = frappe.db.count("Item", {"supports_custom_measurement": 1})
        
        # Scaglioni totali
        total_tiers = frappe.db.sql("SELECT COUNT(*) FROM `tabItem Pricing Tier`")[0][0] if frappe.db.exists("DocType", "Item Pricing Tier") else 0
        
        # Customer groups configurati
        customer_groups = frappe.db.count("Customer Group", {"name": ["in", ["Finale", "Bronze", "Gold", "Diamond"]]})
        
        return {
            "configured_items": configured_items,
            "total_tiers": total_tiers,
            "customer_groups": customer_groups,
            "system_ready": configured_items > 0 and total_tiers > 0
        }
        
    except Exception as e:
        return {"error": str(e)}