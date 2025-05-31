import frappe

def copy_custom_fields(doc, method=None):
    """
    Copia i campi custom tra documenti e ricalcola i prezzi automaticamente
    """
    # Lista completa dei campi da copiare
    fields_to_copy = [
        "tipo_vendita",
        "base", "altezza", "mq_calcolati", "prezzo_mq",
        "larghezza_materiale", "lunghezza", "ml_calcolati", "prezzo_ml",
        "note_calcolo"
    ]
    
    if not hasattr(doc, "items"):
        return
    
    for item in doc.items:
        # Copia campi dal documento precedente se collegato
        if hasattr(item, "linked_document_type") and hasattr(item, "linked_document_name"):
            try:
                prev_doc = frappe.get_doc(item.linked_document_type, item.linked_document_name)
                for field in fields_to_copy:
                    if hasattr(prev_doc, field) and hasattr(item, field):
                        setattr(item, field, getattr(prev_doc, field, None))
            except Exception as e:
                print(f"[iderp] Errore copia campi: {e}")
                continue
        
        # Ricalcola automaticamente i prezzi
        recalculate_item_price(item)

def recalculate_item_price(item):
    """
    Ricalcola il prezzo dell'item in base al tipo di vendita
    """
    try:
        tipo_vendita = getattr(item, "tipo_vendita", "Pezzo")
        
        if tipo_vendita == "Metro Quadrato":
            calculate_square_meter_price(item)
        elif tipo_vendita == "Metro Lineare":
            calculate_linear_meter_price(item)
        elif tipo_vendita == "Pezzo":
            calculate_piece_price(item)
            
    except Exception as e:
        print(f"[iderp] Errore ricalcolo prezzo: {e}")

def calculate_square_meter_price(item):
    """Calcola prezzo per vendita al metro quadrato"""
    base = getattr(item, "base", 0)
    altezza = getattr(item, "altezza", 0)
    prezzo_mq = getattr(item, "prezzo_mq", 0)
    
    if base and altezza:
        # Calcola m² (da cm a m²)
        mq_calcolati = (float(base) * float(altezza)) / 10000
        setattr(item, "mq_calcolati", mq_calcolati)
        
        if prezzo_mq and prezzo_mq > 0:
            nuovo_rate = mq_calcolati * float(prezzo_mq)
            setattr(item, "rate", nuovo_rate)
            setattr(item, "note_calcolo", 
                   f"{mq_calcolati:.3f} m² × €{prezzo_mq} = €{nuovo_rate:.2f}")
        else:
            setattr(item, "note_calcolo", 
                   f"{mq_calcolati:.3f} m² (manca prezzo al m²)")
    else:
        setattr(item, "mq_calcolati", 0)
        setattr(item, "note_calcolo", "Inserire base e altezza")

def calculate_linear_meter_price(item):
    """Calcola prezzo per vendita al metro lineare"""
    lunghezza = getattr(item, "lunghezza", 0)
    prezzo_ml = getattr(item, "prezzo_ml", 0)
    larghezza_materiale = getattr(item, "larghezza_materiale", 0)
    
    if lunghezza:
        # Calcola metri lineari (da cm a m)
        ml_calcolati = float(lunghezza) / 100
        setattr(item, "ml_calcolati", ml_calcolati)
        
        if prezzo_ml and prezzo_ml > 0:
            nuovo_rate = ml_calcolati * float(prezzo_ml)
            setattr(item, "rate", nuovo_rate)
            
            note = f"{ml_calcolati:.2f} ml × €{prezzo_ml}"
            if larghezza_materiale:
                note += f" (largh. {larghezza_materiale}cm)"
            note += f" = €{nuovo_rate:.2f}"
            setattr(item, "note_calcolo", note)
        else:
            setattr(item, "note_calcolo", 
                   f"{ml_calcolati:.2f} ml (manca prezzo al ml)")
    else:
        setattr(item, "ml_calcolati", 0)
        setattr(item, "note_calcolo", "Inserire lunghezza")

def calculate_piece_price(item):
    """Gestisce vendita al pezzo"""
    rate = getattr(item, "rate", 0)
    qty = getattr(item, "qty", 1)
    
    if rate and qty:
        totale = float(rate) * float(qty)
        setattr(item, "note_calcolo", 
               f"{qty} pz × €{rate} = €{totale:.2f}")
    else:
        setattr(item, "note_calcolo", 
               "Vendita al pezzo - inserire prezzo unitario")

# Funzioni di utilità per uso esterno
def get_square_meters(base_cm, altezza_cm):
    """Calcola metri quadrati da misure in cm"""
    return (float(base_cm) * float(altezza_cm)) / 10000

def get_linear_meters(lunghezza_cm):
    """Calcola metri lineari da misure in cm"""
    return float(lunghezza_cm) / 100

def validate_measurements(item):
    """Valida che le misure siano corrette per il tipo di vendita"""
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