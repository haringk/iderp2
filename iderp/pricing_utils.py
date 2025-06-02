# iderp/pricing_utils.py
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
            from iderp.customer_group_pricing import get_customer_specific_price_for_sqm
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