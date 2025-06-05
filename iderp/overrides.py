# iderp/overrides.py
"""
Override classes per ERPNext 15 compatibility
Estende funzionalità core di Item e documenti vendita
"""

import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.stock.doctype.item.item import Item
from erpnext.selling.doctype.quotation.quotation import Quotation

class CustomItem(Item):
    """
    Override della classe Item per supporto misure personalizzate
    """
    
    def validate(self):
        """Validazione estesa per Item con IDERP"""
        super().validate()
        self.validate_iderp_configuration()
        self.validate_pricing_tiers()
        self.validate_customer_group_minimums()
    
    def validate_iderp_configuration(self):
        """Valida configurazione IDERP"""
        if not getattr(self, 'supports_custom_measurement', 0):
            return
            
        # Se supporta misure personalizzate, deve avere tipo vendita default
        if not getattr(self, 'tipo_vendita_default', None):
            frappe.throw(_("Item with custom measurements must have a Default Selling Type"))
            
        # Verifica coerenza configurazione
        if self.tipo_vendita_default == "Metro Lineare":
            if not getattr(self, 'larghezza_materiale_default', 0):
                frappe.msgprint(
                    _("Consider setting a default material width for linear meter sales"),
                    title="Configuration Suggestion",
                    indicator="orange"
                )
    
    def validate_pricing_tiers(self):
        """Valida scaglioni prezzo"""
        if not hasattr(self, 'pricing_tiers') or not self.pricing_tiers:
            return
            
        # Import validation function
        from iderp.doctype.item_pricing_tier.item_pricing_tier import validate_item_pricing_tiers
        validate_item_pricing_tiers(self)
    
    def validate_customer_group_minimums(self):
        """Valida minimi customer group"""
        if not hasattr(self, 'customer_group_minimums') or not self.customer_group_minimums:
            return
            
        # Import validation function  
        from iderp.doctype.customer_group_minimum.customer_group_minimum import validate_item_customer_minimums
        validate_item_customer_minimums(self)
    
    def on_update(self):
        """Dopo aggiornamento Item"""
        super().on_update()
        self.clear_iderp_cache()
    
    def clear_iderp_cache(self):
        """Pulisce cache IDERP per questo item"""
        # Pulisce cache pricing tiers
        from iderp.doctype.item_pricing_tier.item_pricing_tier import clear_all_pricing_tier_cache
        clear_all_pricing_tier_cache()
        
        # Pulisce cache customer minimums
        from iderp.doctype.customer_group_minimum.customer_group_minimum import clear_all_minimum_cache
        clear_all_minimum_cache()
    
    def get_iderp_summary(self):
        """Ottieni riepilogo configurazione IDERP"""
        if not getattr(self, 'supports_custom_measurement', 0):
            return {"configured": False}
            
        summary = {
            "configured": True,
            "tipo_vendita_default": self.tipo_vendita_default,
            "pricing_tiers": len(self.pricing_tiers) if hasattr(self, 'pricing_tiers') else 0,
            "customer_minimums": len(self.customer_group_minimums) if hasattr(self, 'customer_group_minimums') else 0
        }
        
        # Conta scaglioni per tipo
        if hasattr(self, 'pricing_tiers') and self.pricing_tiers:
            tiers_by_type = {}
            for tier in self.pricing_tiers:
                st = tier.selling_type
                tiers_by_type[st] = tiers_by_type.get(st, 0) + 1
            summary["tiers_by_type"] = tiers_by_type
        
        return summary

class CustomQuotation(Quotation):
    """
    Override della classe Quotation per calcoli IDERP
    """
    
    def validate(self):
        """Validazione estesa per Quotation con IDERP"""
        super().validate()
        self.validate_iderp_items()
    
    def validate_iderp_items(self):
        """Valida item con configurazione IDERP"""
        if not hasattr(self, 'items') or not self.items:
            return
            
        for item in self.items:
            self.validate_single_iderp_item(item)
    
    def validate_single_iderp_item(self, item):
        """Valida singolo item IDERP"""
        tipo_vendita = getattr(item, 'tipo_vendita', 'Pezzo')
        
        # Validazioni specifiche per tipo
        if tipo_vendita == "Metro Quadrato":
            base = getattr(item, 'base', 0)
            altezza = getattr(item, 'altezza', 0)
            
            if base and altezza:
                if base <= 0 or altezza <= 0:
                    frappe.throw(_(f"Row {item.idx}: Base and Height must be greater than 0 for Metro Quadrato"))
                    
                # Calcola m² se non calcolati
                if not getattr(item, 'mq_calcolati', 0):
                    mq_singolo = (base * altezza) / 10000
                    item.mq_singolo = round(mq_singolo, 4)
                    item.mq_calcolati = round(mq_singolo * (item.qty or 1), 3)
        
        elif tipo_vendita == "Metro Lineare":
            lunghezza = getattr(item, 'lunghezza', 0)
            
            if lunghezza:
                if lunghezza <= 0:
                    frappe.throw(_(f"Row {item.idx}: Length must be greater than 0 for Metro Lineare"))
                    
                # Calcola ml se non calcolati
                if not getattr(item, 'ml_calcolati', 0):
                    ml_singolo = lunghezza / 100
                    item.ml_calcolati = round(ml_singolo * (item.qty or 1), 2)
        
        elif tipo_vendita == "Pezzo":
            # Aggiorna pezzi totali
            item.pz_totali = item.qty or 1
    
    def before_save(self):
        """Prima del salvataggio"""
        super().before_save()
        
        # Applica calcoli IDERP se configurato
        if self.customer:
            self.apply_iderp_calculations()
    
    def apply_iderp_calculations(self):
        """Applica calcoli IDERP server-side"""
        try:
            # Import funzioni di calcolo
            from iderp.universal_pricing import apply_universal_pricing_server_side
            from iderp.global_minimums import apply_global_minimums_server_side
            
            # Applica pricing universale
            apply_universal_pricing_server_side(self)
            
            # Applica minimi globali
            apply_global_minimums_server_side(self)
            
        except ImportError:
            # Fallback se moduli non disponibili
            frappe.logger().warning("IDERP calculation modules not available, using basic calculations")
            self.apply_basic_iderp_calculations()
    
    def apply_basic_iderp_calculations(self):
        """Calcoli IDERP base di fallback"""
        for item in self.items:
            tipo_vendita = getattr(item, 'tipo_vendita', 'Pezzo')
            
            # Calcoli base senza pricing avanzato
            if tipo_vendita == "Metro Quadrato" and item.base and item.altezza:
                mq_singolo = (item.base * item.altezza) / 10000
                item.mq_singolo = round(mq_singolo, 4)
                item.mq_calcolati = round(mq_singolo * (item.qty or 1), 3)
                
                # Calcolo prezzo base se disponibile
                if getattr(item, 'prezzo_mq', 0):
                    item.rate = round(mq_singolo * item.prezzo_mq, 2)
            
            elif tipo_vendita == "Metro Lineare" and item.lunghezza:
                ml_singolo = item.lunghezza / 100
                item.ml_calcolati = round(ml_singolo * (item.qty or 1), 2)
                
                # Calcolo prezzo base se disponibile
                if getattr(item, 'prezzo_ml', 0):
                    item.rate = round(ml_singolo * item.prezzo_ml, 2)

# Utility functions per override
def get_item_iderp_config(item_code):
    """Ottieni configurazione IDERP per item"""
    try:
        item_doc = frappe.get_doc("Item", item_code)
        if hasattr(item_doc, 'get_iderp_summary'):
            return item_doc.get_iderp_summary()
        return {"configured": False}
    except:
        return {"configured": False}

def validate_iderp_item_compatibility(doc, method=None):
    """Hook di validazione compatibilità IDERP"""
    if hasattr(doc, 'item_code') and doc.item_code:
        config = get_item_iderp_config(doc.item_code)
        
        if config.get("configured"):
            # Item configurato per IDERP, applica validazioni
            tipo_vendita = getattr(doc, 'tipo_vendita', None)
            
            if not tipo_vendita:
                # Imposta tipo default se non specificato
                doc.tipo_vendita = config.get("tipo_vendita_default", "Pezzo")

# Event handlers per cache management
def clear_iderp_cache_on_customer_group_change(doc, method=None):
    """Pulisce cache quando cambia customer group"""
    from iderp.doctype.customer_group_minimum.customer_group_minimum import clear_all_minimum_cache
    clear_all_minimum_cache()

def clear_iderp_cache_on_item_change(doc, method=None):
    """Pulisce cache quando cambia item"""
    if hasattr(doc, 'clear_iderp_cache'):
        doc.clear_iderp_cache()