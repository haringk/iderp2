# iderp/universal_pricing.py
"""
Sistema prezzi universale per tutti i tipi di vendita:
- Metro Quadrato (esistente)
- Metro Lineare (nuovo)
- Pezzo/Cad (nuovo)
+ Costi fissi configurabili
"""

import frappe
from collections import defaultdict

def apply_universal_pricing_server_side(doc, method=None):
    """
    Applica pricing universale per tutti i tipi di vendita
    """
    if not hasattr(doc, 'items') or not doc.items:
        return
    
    customer = getattr(doc, 'customer', None) or getattr(doc, 'party_name', None)
    if not customer:
        return
    
    customer_group = frappe.db.get_value("Customer", customer, "customer_group")
    if not customer_group:
        return
    
    print(f"[UNIVERSAL] === Pricing universale per {customer} (gruppo: {customer_group}) ===")
    
    # Raggruppa item per tipo vendita e modalità calcolo
    pricing_groups = defaultdict(list)
    
    for item in doc.items:
        tipo_vendita = getattr(item, 'tipo_vendita', 'Pezzo')
        
        if tipo_vendita not in ['Metro Quadrato', 'Metro Lineare', 'Pezzo']:
            continue
        
        try:
            # Calcola quantità base per ogni tipo
            qty_info = calculate_base_quantities(item, tipo_vendita)
            if not qty_info:
                continue
            
            item.update(qty_info)  # Aggiorna campi calcolati
            
            # Carica configurazione item
            item_doc = frappe.get_doc("Item", item.item_code)
            minimum_config = get_minimum_config_for_type(item_doc, customer_group, tipo_vendita)
            
            if minimum_config:
                calculation_mode = getattr(minimum_config, 'calculation_mode', 'Per Riga')
                key = f"{item.item_code}_{tipo_vendita}_{calculation_mode}_{customer_group}"
                
                pricing_groups[key].append({
                    'item': item,
                    'minimum_config': minimum_config,
                    'item_doc': item_doc,
                    'tipo_vendita': tipo_vendita,
                    'base_qty': qty_info['total_qty']
                })
            else:
                # Nessun minimo, calcolo standard
                apply_standard_pricing(item, tipo_vendita)
                
        except Exception as e:
            print(f"[UNIVERSAL] ❌ Errore item {item.item_code}: {e}")
            continue
    
    # Applica pricing per ogni gruppo
    for group_key, group_items in pricing_groups.items():
        apply_pricing_to_group(group_items, customer_group)
    
    # Applica costi fissi globali
    apply_global_fixed_costs(doc, customer_group)
    
    print(f"[UNIVERSAL] === Completato pricing universale ===")

def calculate_base_quantities(item, tipo_vendita):
    """
    Calcola quantità base per ogni tipo di vendita
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
                'mq_singolo': round(mq_singolo, 4),
                'mq_calcolati': round(mq_totali, 3),
                'total_qty': mq_totali,
                'unit_qty': mq_singolo,
                'qty_label': 'm²'
            }
            
        elif tipo_vendita == "Metro Lineare":
            lunghezza = float(getattr(item, 'lunghezza', 0) or 0)
            
            if not lunghezza:
                return None
            
            ml_singolo = lunghezza / 100  # da cm a metri
            ml_totali = ml_singolo * qty
            
            return {
                'ml_singolo': round(ml_singolo, 2),
                'ml_calcolati': round(ml_totali, 2),
                'total_qty': ml_totali,
                'unit_qty': ml_singolo,
                'qty_label': 'ml'
            }
            
        elif tipo_vendita == "Pezzo":
            return {
                'pz_singolo': 1,
                'pz_totali': qty,
                'total_qty': qty,
                'unit_qty': 1,
                'qty_label': 'pz'
            }
            
        return None
        
    except Exception as e:
        print(f"[UNIVERSAL] Errore calcolo quantità {tipo_vendita}: {e}")
        return None

def get_minimum_config_for_type(item_doc, customer_group, tipo_vendita):
    """
    Ottieni configurazione minimi per tipo vendita
    """
    if not hasattr(item_doc, 'customer_group_minimums') or not item_doc.customer_group_minimums:
        return None
    
    for min_rule in item_doc.customer_group_minimums:
        if (min_rule.customer_group == customer_group and 
            getattr(min_rule, 'selling_type', 'Metro Quadrato') == tipo_vendita and 
            min_rule.enabled):
            return min_rule
    
    return None

def apply_pricing_to_group(group_items, customer_group):
    """
    Applica pricing a un gruppo di item dello stesso tipo
    """
    if not group_items:
        return
    
    first_item = group_items[0]
    item_code = first_item['item'].item_code
    tipo_vendita = first_item['tipo_vendita']
    minimum_config = first_item['minimum_config']
    calculation_mode = getattr(minimum_config, 'calculation_mode', 'Per Riga')
    
    print(f"[UNIVERSAL] Gruppo {item_code} ({tipo_vendita}) - Modalità: {calculation_mode}")
    
    if calculation_mode == "Globale Preventivo":
        apply_global_pricing_to_group(group_items, customer_group)
    else:
        # Per riga
        for group_item in group_items:
            apply_single_row_pricing(group_item, customer_group)

def apply_global_pricing_to_group(group_items, customer_group):
    """
    Applica pricing globale (come per m²)
    """
    if not group_items:
        return
    
    item_code = group_items[0]['item'].item_code
    tipo_vendita = group_items[0]['tipo_vendita']
    minimum_config = group_items[0]['minimum_config']
    item_doc = group_items[0]['item_doc']
    
    # Somma quantità totali
    total_qty = sum(group_item['base_qty'] for group_item in group_items)
    min_qty = getattr(minimum_config, 'min_qty', 0)
    
    print(f"[UNIVERSAL] {item_code} ({tipo_vendita}): {total_qty:.3f} totali, minimo {min_qty}")
    
    # Applica minimo
    effective_total_qty = max(total_qty, min_qty)
    minimum_applied = effective_total_qty > total_qty
    
    # Trova prezzo
    price_per_unit = get_price_for_quantity(item_doc, tipo_vendita, effective_total_qty)
    
    if price_per_unit == 0:
        print(f"[UNIVERSAL] ⚠️ Nessun prezzo per {effective_total_qty:.3f} {group_items[0]['item'].get('qty_label', 'unità')}")
        return
    
    # Calcola valore totale
    total_value = effective_total_qty * price_per_unit
    
    # Costo fisso per item totale
    fixed_cost = getattr(minimum_config, 'fixed_cost', 0) or 0
    fixed_cost_mode = getattr(minimum_config, 'fixed_cost_mode', 'Per Preventivo')
    
    if fixed_cost > 0 and fixed_cost_mode == "Per Item Totale":
        total_value += fixed_cost
        print(f"[UNIVERSAL] Costo fisso per item: +€{fixed_cost}")
    
    print(f"[UNIVERSAL] Valore totale: €{total_value:.2f}")
    
    # Redistribuisci
    for group_item in group_items:
        item = group_item['item']
        original_qty = group_item['base_qty']
        
        if total_qty > 0:
            proportion = original_qty / total_qty
            row_value = total_value * proportion
            row_rate = row_value / float(item.qty or 1)
        else:
            row_value = 0
            row_rate = 0
        
        # Costo fisso per riga
        if fixed_cost > 0 and fixed_cost_mode == "Per Riga":
            row_rate += fixed_cost
        
        # Aggiorna item
        item.rate = round(row_rate, 2)
        setattr(item, f'prezzo_{tipo_vendita.lower().replace(" ", "_")}', price_per_unit)
        
        # Note
        create_pricing_notes(item, tipo_vendita, minimum_config, {
            'original_qty': original_qty,
            'effective_total_qty': effective_total_qty,
            'minimum_applied': minimum_applied,
            'price_per_unit': price_per_unit,
            'proportion': proportion,
            'fixed_cost': fixed_cost if fixed_cost_mode == "Per Riga" else 0,
            'is_global': True
        })

def apply_single_row_pricing(group_item, customer_group):
    """
    Applica pricing per singola riga
    """
    item = group_item['item']
    tipo_vendita = group_item['tipo_vendita']
    minimum_config = group_item['minimum_config']
    item_doc = group_item['item_doc']
    original_qty = group_item['base_qty']
    
    min_qty = getattr(minimum_config, 'min_qty', 0)
    effective_qty = max(original_qty, min_qty)
    minimum_applied = effective_qty > original_qty
    
    # Trova prezzo
    price_per_unit = get_price_for_quantity(item_doc, tipo_vendita, effective_qty)
    
    if price_per_unit == 0:
        return
    
    # Calcola rate
    rate_base = (effective_qty / float(item.qty or 1)) * price_per_unit
    
    # Costo fisso
    fixed_cost = getattr(minimum_config, 'fixed_cost', 0) or 0
    if fixed_cost > 0:
        fixed_cost_mode = getattr(minimum_config, 'fixed_cost_mode', 'Per Riga')
        if fixed_cost_mode == "Per Riga":
            rate_base += fixed_cost
    
    item.rate = round(rate_base, 2)
    setattr(item, f'prezzo_{tipo_vendita.lower().replace(" ", "_")}', price_per_unit)
    
    # Note
    create_pricing_notes(item, tipo_vendita, minimum_config, {
        'original_qty': original_qty,
        'effective_qty': effective_qty,
        'minimum_applied': minimum_applied,
        'price_per_unit': price_per_unit,
        'fixed_cost': fixed_cost if fixed_cost_mode == "Per Riga" else 0,
        'is_global': False
    })

def get_price_for_quantity(item_doc, tipo_vendita, quantity):
    """
    Ottieni prezzo per quantità in base agli scaglioni
    """
    try:
        if not hasattr(item_doc, 'pricing_tiers') or not item_doc.pricing_tiers:
            return 0
        
        # Cerca scaglioni per questo tipo vendita
        relevant_tiers = [
            tier for tier in item_doc.pricing_tiers 
            if getattr(tier, 'selling_type', 'Metro Quadrato') == tipo_vendita
        ]
        
        if not relevant_tiers:
            return 0
        
        # Trova scaglione appropriato
        for tier in relevant_tiers:
            from_qty = getattr(tier, 'from_qty', getattr(tier, 'from_sqm', 0))
            to_qty = getattr(tier, 'to_qty', getattr(tier, 'to_sqm', None))
            
            if quantity >= from_qty:
                if not to_qty or quantity <= to_qty:
                    return getattr(tier, 'price_per_unit', getattr(tier, 'price_per_sqm', 0))
        
        # Cerca default
        for tier in relevant_tiers:
            if getattr(tier, 'is_default', 0):
                return getattr(tier, 'price_per_unit', getattr(tier, 'price_per_sqm', 0))
        
        return 0
        
    except Exception as e:
        print(f"[UNIVERSAL] Errore prezzo: {e}")
        return 0

def create_pricing_notes(item, tipo_vendita, minimum_config, calc_info):
    """
    Crea note dettagliate per il calcolo
    """
    note_parts = []
    
    if calc_info['is_global']:
        note_parts.append("🌍 CALCOLO GLOBALE PREVENTIVO")
    else:
        note_parts.append("📄 CALCOLO PER RIGA")
    
    note_parts.extend([
        f"🎯 Gruppo: {minimum_config.customer_group}",
        f"📊 Tipo: {tipo_vendita}",
        f"📦 Quantità: {item.qty} pz"
    ])
    
    if tipo_vendita == "Metro Quadrato":
        note_parts.extend([
            f"📐 Dimensioni: {item.base}×{item.altezza}cm",
            f"🔢 m² originali: {calc_info['original_qty']:.3f} m²"
        ])
    elif tipo_vendita == "Metro Lineare":
        note_parts.extend([
            f"📏 Lunghezza: {item.lunghezza}cm",
            f"🔢 ml originali: {calc_info['original_qty']:.2f} ml"
        ])
    elif tipo_vendita == "Pezzo":
        note_parts.append(f"🔢 Pezzi: {calc_info['original_qty']:.0f} pz")
    
    if calc_info['minimum_applied']:
        if calc_info['is_global']:
            note_parts.append(f"⚠️ MINIMO GLOBALE: {calc_info['effective_total_qty']:.3f} {item.get('qty_label', 'unità')}")
        else:
            note_parts.append(f"⚠️ MINIMO RIGA: {calc_info['effective_qty']:.3f} {item.get('qty_label', 'unità')}")
    
    note_parts.append(f"💰 Prezzo: €{calc_info['price_per_unit']}/unità")
    
    if calc_info.get('fixed_cost', 0) > 0:
        note_parts.append(f"⚡ Costo fisso: +€{calc_info['fixed_cost']}")
    
    if calc_info['is_global'] and 'proportion' in calc_info:
        note_parts.append(f"📊 Proporzione riga: {calc_info['proportion']:.1%}")
    
    note_parts.append(f"💵 Prezzo unitario: €{item.rate}")
    
    item.note_calcolo = '\n'.join(note_parts)

def apply_global_fixed_costs(doc, customer_group):
    """
    Applica costi fissi globali per preventivo
    """
    # Trova costi fissi "Per Preventivo"
    fixed_costs = frappe.db.sql("""
        SELECT DISTINCT cgm.fixed_cost, cgm.description, cgm.customer_group
        FROM `tabCustomer Group Minimum` cgm
        JOIN `tabItem` i ON cgm.parent = i.name
        JOIN `tab{doctype} Item` qi ON qi.item_code = i.item_code
        WHERE qi.parent = %s 
        AND cgm.customer_group = %s
        AND cgm.fixed_cost > 0
        AND cgm.fixed_cost_mode = 'Per Preventivo'
        AND cgm.enabled = 1
    """.format(doctype=doc.doctype), [doc.name, customer_group], as_dict=True)
    
    total_fixed_cost = sum(cost.fixed_cost for cost in fixed_costs)
    
    if total_fixed_cost > 0:
        print(f"[UNIVERSAL] Costi fissi globali: €{total_fixed_cost}")
        
        # Aggiungi riga separata per costi fissi
        # O distribuisci su tutte le righe
        # Per ora loggiamo solo
        for cost in fixed_costs:
            print(f"[UNIVERSAL] - {cost.description}: €{cost.fixed_cost}")

def apply_standard_pricing(item, tipo_vendita):
    """
    Applica pricing standard senza minimi
    """
    try:
        item_doc = frappe.get_doc("Item", item.item_code)
        
        qty_info = calculate_base_quantities(item, tipo_vendita)
        if not qty_info:
            return
        
        item.update(qty_info)
        
        price_per_unit = get_price_for_quantity(item_doc, tipo_vendita, qty_info['total_qty'])
        
        if price_per_unit > 0:
            rate = qty_info['unit_qty'] * price_per_unit
            item.rate = round(rate, 2)
            
            item.note_calcolo = (
                f"📊 Calcolo standard {tipo_vendita}\n"
                f"💰 Prezzo: €{price_per_unit}/unità\n"
                f"💵 Prezzo unitario: €{rate:.2f}"
            )
        
    except Exception as e:
        print(f"[UNIVERSAL] Errore pricing standard: {e}")