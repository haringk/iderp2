# iderp/global_minimums.py
"""
Sistema minimi globali per preventivo
Calcola minimi UNA volta per item e li redistribuisce proporzionalmente
"""

import frappe
from collections import defaultdict

def apply_global_minimums_server_side(doc, method=None):
    """
    Applica minimi globali per preventivo invece che per singola riga
    """
    if not hasattr(doc, 'items') or not doc.items:
        return
    
    customer = getattr(doc, 'customer', None) or getattr(doc, 'party_name', None)
    if not customer:
        return
    
    # Ottieni gruppo cliente
    customer_group = frappe.db.get_value("Customer", customer, "customer_group")
    if not customer_group:
        return
    
    print(f"[GLOBAL] === Applicando minimi globali per {customer} (gruppo: {customer_group}) ===")
    
    # Raggruppa righe per item_code + calculation_mode
    item_groups = defaultdict(list)
    global_items = []  # Item con modalità globale
    
    for item in doc.items:
        if getattr(item, 'tipo_vendita', '') != 'Metro Quadrato':
            continue
            
        if not getattr(item, 'base', 0) or not getattr(item, 'altezza', 0):
            continue
        
        try:
            # Carica configurazione item
            item_doc = frappe.get_doc("Item", item.item_code)
            
            if not getattr(item_doc, 'supports_custom_measurement', 0):
                continue
                
            if not hasattr(item_doc, 'customer_group_minimums') or not item_doc.customer_group_minimums:
                continue
            
            # Cerca configurazione per questo gruppo
            minimum_config = None
            for min_rule in item_doc.customer_group_minimums:
                if min_rule.customer_group == customer_group and min_rule.enabled:
                    minimum_config = min_rule
                    break
            
            if not minimum_config:
                continue
            
            # Calcola m² di base
            base = float(item.base) 
            altezza = float(item.altezza)
            qty = float(item.qty or 1)
            
            mq_singolo = (base * altezza) / 10000
            mq_totali = mq_singolo * qty
            
            item.mq_singolo = mq_singolo
            item.mq_calcolati = mq_totali
            
            # Verifica modalità calcolo
            calculation_mode = getattr(minimum_config, 'calculation_mode', 'Per Riga')
            
            if calculation_mode == "Globale Preventivo":
                # Aggiungi a gruppo per calcolo globale
                key = f"{item.item_code}_{customer_group}"
                item_groups[key].append({
                    'item': item,
                    'minimum_config': minimum_config,
                    'mq_totali': mq_totali,
                    'item_doc': item_doc
                })
                global_items.append(item)
                print(f"[GLOBAL] Item {item.item_code} → modalità GLOBALE")
            else:
                # Applica minimo per riga (logica esistente)
                apply_single_row_minimum(item, minimum_config, item_doc)
                print(f"[GLOBAL] Item {item.item_code} → modalità PER RIGA")
                
        except Exception as e:
            print(f"[GLOBAL] ❌ Errore item {item.item_code}: {e}")
            continue
    
    # Applica minimi globali per ogni gruppo
    for group_key, group_items in item_groups.items():
        apply_global_minimum_to_group(group_items, customer_group)
    
    print(f"[GLOBAL] === Completato: {len(global_items)} item con minimi globali ===")

def apply_global_minimum_to_group(group_items, customer_group):
    """
    Applica minimo globale a un gruppo di righe dello stesso item
    """
    if not group_items:
        return
    
    item_code = group_items[0]['item'].item_code
    minimum_config = group_items[0]['minimum_config']
    item_doc = group_items[0]['item_doc']
    
    # Calcola totale m² per questo item nel preventivo
    total_sqm = sum(group_item['mq_totali'] for group_item in group_items)
    min_sqm = minimum_config.min_sqm
    
    print(f"[GLOBAL] Item {item_code}: {total_sqm:.3f} m² totali, minimo {min_sqm} m²")
    
    # Applica minimo UNA volta
    effective_total_sqm = max(total_sqm, min_sqm)
    minimum_applied = effective_total_sqm > total_sqm
    
    if minimum_applied:
        print(f"[GLOBAL] 🔥 MINIMO GLOBALE APPLICATO: {total_sqm:.3f} → {effective_total_sqm:.3f} m²")
    
    # Trova scaglione prezzo per il totale effettivo
    price_per_sqm = get_price_for_total_sqm(item_doc, effective_total_sqm)
    
    if price_per_sqm == 0:
        print(f"[GLOBAL] ⚠️ Nessun prezzo trovato per {effective_total_sqm:.3f} m²")
        return
    
    # Calcola totale valore per questo item
    total_value = effective_total_sqm * price_per_sqm
    
    print(f"[GLOBAL] Prezzo: €{price_per_sqm}/m² × {effective_total_sqm:.3f} m² = €{total_value:.2f}")
    
    # Redistribuisci proporzionalmente sulle righe
    for group_item in group_items:
        item = group_item['item']
        mq_originali = group_item['mq_totali']
        
        # Proporzione di questa riga sul totale
        if total_sqm > 0:
            proportion = mq_originali / total_sqm
            row_effective_sqm = effective_total_sqm * proportion
            row_value = total_value * proportion
            row_rate = row_value / float(item.qty or 1)
        else:
            row_effective_sqm = 0
            row_value = 0
            row_rate = 0
        
        # Aggiorna riga
        item.rate = round(row_rate, 2)
        item.prezzo_mq = price_per_sqm
        
        # Note dettagliate
        note_parts = [
            f"🌍 CALCOLO GLOBALE PREVENTIVO",
            f"🎯 Gruppo: {customer_group}",
            f"📐 Dimensioni: {item.base}×{item.altezza}cm",
            f"🔢 m² singolo: {item.mq_singolo:.4f} m²",
            f"📦 Quantità: {item.qty} pz",
            f"📊 m² riga: {mq_originali:.3f} m²",
            f"📈 TOTALE item nel preventivo: {total_sqm:.3f} m²"
        ]
        
        if minimum_applied:
            note_parts.extend([
                f"⚠️ MINIMO GLOBALE {customer_group}: {min_sqm} m²",
                f"💡 {minimum_config.description or 'Setup applicato UNA volta'}",
                f"🔄 m² effettivi totali: {effective_total_sqm:.3f} m²"
            ])
        
        note_parts.extend([
            f"💰 Prezzo: €{price_per_sqm}/m²",
            f"📊 Proporzione riga: {proportion:.1%}",
            f"💵 Valore riga: €{row_value:.2f}",
            f"💸 Prezzo unitario: €{row_rate:.2f}"
        ])
        
        item.note_calcolo = '\n'.join(note_parts)
        
        print(f"[GLOBAL] ✓ Riga {item.idx}: {mq_originali:.3f} m² → €{row_rate:.2f} ({proportion:.1%})")

def apply_single_row_minimum(item, minimum_config, item_doc):
    """
    Applica minimo per singola riga (logica esistente)
    """
    base = float(item.base) 
    altezza = float(item.altezza)
    qty = float(item.qty or 1)
    
    mq_singolo = (base * altezza) / 10000
    mq_totali = mq_singolo * qty
    
    # Applica minimo per riga
    mq_effettivi = max(mq_totali, minimum_config.min_sqm)
    minimo_applicato = mq_effettivi > mq_totali
    
    # Trova prezzo
    price_per_sqm = get_price_for_total_sqm(item_doc, mq_effettivi)
    
    if price_per_sqm > 0:
        calculated_rate = (mq_effettivi / qty) * price_per_sqm
        item.rate = round(calculated_rate, 2)
        item.prezzo_mq = price_per_sqm
        
        # Note per riga singola
        note_parts = [
            f"📄 CALCOLO PER RIGA",
            f"🎯 Gruppo: {minimum_config.customer_group}",
            f"📐 Dimensioni: {base}×{altezza}cm",
            f"🔢 m² singolo: {mq_singolo:.4f} m²",
            f"📦 Quantità: {qty} pz",
            f"📊 m² originali: {mq_totali:.3f} m²"
        ]
        
        if minimo_applicato:
            note_parts.extend([
                f"⚠️ MINIMO RIGA {minimum_config.customer_group}: {minimum_config.min_sqm} m²",
                f"📈 m² fatturati: {mq_effettivi:.3f} m²"
            ])
        
        note_parts.extend([
            f"💰 Prezzo: €{price_per_sqm}/m²",
            f"💵 Prezzo unitario: €{calculated_rate:.2f}"
        ])
        
        item.note_calcolo = '\n'.join(note_parts)

def get_price_for_total_sqm(item_doc, total_sqm):
    """
    Ottieni prezzo per m² in base agli scaglioni
    """
    try:
        if hasattr(item_doc, 'pricing_tiers') and item_doc.pricing_tiers:
            for tier in item_doc.pricing_tiers:
                if total_sqm >= tier.from_sqm:
                    if not tier.to_sqm or total_sqm <= tier.to_sqm:
                        return tier.price_per_sqm
            
            # Default tier
            for tier in item_doc.pricing_tiers:
                if tier.is_default:
                    return tier.price_per_sqm
        
        return 0
        
    except Exception as e:
        print(f"[GLOBAL] Errore prezzo: {e}")
        return 0