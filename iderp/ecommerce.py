# iderp/ecommerce.py
import frappe
from frappe import _
import json

@frappe.whitelist(allow_guest=True)
def calculate_item_price(item_code, tipo_vendita, **kwargs):
    """
    API per calcolare il prezzo dinamicamente dall'e-commerce
    """
    try:
        # Verifica che l'item esista
        if not frappe.db.exists("Item", item_code):
            return {"error": "Prodotto non trovato"}
        
        item = frappe.get_doc("Item", item_code)
        
        # Ottieni il prezzo base dal Price List
        price_list = frappe.db.get_single_value("E Commerce Settings", "price_list") or "Standard Selling"
        base_price = get_item_price(item_code, price_list)
        
        if not base_price:
            return {"error": "Prezzo non configurato"}
        
        result = {
            "item_code": item_code,
            "tipo_vendita": tipo_vendita,
            "base_price": base_price,
            "calculated_price": base_price,
            "quantity_calculated": 1,
            "note_calcolo": "",
            "currency": frappe.db.get_single_value("E Commerce Settings", "currency") or "EUR"
        }
        
        if tipo_vendita == "Metro Quadrato":
            result = calculate_square_meter_ecommerce(result, kwargs)
        elif tipo_vendita == "Metro Lineare":
            result = calculate_linear_meter_ecommerce(result, kwargs)
        else:
            result["note_calcolo"] = "Vendita al pezzo"
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Errore calcolo prezzo e-commerce: {str(e)}")
        return {"error": "Errore nel calcolo del prezzo"}

def calculate_square_meter_ecommerce(result, kwargs):
    """Calcola prezzo per metri quadrati nell'e-commerce"""
    base = float(kwargs.get("base", 0))
    altezza = float(kwargs.get("altezza", 0))
    
    if base and altezza:
        # Calcola metri quadrati
        mq_calcolati = (base * altezza) / 10000
        result["quantity_calculated"] = mq_calcolati
        result["calculated_price"] = result["base_price"] * mq_calcolati
        result["note_calcolo"] = f"Base: {base}cm × Altezza: {altezza}cm = {mq_calcolati:.3f} m²"
        result["measurements"] = {
            "base": base,
            "altezza": altezza,
            "mq_calcolati": mq_calcolati
        }
    else:
        result["error"] = "Inserire base e altezza"
    
    return result

def calculate_linear_meter_ecommerce(result, kwargs):
    """Calcola prezzo per metri lineari nell'e-commerce"""
    lunghezza = float(kwargs.get("lunghezza", 0))
    larghezza_materiale = float(kwargs.get("larghezza_materiale", 0))
    
    if lunghezza:
        # Calcola metri lineari
        ml_calcolati = lunghezza / 100
        result["quantity_calculated"] = ml_calcolati
        result["calculated_price"] = result["base_price"] * ml_calcolati
        
        note = f"Lunghezza: {lunghezza}cm = {ml_calcolati:.2f} ml"
        if larghezza_materiale:
            note += f" (Larghezza materiale: {larghezza_materiale}cm)"
        
        result["note_calcolo"] = note
        result["measurements"] = {
            "lunghezza": lunghezza,
            "larghezza_materiale": larghezza_materiale,
            "ml_calcolati": ml_calcolati
        }
    else:
        result["error"] = "Inserire lunghezza"
    
    return result

def get_item_price(item_code, price_list):
    """Ottieni prezzo item da Price List"""
    price = frappe.db.sql("""
        SELECT price_list_rate 
        FROM `tabItem Price` 
        WHERE item_code = %s AND price_list = %s
        ORDER BY valid_from DESC 
        LIMIT 1
    """, (item_code, price_list))
    
    return price[0][0] if price else None

@frappe.whitelist(allow_guest=True)
def add_to_cart_calculated(item_code, tipo_vendita, measurements=None, qty=1):
    """
    Aggiunge item al carrello con calcoli personalizzati
    """
    try:
        # Calcola il prezzo con le misure
        calc_result = calculate_item_price(
            item_code=item_code,
            tipo_vendita=tipo_vendita,
            **(measurements or {})
        )
        
        if calc_result.get("error"):
            return {"error": calc_result["error"]}
        
        # Usa la funzione standard di ERPNext per aggiungere al carrello
        from erpnext.e_commerce.shopping_cart.cart import add_to_cart
        
        cart_result = add_to_cart(
            item_code=item_code,
            qty=calc_result["quantity_calculated"],
            rate=calc_result["base_price"]
        )
        
        # Aggiungi informazioni personalizzate
        cart_result.update({
            "tipo_vendita": tipo_vendita,
            "measurements": calc_result.get("measurements"),
            "note_calcolo": calc_result["note_calcolo"],
            "calculated_price": calc_result["calculated_price"]
        })
        
        return cart_result
        
    except Exception as e:
        frappe.log_error(f"Errore aggiunta carrello calcolato: {str(e)}")
        return {"error": "Errore nell'aggiunta al carrello"}

@frappe.whitelist()
def get_item_selling_config(item_code):
    """
    Ottieni configurazione vendita per un item (per configurare l'interfaccia)
    """
    try:
        # Verifica se l'item ha configurazioni personalizzate
        custom_config = frappe.db.sql("""
            SELECT 
                tipo_vendita_default,
                larghezza_materiale_default,
                base_min, base_max,
                altezza_min, altezza_max,
                lunghezza_min, lunghezza_max
            FROM `tabItem` 
            WHERE item_code = %s
        """, item_code, as_dict=True)
        
        if custom_config:
            return custom_config[0]
        else:
            return {
                "tipo_vendita_default": "Pezzo",
                "larghezza_materiale_default": None,
                "base_min": 1, "base_max": 1000,
                "altezza_min": 1, "altezza_max": 1000,
                "lunghezza_min": 1, "lunghezza_max": 1000
            }
            
    except Exception as e:
        frappe.log_error(f"Errore config item: {str(e)}")
        return {"error": "Errore nel caricamento configurazione"}

# Hook per estendere Website Item
def extend_website_item_context(context, item):
    """
    Aggiunge dati personalizzati al contesto della pagina prodotto
    """
    context["selling_config"] = get_item_selling_config(item.item_code)
    context["supports_custom_measurement"] = True
    
# Hook per validare il carrello
def validate_cart_item(doc, method):
    """
    Valida gli item del carrello con misure personalizzate
    """
    if hasattr(doc, 'tipo_vendita') and doc.tipo_vendita in ["Metro Quadrato", "Metro Lineare"]:
        # Ricalcola il prezzo server-side per sicurezza
        from iderp.copy_fields import recalculate_item_price
        recalculate_item_price(doc)